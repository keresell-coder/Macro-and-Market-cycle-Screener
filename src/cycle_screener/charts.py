from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Any

import pandas as pd

from .indicators import IndicatorDefinition, indicator_by_slug, public_indicator_slug
from .taxonomy import SUBSECTORS, Subsector


CHART_LAYER_VERSION = "sprint10-credit-liquidity-chart-layer"
CHART_MIN_YEARS = 10
CHART_MAX_YEARS = 30
CHART_MAX_MONTHS = CHART_MAX_YEARS * 12 + 1

CHART_VIEW_DEFINITIONS: tuple[dict[str, Any], ...] = (
    {
        "view_id": "global",
        "title": "Global macro and market proxy history",
        "scope": "global",
        "description": "Top-level historical view using monthly OECD CLI mirror data, annual World Bank growth background, commodity pressure, rates, FX, and broad public market-chart proxies.",
        "indicator_slugs": (
            "g20_cli",
            "g7_cli",
            "global_pmi",
            "chicago_fed_nfci",
            "st_louis_financial_stress",
            "brent",
            "us_natural_gas",
            "copper",
            "rates_pressure",
            "nasdaq_proxy",
            "oil_curve_pressure",
        ),
    },
    {
        "view_id": "united_states",
        "title": "United States proxy history",
        "scope": "United States",
        "description": "US-linked leading, rates, market, oil, gas, and product-fuel proxies that are already available in the live public dataset.",
        "indicator_slugs": ("us_cli", "chicago_fed_nfci", "st_louis_financial_stress", "rates_pressure", "nasdaq_proxy", "wti", "us_natural_gas", "us_distillate_stocks"),
    },
    {
        "view_id": "liquidity_credit",
        "title": "Liquidity and credit proxy history",
        "scope": "Liquidity/credit",
        "description": "Narrow first Sprint 10 credit/liquidity layer using public FRED CSV financial-conditions and financial-stress proxies before broader BIS or credit-spread connectors are added.",
        "indicator_slugs": ("chicago_fed_nfci", "st_louis_financial_stress", "rates_pressure", "g20_cli", "nasdaq_proxy"),
    },
    {
        "view_id": "europe",
        "title": "Europe proxy history",
        "scope": "Europe",
        "description": "Europe-linked CLI, EUR/NOK, rates, energy, and industrial commodity proxies. This is not yet a full euro-area credit or monetary-data layer.",
        "indicator_slugs": ("europe_cli", "eur_nok", "rates_pressure", "brent", "copper"),
    },
    {
        "view_id": "china",
        "title": "China proxy history",
        "scope": "China",
        "description": "China OECD CLI mirror data, annual World Bank growth background, and industrial commodity proxies relevant to dry bulk and materials.",
        "indicator_slugs": ("china_cli", "china_growth_proxy", "copper", "aluminum", "g20_cli"),
    },
    {
        "view_id": "norway_oslo",
        "title": "Norway and Oslo-linked proxy history",
        "scope": "Norway/Oslo-linked",
        "description": "Norges Bank policy and FX series, Statistics Norway CPI, and global proxies that matter for Oslo-linked subsectors.",
        "indicator_slugs": ("norges_bank_policy_rate", "norway_cpi", "usd_nok", "eur_nok", "g20_cli", "brent"),
    },
)

MARKET_CHART_COLUMNS = {
    "price_index": "Subsector price proxy",
    "benchmark_index": "Oslo benchmark proxy",
    "relative_price_index": "Relative subsector price proxy",
    "valuation_proxy": "Valuation proxy",
}


def build_chart_layer(
    observations: pd.DataFrame,
    market_cycle: pd.DataFrame,
    source_freshness: list[dict[str, Any]],
) -> dict[str, Any]:
    freshness_lookup = {str(item.get("indicator_slug", "")): item for item in source_freshness}
    indicator_lookup = indicator_by_slug()
    scoring_lookup = _scoring_lookup()

    views = [
        _indicator_chart_view(definition, observations, freshness_lookup, indicator_lookup, scoring_lookup)
        for definition in CHART_VIEW_DEFINITIONS
    ]
    sector_views = _sector_views(market_cycle, observations, freshness_lookup, indicator_lookup, scoring_lookup)
    series_count = sum(len(view.get("series", [])) for view in views)
    series_count += sum(
        len(subsector.get("proxy_view", {}).get("series", []))
        + len(subsector.get("market_view", {}).get("series", []))
        + len(subsector.get("driver_view", {}).get("series", []))
        for sector in sector_views
        for subsector in sector.get("subsectors", [])
    )

    return {
        "version": CHART_LAYER_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "summary": "Historical chart layer built from existing live public indicators and explicitly sample-backed subsector market-cycle histories.",
        "normalization": "Most chart lines are indexed to 100 at the first available observation inside each chart window. Near-zero or sign-changing series are range-normalized around 100 to avoid distorted chart scales. Chart x-axes target a common overlapping history, are capped at 30 years, and are not compressed below 10 years; series with shorter available history are flagged in metadata.",
        "chart_window_policy": {
            "minimum_years": CHART_MIN_YEARS,
            "maximum_years": CHART_MAX_YEARS,
            "alignment": "Use the shortest available series range in the view, clamped to a 10-30 year display window. End the window at the latest date common to the included series so the data aligns with the x-axis.",
        },
        "global_view_id": "global",
        "series_count": series_count,
        "views": views,
        "sector_views": sector_views,
        "coverage_notes": _coverage_notes(),
    }


def _indicator_chart_view(
    definition: dict[str, Any],
    observations: pd.DataFrame,
    freshness_lookup: dict[str, dict[str, Any]],
    indicator_lookup: dict[str, IndicatorDefinition],
    scoring_lookup: dict[str, list[str]],
) -> dict[str, Any]:
    series = []
    missing = []
    for slug in definition["indicator_slugs"]:
        record = _indicator_series(slug, observations, freshness_lookup, indicator_lookup, scoring_lookup)
        if record["points"]:
            series.append(record)
        else:
            missing.append(
                {
                    "series_id": public_indicator_slug(slug),
                    "label": indicator_lookup[slug].name if slug in indicator_lookup else slug,
                    "status": "missing",
                    "message": "No observations are available in this snapshot.",
                }
            )
    chart_window = _apply_common_chart_window(series)
    return {
        "view_id": str(definition["view_id"]),
        "title": str(definition["title"]),
        "scope": str(definition["scope"]),
        "description": str(definition["description"]),
        "value_basis": "indexed_to_100",
        "series": series,
        "missing_series": missing,
        "chart_window": chart_window,
    }


def _indicator_series(
    slug: str,
    observations: pd.DataFrame,
    freshness_lookup: dict[str, dict[str, Any]],
    indicator_lookup: dict[str, IndicatorDefinition],
    scoring_lookup: dict[str, list[str]],
) -> dict[str, Any]:
    indicator = indicator_lookup.get(slug)
    frame = _series_frame(observations, "indicator_slug", slug)
    points = _indexed_points(frame)
    freshness = freshness_lookup.get(slug, {})
    source = str(freshness.get("source") or (indicator.source if indicator else "unknown"))
    source_category = str(freshness.get("source_category") or "missing")
    scoring_subsectors = scoring_lookup.get(slug, [])
    latest_point = points[-1] if points else {}
    first_point = points[0] if points else {}

    return {
        "series_id": public_indicator_slug(slug),
        "legacy_slug": slug if public_indicator_slug(slug) != slug else "",
        "label": indicator.name if indicator else slug,
        "description": indicator.description if indicator else "",
        "unit": indicator.unit if indicator else str(frame["unit"].iloc[-1]) if not frame.empty and "unit" in frame else "",
        "frequency": _indicator_frequency(indicator),
        "source_slug": source,
        "source": _source_label(source, indicator.source if indicator else ""),
        "configured_source": indicator.source if indicator else "",
        "latest_observed_at": str(freshness.get("latest_observed_at") or latest_point.get("date", "")),
        "freshness_status": str(freshness.get("freshness_status") or "missing"),
        "data_class": source_category,
        "proxy_status": _indicator_proxy_status(indicator, source_category),
        "scoring_inclusion": bool(scoring_subsectors),
        "scoring_note": _scoring_note(scoring_subsectors),
        "latest_value": latest_point.get("value"),
        "latest_indexed_value": latest_point.get("indexed_value"),
        "first_observed_at": str(first_point.get("date", "")),
        "available_years": _available_years(points),
        "points": points,
    }


def _sector_views(
    market_cycle: pd.DataFrame,
    observations: pd.DataFrame,
    freshness_lookup: dict[str, dict[str, Any]],
    indicator_lookup: dict[str, IndicatorDefinition],
    scoring_lookup: dict[str, list[str]],
) -> list[dict[str, Any]]:
    sectors: dict[str, list[Subsector]] = {}
    for subsector in SUBSECTORS:
        sectors.setdefault(subsector.group, []).append(subsector)

    records = []
    for group_name, subsectors in sectors.items():
        records.append(
            {
                "group_name": group_name,
                "description": "Subsector drilldown uses current scoring proxy histories plus deterministic sample-backed market-cycle histories until reviewed public or licensed market data is connected.",
                "subsectors": [
                    _subsector_chart_record(
                        subsector,
                        market_cycle,
                        observations,
                        freshness_lookup,
                        indicator_lookup,
                        scoring_lookup,
                    )
                    for subsector in subsectors
                ],
            }
        )
    return records


def _subsector_chart_record(
    subsector: Subsector,
    market_cycle: pd.DataFrame,
    observations: pd.DataFrame,
    freshness_lookup: dict[str, dict[str, Any]],
    indicator_lookup: dict[str, IndicatorDefinition],
    scoring_lookup: dict[str, list[str]],
) -> dict[str, Any]:
    proxy_view = _indicator_chart_view(
        {
            "view_id": f"{subsector.slug}_scoring_proxies",
            "title": f"{subsector.name}: scoring proxy histories",
            "scope": subsector.name,
            "description": f"Live public indicators currently used in the {subsector.name} opportunity score where data exists.",
            "indicator_slugs": subsector.proxy_indicators,
        },
        observations,
        freshness_lookup,
        indicator_lookup,
        scoring_lookup,
    )
    market_view = _market_cycle_view(subsector, market_cycle, tuple(MARKET_CHART_COLUMNS))
    driver_view = _market_cycle_view(subsector, market_cycle, ("driver_pressure",), raw=True)
    return {
        "subsector_slug": subsector.slug,
        "subsector_name": subsector.name,
        "group_name": subsector.group,
        "data_boundary": "Subsector market-cycle histories are deterministic sample-backed proxies. They are not true Oslo subsector price histories or valuation multiples.",
        "proxy_view": proxy_view,
        "market_view": market_view,
        "driver_view": driver_view,
    }


def _market_cycle_view(subsector: Subsector, market_cycle: pd.DataFrame, columns: tuple[str, ...], raw: bool = False) -> dict[str, Any]:
    series = []
    for column in columns:
        frame = _market_frame(market_cycle, subsector.slug, column)
        points = _raw_points(frame) if raw else _indexed_points(frame)
        latest = points[-1] if points else {}
        first = points[0] if points else {}
        series.append(
            {
                "series_id": column,
                "legacy_slug": "",
                "label": MARKET_CHART_COLUMNS.get(column, "Driver pressure proxy"),
                "description": _market_description(column),
                "unit": "standardized signal" if raw else "index",
                "frequency": "monthly",
                "source_slug": "sample_market_proxy",
                "source": "Deterministic sample market-cycle proxy",
                "configured_source": "sample_market_proxy",
                "latest_observed_at": str(latest.get("date", "")),
                "freshness_status": "current" if points else "missing",
                "data_class": "sample_backed_proxy",
                "proxy_status": "sample_backed",
                "scoring_inclusion": False,
                "scoring_note": "Not included in the opportunity score. Used as visible subsector context and contradiction evidence only.",
                "latest_value": latest.get("value"),
                "latest_indexed_value": latest.get("indexed_value") if not raw else None,
                "first_observed_at": str(first.get("date", "")),
                "available_years": _available_years(points),
                "points": points,
            }
        )
    chart_window = _apply_common_chart_window(series)
    return {
        "view_id": f"{subsector.slug}_{'driver_pressure' if raw else 'market_cycle'}",
        "title": f"{subsector.name}: {'driver pressure proxy' if raw else 'sample-backed market-cycle proxy history'}",
        "scope": subsector.name,
        "description": "Sample-backed subsector proxy history. True price histories and valuation multiples remain missing until reviewed public or licensed market data is connected.",
        "value_basis": "raw_standardized" if raw else "indexed_to_100",
        "series": [item for item in series if item["points"]],
        "missing_series": [item for item in series if not item["points"]],
        "chart_window": chart_window,
    }


def _series_frame(frame: pd.DataFrame, column: str, value: str) -> pd.DataFrame:
    if frame.empty or column not in frame or "observed_at" not in frame or "value" not in frame:
        return pd.DataFrame()
    result = frame[frame[column].astype(str) == value].copy()
    result["observed_at_sort"] = pd.to_datetime(result["observed_at"], errors="coerce")
    result["value"] = pd.to_numeric(result["value"], errors="coerce")
    return result.dropna(subset=["observed_at_sort", "value"]).sort_values("observed_at_sort").tail(CHART_MAX_MONTHS)


def _market_frame(market_cycle: pd.DataFrame, subsector_slug: str, value_column: str) -> pd.DataFrame:
    if market_cycle.empty or "subsector_slug" not in market_cycle or value_column not in market_cycle:
        return pd.DataFrame()
    frame = market_cycle[market_cycle["subsector_slug"].astype(str) == subsector_slug][["observed_at", value_column]].copy()
    frame = frame.rename(columns={value_column: "value"})
    frame["observed_at_sort"] = pd.to_datetime(frame["observed_at"], errors="coerce")
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    return frame.dropna(subset=["observed_at_sort", "value"]).sort_values("observed_at_sort").tail(CHART_MAX_MONTHS)


def _apply_common_chart_window(series: list[dict[str, Any]]) -> dict[str, Any]:
    spans = []
    for item in series:
        dates = [_parse_point_date(point) for point in item.get("points", [])]
        dates = [date for date in dates if date is not None]
        if not dates:
            continue
        start = min(dates)
        end = max(dates)
        available_years = _year_span(start, end)
        item["available_years"] = round(available_years, 2)
        spans.append(
            {
                "series_id": str(item.get("series_id", "")),
                "label": str(item.get("label", "")),
                "start": start,
                "end": end,
                "available_years": available_years,
            }
        )

    if not spans:
        return {
            "start": "",
            "end": "",
            "year_span": 0,
            "minimum_years": CHART_MIN_YEARS,
            "maximum_years": CHART_MAX_YEARS,
            "minimum_years_satisfied": False,
            "short_history_series": [],
        }

    shortest_available_years = min(span["available_years"] for span in spans)
    target_months = min(max(math.ceil(shortest_available_years * 12), CHART_MIN_YEARS * 12), CHART_MAX_YEARS * 12)
    window_end = min(span["end"] for span in spans)
    window_start = window_end - pd.DateOffset(months=target_months)

    for item in series:
        item["points"] = [
            point
            for point in item.get("points", [])
            if (parsed := _parse_point_date(point)) is not None and window_start <= parsed <= window_end
        ]

    short_history = [
        {
            "series_id": span["series_id"],
            "label": span["label"],
            "available_years": round(span["available_years"], 2),
        }
        for span in spans
        if span["available_years"] < CHART_MIN_YEARS
    ]
    year_span = _year_span(window_start, window_end)
    return {
        "start": window_start.date().isoformat(),
        "end": window_end.date().isoformat(),
        "year_span": round(year_span, 2),
        "minimum_years": CHART_MIN_YEARS,
        "maximum_years": CHART_MAX_YEARS,
        "minimum_years_satisfied": year_span >= CHART_MIN_YEARS,
        "shortest_available_years": round(shortest_available_years, 2),
        "short_history_series": short_history,
    }


def _available_years(points: list[dict[str, Any]]) -> float:
    dates = [_parse_point_date(point) for point in points]
    dates = [date for date in dates if date is not None]
    if not dates:
        return 0.0
    return round(_year_span(min(dates), max(dates)), 2)


def _year_span(start: pd.Timestamp, end: pd.Timestamp) -> float:
    return max(0.0, (end - start).days / 365.25)


def _parse_point_date(point: dict[str, Any]) -> pd.Timestamp | None:
    value = pd.to_datetime(point.get("date"), errors="coerce")
    if pd.isna(value):
        return None
    return pd.Timestamp(value)


def _indexed_points(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    values = [float(value) for value in frame["value"].tolist()]
    first = values[0]
    min_value = min(values)
    max_value = max(values)
    positive_level_series = first > 1 and min_value > 0 and (max_value / max(min_value, 1e-9)) <= 4
    value_range = max(values) - min(values)
    denominator = first if positive_level_series else value_range if abs(value_range) > 1e-9 else 1.0
    return [
        {
            "date": row["observed_at_sort"].date().isoformat(),
            "value": round(float(row["value"]), 4),
            "indexed_value": round(float(row["value"]) / denominator * 100, 3)
            if positive_level_series
            else round(100 + ((float(row["value"]) - first) / denominator * 80), 3),
            "chart_value": round(float(row["value"]) / denominator * 100, 3)
            if positive_level_series
            else round(100 + ((float(row["value"]) - first) / denominator * 80), 3),
        }
        for _, row in frame.iterrows()
    ]


def _raw_points(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    return [
        {
            "date": row["observed_at_sort"].date().isoformat(),
            "value": round(float(row["value"]), 4),
            "chart_value": round(float(row["value"]), 4),
        }
        for _, row in frame.iterrows()
    ]


def _scoring_lookup() -> dict[str, list[str]]:
    lookup: dict[str, list[str]] = {}
    for subsector in SUBSECTORS:
        for slug in subsector.proxy_indicators:
            lookup.setdefault(slug, []).append(subsector.name)
    return lookup


def _scoring_note(subsector_names: list[str]) -> str:
    if not subsector_names:
        return "Not included in current opportunity scoring."
    if len(subsector_names) <= 3:
        return f"Included in current scoring for {', '.join(subsector_names)}."
    return f"Included in current scoring for {len(subsector_names)} subsectors."


def _indicator_frequency(indicator: IndicatorDefinition | None) -> str:
    if indicator and indicator.source == "world_bank_indicator":
        return "annual"
    if indicator:
        return "monthly"
    return "unknown"


def _indicator_proxy_status(indicator: IndicatorDefinition | None, source_category: str) -> str:
    if source_category == "numeric_sample_fallback":
        return "sample_fallback"
    if source_category == "deterministic_sample":
        return "sample_build"
    if not indicator:
        return "missing"
    if indicator.source == "dbnomics_oecd_cli":
        return "live_public_mirror_proxy"
    if indicator.source == "world_bank_indicator":
        return "annual_background_proxy"
    if indicator.source == "yahoo_chart":
        return "public_market_chart_proxy"
    if indicator.source == "fred_public":
        return "live_public_financial_conditions_proxy"
    if indicator.source == "derived_public":
        return "derived_public_proxy"
    return "live_public_proxy"


def _source_label(source_slug: str, configured_source: str) -> str:
    labels = {
        "world_bank_commodity": "World Bank Pink Sheet",
        "world_bank_indicator": "World Bank Indicators API",
        "dbnomics_oecd_cli": "DB.nomics mirror of OECD CLI",
        "norges_bank": "Norges Bank CSV API",
        "norges_bank_csv": "Norges Bank CSV API",
        "ssb": "Statistics Norway API",
        "ssb_cpi": "Statistics Norway API",
        "yahoo_chart": "Public market chart data",
        "fred_public": "FRED public CSV",
        "derived_public": "Derived from public source series",
        "sample": "Deterministic sample data",
        "sample_fallback": "Deterministic sample fallback",
    }
    return labels.get(source_slug) or labels.get(configured_source) or source_slug.replace("_", " ").title()


def _market_description(column: str) -> str:
    descriptions = {
        "price_index": "Synthetic subsector price proxy for development and visual context.",
        "benchmark_index": "Synthetic Oslo benchmark proxy for development and visual context.",
        "relative_price_index": "Synthetic relative subsector price proxy versus the benchmark proxy.",
        "valuation_proxy": "Valuation proxy only; not a true market valuation multiple.",
        "driver_pressure": "Synthetic driver-pressure signal on a standardized scale.",
    }
    return descriptions.get(column, column.replace("_", " "))


def _coverage_notes() -> list[dict[str, str]]:
    return [
        {
            "dimension": "Global historical charts",
            "status": "available",
            "note": "Built from existing live public numeric indicators and clearly labeled proxy series.",
        },
        {
            "dimension": "Regional drilldown",
            "status": "partial",
            "note": "Global, United States, Europe, China, and Norway/Oslo-linked views are available where current live series exist.",
        },
        {
            "dimension": "Subsector price and valuation history",
            "status": "sample_backed",
            "note": "Uses deterministic proxy histories until reviewed public or licensed subsector market data is connected.",
        },
        {
            "dimension": "Liquidity and credit charts",
            "status": "partial",
            "note": "Sprint 10 adds Chicago Fed NFCI and St. Louis Fed Financial Stress Index from public FRED CSV to the global, US, and dedicated liquidity/credit chart views.",
        },
        {
            "dimension": "True valuation multiples",
            "status": "missing",
            "note": "No true Oslo subsector valuation multiples are displayed or scored yet.",
        },
        {
            "dimension": "Direct PMI and restricted market data",
            "status": "missing",
            "note": "The report does not imply true PMI, paid market data, or restricted datasets where only proxies are available.",
        },
    ]
