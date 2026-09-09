from __future__ import annotations

from datetime import date, datetime, timezone
import json
from pathlib import Path
from typing import Any

import pandas as pd

from .charts import build_chart_layer
from .config import EXPORT_DIR, get_settings
from .cycle_state import build_cycle_state, classify_subsector_phase
from .indicators import indicator_by_slug, public_indicator_slug
from .outlooks import outlook_summary
from .publication import is_public_export_path
from .signal_metrics import build_indicator_metrics
from .scoring import calculate_scores
from .source_health import observation_health, numeric_health, freshness_status, public_health
from .sources import SOURCE_DEFINITIONS
from .storage import RadarStore
from .taxonomy import subsector_by_slug


SIGNAL_COLUMNS = (
    "cycle_pressure",
    "recovery_potential",
    "reversal_watch",
    "valuation_proxy",
    "cycle_position_score",
    "momentum",
    "macro_tailwind",
    "narrative_divergence",
    "confidence",
    "data_support",
)

MARKET_COLUMNS = (
    "price_index",
    "benchmark_index",
    "relative_price_index",
    "valuation_proxy",
    "driver_pressure",
)

REPORT_STATE_VERSION = "2026-09-09-source-health-v4"
SCORING_METHODOLOGY_VERSION = "research-priority-v4-observation-health-gated"
CREDIT_LIQUIDITY_INDICATORS = ("chicago_fed_nfci", "st_louis_financial_stress", "us_high_yield_spread", "us_investment_grade_spread", "broad_us_dollar")
MACRO_CONFIRMATION_INDICATORS = ("g20_cli", "us_cli", "europe_cli", "global_equity_proxy", "em_equity_proxy")
VALUATION_INTERNALS_INDICATORS = ("us_equity_market_cap_gdp_proxy", "vix_proxy", "sp500_equal_weight_leadership_proxy")


def build_report_state(store: RadarStore | None = None) -> dict[str, Any]:
    owns_store = store is None
    if store is None:
        store = RadarStore(get_settings().database_path)

    scores = store.table("subsector_scores")
    observations = store.table("observations")
    source_status = store.table("source_status")
    research_facts = store.table("research_facts")
    market_cycle = store.table("subsector_market_cycle")
    institutional_outlooks = store.table("institutional_outlooks")

    if owns_store:
        store.close()

    source_status_records = _latest_source_status(source_status)
    sample = any(item.get("source_slug") == "sample" for item in source_status_records)
    # Re-evaluate dates at publication time, including databases refreshed earlier.
    scores = calculate_scores(observations, sample=sample)
    ranked_scores = scores.sort_values("opportunity_score", ascending=False).reset_index(drop=True)
    subsectors = [_subsector_record(rank, row, market_cycle, research_facts) for rank, (_, row) in enumerate(ranked_scores.iterrows(), start=1)]

    source_status_records = _latest_source_status(source_status)
    source_freshness = _source_freshness(observations, source_status_records)
    chart_layer = build_chart_layer(observations, market_cycle, source_freshness)

    contradicting_evidence = _contradicting_evidence_summary(subsectors)
    signal_groups = _signal_groups(observations, source_freshness)
    framework_coverage = _framework_coverage()
    cycle_state = build_cycle_state(
        observations=observations,
        source_freshness=source_freshness,
        signal_groups=signal_groups,
        subsectors=subsectors,
        contradicting_evidence=contradicting_evidence,
        framework_coverage=framework_coverage,
    )

    return {
        "schema_version": REPORT_STATE_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "data_as_of": _data_as_of(observations, market_cycle),
        "methodology": {
            "scoring_version": SCORING_METHODOLOGY_VERSION,
            "report_state_version": REPORT_STATE_VERSION,
            "framework_reference": "docs/knowledge_base/global_macro_market_cycle_knowledge_base.md",
            "framework_coverage": "Global evidence-gated framework spanning OECD leading indicators, inflation, major central-bank policy rates, nominal and real yields, financial conditions, credit spreads, dollar liquidity, commodities, geopolitical risk and regional equity markets. Annual GDP is slow background only. Correlated country series collapse to economic-family signals, transformations are explicit, and stale observations are excluded from scores.",
            "implementation_boundary": "Research-priority scores are triage signals, not expected returns. Cycle-state labels are rule-based synthesis outputs from public/proxied evidence, not forecasts, timing signals, or investment advice. Missing dimensions are explicit blind spots rather than neutral evidence.",
            "scoring": "Transparent frequency-aware research-priority heuristic from public indicators. It is capped at low data support until direct sector evidence is connected and is never an expected-return estimate.",
            "research_policy": "Only manually reviewed facts and official institutional outlook records are published. Outlooks are attributed, reliability-tiered and non-scoring; unreviewed webpage sentiment is disabled.",
            "not_investment_advice": True,
        },
        "chart_layer": chart_layer,
        "cycle_state": cycle_state,
        "signal_groups": signal_groups,
        "subsectors": subsectors,
        "contradicting_evidence": contradicting_evidence,
        "source_status": source_status_records,
        "source_freshness": source_freshness,
        "source_health": _source_health_summary(source_freshness, source_status_records),
        "framework_coverage": framework_coverage,
        "research_facts": _public_research_facts(research_facts),
        "institutional_outlooks": outlook_summary(institutional_outlooks),
    }


def export_report_state(output_path: Path | None = None, store: RadarStore | None = None) -> Path:
    output = output_path or EXPORT_DIR / "public" / "data" / "report_state.json"
    output = output.resolve()
    root_relative = output.relative_to(get_settings().database_path.parents[2]) if output.is_absolute() else output
    if not is_public_export_path(root_relative):
        raise ValueError(f"Report state output is not public-allowlisted: {output}")

    state = build_report_state(store=store)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(state, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return output


def _subsector_record(rank: int, row: pd.Series, market_cycle: pd.DataFrame, research_facts: pd.DataFrame) -> dict[str, Any]:
    slug = str(row["slug"])
    taxonomy = subsector_by_slug().get(slug)
    signals = {column: _rounded(row[column], 3) for column in SIGNAL_COLUMNS if column in row}
    latest_market_cycle = _latest_market_cycle(slug, market_cycle)
    direct_evidence = bool(latest_market_cycle) and str(latest_market_cycle.get("source", "")).lower() not in {"", "sample_market_proxy"}
    cycle_phase = classify_subsector_phase(
        recovery=float(signals.get("recovery_potential", 0) or 0),
        momentum=float(signals.get("momentum", 0) or 0),
        macro=float(signals.get("macro_tailwind", 0) or 0),
        score=float(row["opportunity_score"]),
        confidence=float(signals.get("confidence", 0) or 0),
        direct_evidence=direct_evidence,
    )
    return {
        "slug": slug,
        "name": str(row["name"]),
        "group_name": str(row["group_name"]),
        "rank": rank if pd.notna(row["opportunity_score"]) else None,
        "score_status": row.get("score_status", "unknown"),
        "included_indicator_count": int(row.get("included_indicator_count", 0)),
        "expected_indicator_count": int(row.get("expected_indicator_count", 0)),
        "excluded_indicators": str(row.get("excluded_indicators", "")),
        "opportunity_score": _rounded(row["opportunity_score"], 1),
        "research_priority_score": _rounded(row.get("research_priority_score", row["opportunity_score"]), 1),
        "score_type": "research_priority_not_expected_return",
        "cycle_phase": cycle_phase,
        "cycle_direction": _direction_label(float(signals.get("momentum", 0) or 0)) if pd.notna(row["opportunity_score"]) else "unavailable",
        "signals": signals,
        "data_confidence": str(row.get("data_confidence", "")),
        "data_support": _rounded(row.get("data_support", row.get("confidence", 0)), 3),
        "evidence_gate": "direct_sector_evidence" if direct_evidence else "insufficient_direct_sector_evidence",
        "direct_evidence_required": list(taxonomy.direct_evidence_required) if taxonomy else [],
        "explanation": str(row.get("explanation", "")),
        "market_cycle": latest_market_cycle,
        "contradicting_evidence": _subsector_contradictions(str(row["name"]), signals, latest_market_cycle),
        "reviewed_public_fact_ids": _fact_ids_for_subsector(slug, research_facts),
    }


def _latest_market_cycle(slug: str, market_cycle: pd.DataFrame) -> dict[str, Any]:
    if market_cycle.empty or "subsector_slug" not in market_cycle:
        return {}
    frame = market_cycle[market_cycle["subsector_slug"] == slug].copy()
    if frame.empty:
        return {}
    frame["observed_at"] = pd.to_datetime(frame["observed_at"], errors="coerce")
    frame = frame.dropna(subset=["observed_at"]).sort_values("observed_at")
    latest = frame.iloc[-1]
    return {
        "observed_at": latest["observed_at"].date().isoformat(),
        **{column: _rounded(latest[column], 3) for column in MARKET_COLUMNS if column in latest},
        "source": str(latest.get("source", "")),
    }


def _latest_source_status(source_status: pd.DataFrame) -> list[dict[str, Any]]:
    if source_status.empty or "source_slug" not in source_status:
        return []
    frame = source_status.copy()
    frame["checked_at_sort"] = pd.to_datetime(frame.get("checked_at"), errors="coerce")
    frame = frame.sort_values(["source_slug", "checked_at_sort"]).drop_duplicates("source_slug", keep="last")
    records = []
    for _, row in frame.sort_values("source_slug").iterrows():
        records.append(
            {
                "source_slug": str(row["source_slug"]),
                "status": str(row.get("status", "")),
                "message": str(row.get("message", "")),
                "checked_at": str(row.get("checked_at", "")),
            }
        )
    return records


def _source_freshness(observations: pd.DataFrame, source_status: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return observation_health(
        observations,
        sample=any(item.get("source_slug") == "sample" for item in source_status),
        supported_slugs=set(build_indicator_metrics(observations)),
    )


def _source_health_summary(source_freshness: list[dict[str, Any]], source_status: list[dict[str, Any]]) -> dict[str, Any]:
    fallback_indicators = [
        str(item["indicator_slug"])
        for item in source_freshness
        if item.get("has_sample_fallback") or item.get("source_category") == "numeric_sample_fallback"
    ]
    sample_indicators = [
        str(item["indicator_slug"])
        for item in source_freshness
        if item.get("source_category") == "deterministic_sample"
    ]
    live_indicators = [
        str(item["indicator_slug"])
        for item in source_freshness
        if item.get("source_category") == "live_numeric"
    ]
    stale_indicators = [
        str(item["indicator_slug"])
        for item in source_freshness
        if item.get("freshness_status") in {"stale", "very_stale"}
    ]

    research_slugs = {source.slug for source in SOURCE_DEFINITIONS if source.source_type == "research" and source.access == "public"}
    research_page_statuses = [item for item in source_status if item.get("source_slug") in research_slugs]
    research_failures = [
        {
            "source_slug": str(item.get("source_slug", "")),
            "message": str(item.get("message", "")),
            "checked_at": str(item.get("checked_at", "")),
        }
        for item in research_page_statuses
        if str(item.get("status", "")).lower() not in {"ok", "sample"}
    ]
    research_mentions_fallback = _first_status(source_status, "research_fallback")
    evidence_fallback = _first_status(source_status, "research_evidence_fallback") or _first_status(source_status, "sample_research_evidence")
    evidence_files = _first_status(source_status, "research_evidence_files")

    if sample_indicators and len(sample_indicators) == len(source_freshness):
        numeric_mode = "deterministic_sample"
    elif fallback_indicators:
        numeric_mode = "live_with_numeric_sample_fallback"
    elif live_indicators:
        numeric_mode = "live_numeric"
    else:
        numeric_mode = "unknown"

    evidence_mode = "sample_fallback" if evidence_fallback else "structured_files" if evidence_files else "unknown"

    return {
        "numeric": numeric_health(source_freshness),
        "research_pages": {
            "checked_count": len(research_page_statuses),
            "failed_count": len(research_failures),
            "failed_sources": research_failures,
            "sample_mentions_fallback_used": bool(research_mentions_fallback),
            "sample_mentions_fallback_message": str(research_mentions_fallback.get("message", "")) if research_mentions_fallback else "",
        },
        "research_evidence": {
            "mode": evidence_mode,
            "fallback_used": bool(evidence_fallback),
            "message": str((evidence_fallback or evidence_files or {}).get("message", "")),
        },
    }


def _signal_groups(observations: pd.DataFrame, source_freshness: list[dict[str, Any]]) -> list[dict[str, Any]]:
    freshness_lookup = {str(item.get("indicator_slug", "")): item for item in source_freshness}
    credit_metrics = _indicator_signal_metrics(observations, CREDIT_LIQUIDITY_INDICATORS)
    macro_metrics = _indicator_signal_metrics(observations, MACRO_CONFIRMATION_INDICATORS)
    internals_metrics = _indicator_signal_metrics(observations, VALUATION_INTERNALS_INDICATORS)

    eligible = {r["indicator_slug"] for r in source_freshness if r.get("scoring_eligible")}
    credit_metrics = {k: v for k, v in credit_metrics.items() if k in eligible}
    macro_metrics = {k: v for k, v in macro_metrics.items() if k in eligible}
    internals_metrics = {k: v for k, v in internals_metrics.items() if k in eligible}

    credit_tailwind = _mean_float([item.get("tailwind_score") for item in credit_metrics.values()])
    macro_tailwind = _mean_float([item.get("tailwind_score") for item in macro_metrics.values()])
    internals_tailwind = _mean_float([item.get("tailwind_score") for item in internals_metrics.values()])

    return [
        {
            "group_id": "liquidity_credit",
            "title": "Liquidity and credit conditions",
            "status": _group_connection_status(CREDIT_LIQUIDITY_INDICATORS, freshness_lookup),
            "scoring_inclusion": False,
            "summary_label": _liquidity_label(credit_tailwind),
            "tailwind_score": _rounded(credit_tailwind, 3),
            "macro_confirmation": _confirmation_label(credit_tailwind, macro_tailwind),
            "macro_tailwind_reference": _rounded(macro_tailwind, 3),
            "methodology_note": "Non-scoring Sprint 10 signal group. Lower NFCI and lower St. Louis financial stress are treated as easier liquidity/credit conditions; higher values are treated as tighter or more stressed.",
            "indicators": _signal_group_indicators(CREDIT_LIQUIDITY_INDICATORS, credit_metrics, freshness_lookup),
        },
        {
            "group_id": "valuation_market_internals",
            "title": "Valuation and market internals reality check",
            "status": _group_connection_status(VALUATION_INTERNALS_INDICATORS, freshness_lookup),
            "scoring_inclusion": False,
            "summary_label": _valuation_internals_label(internals_tailwind),
            "tailwind_score": _rounded(internals_tailwind, 3),
            "macro_confirmation": _confirmation_label(internals_tailwind, macro_tailwind),
            "macro_tailwind_reference": _rounded(macro_tailwind, 3),
            "methodology_note": "Non-scoring Sprint 12 signal group. It uses broad public valuation, volatility, and equal-weight leadership proxies as a cycle reality check. It is not true Oslo subsector valuation, positioning, breadth, or analyst-revision coverage.",
            "indicators": _signal_group_indicators(VALUATION_INTERNALS_INDICATORS, internals_metrics, freshness_lookup),
        },
    ]


def _signal_group_indicators(
    slugs: tuple[str, ...],
    metrics: dict[str, dict[str, float]],
    freshness_lookup: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    indicators = []
    for slug in slugs:
        metric = metrics.get(slug, {})
        freshness = freshness_lookup.get(slug, {})
        indicators.append(
            {
                "indicator_slug": slug,
                "display_slug": str(freshness.get("display_slug") or slug),
                "indicator_name": str(freshness.get("indicator_name") or slug),
                "latest_observed_at": str(freshness.get("latest_observed_at") or ""),
                "source": str(freshness.get("source") or ""),
                "source_category": str(freshness.get("source_category") or "missing"),
                "freshness_status": str(freshness.get("freshness_status") or "missing"),
                "latest_value": _rounded_or_zero(metric.get("latest"), 4),
                "percentile": _rounded_or_zero(metric.get("percentile"), 3),
                "momentum": _rounded_or_zero(metric.get("momentum"), 3),
                "tailwind_score": _rounded_or_zero(metric.get("tailwind_score"), 3),
                "frequency_bucket": str(metric.get("frequency_bucket", "unknown")),
                "momentum_horizon": str(metric.get("momentum_horizon", "unknown")),
                "observation_count_used": int(metric.get("observation_count_used", 0) or 0),
            }
        )
    return indicators


def _group_connection_status(slugs: tuple[str, ...], freshness_lookup: dict[str, dict[str, Any]]) -> str:
    fallback_used = any(
        freshness_lookup.get(slug, {}).get("has_sample_fallback")
        or freshness_lookup.get(slug, {}).get("source_category") == "numeric_sample_fallback"
        for slug in slugs
    )
    live_count = sum(1 for slug in slugs if freshness_lookup.get(slug, {}).get("scoring_eligible"))
    if fallback_used:
        return "sample_fallback"
    if live_count == len(slugs):
        return "connected"
    if live_count:
        return "partial"
    return "missing"


def _indicator_signal_metrics(observations: pd.DataFrame, slugs: tuple[str, ...]) -> dict[str, dict[str, float]]:
    return build_indicator_metrics(observations, slugs)


def _direction_label(momentum: float) -> str:
    if momentum >= 0.15:
        return "improving"
    if momentum <= -0.15:
        return "deteriorating"
    return "stable/mixed"


def _mean_float(values: list[object]) -> float:
    numeric = [float(value) for value in values if value is not None]
    return sum(numeric) / len(numeric) if numeric else None


def _liquidity_label(score: float) -> str:
    if score is None:
        return "unavailable"
    if score >= 0.25:
        return "easier/liquidity tailwind"
    if score <= -0.25:
        return "tighter/stress headwind"
    return "mixed/neutral"


def _valuation_internals_label(score: float) -> str:
    if score is None:
        return "unavailable"
    if score >= 0.25:
        return "valuation/internals supportive"
    if score <= -0.25:
        return "crowding/volatility warning"
    return "mixed/neutral"


def _confirmation_label(credit_tailwind: float, macro_tailwind: float) -> str:
    if credit_tailwind is None or macro_tailwind is None:
        return "unavailable"
    if abs(credit_tailwind) < 0.15 or abs(macro_tailwind) < 0.15:
        return "mixed or not decisive"
    if credit_tailwind * macro_tailwind > 0:
        return "confirming macro signal"
    return "contradicting macro signal"


def _framework_coverage() -> list[dict[str, str]]:
    return [
        {
            "dimension": "Growth",
            "status": "partial",
            "current_coverage": "Monthly OECD CLI proxies for the G20, G7, United States, China and major Europe, plus World Bank annual real-GDP background.",
            "main_gap": "No direct PMI, industrial-production, or new-orders feed yet; direct OECD SDMX API access is documented but currently blocked from this environment, so CLI data is mirrored through DB.nomics.",
        },
        {
            "dimension": "Inflation",
            "status": "partial",
            "current_coverage": "Twelve-month CPI inflation for Norway, the United States, euro area, United Kingdom, Japan and China, plus commodity inputs.",
            "main_gap": "No harmonised core inflation, wage growth or market inflation-expectations layer across all economies.",
        },
        {
            "dimension": "Policy and rates",
            "status": "partial",
            "current_coverage": "BIS policy-rate series for the Fed, ECB, BoE, BoJ, PBoC, BoC, RBA, SNB and Riksbank; official Norges Bank rate; US nominal/real 10-year yields and 10y-2y curve.",
            "main_gap": "No market-implied policy paths, cross-country yield curves or central-bank balance-sheet layer.",
        },
        {
            "dimension": "Liquidity and credit",
            "status": "partial",
            "current_coverage": "Chicago Fed NFCI, St. Louis Fed Financial Stress, US high-yield and investment-grade spreads, and the broad trade-weighted dollar.",
            "main_gap": "No BIS credit/property-cycle data, lending surveys, default series or non-US credit-spread catalogue.",
        },
        {
            "dimension": "Earnings and margins",
            "status": "missing",
            "current_coverage": "No live earnings revision, margin, order-intake, or analyst-estimate feed.",
            "main_gap": "Likely requires paid data, manual reviewed evidence, or limited public filing/statement extraction.",
        },
        {
            "dimension": "Valuation and risk premium",
            "status": "partial",
            "current_coverage": "Broad US market-cap-to-GDP context derived from official FRED/Fed Z.1 and BEA inputs.",
            "main_gap": "No validated sector or constituent valuation multiples, earnings yields or equity-risk-premium surface.",
        },
        {
            "dimension": "Market internals and positioning",
            "status": "partial",
            "current_coverage": "VIX and adjusted-close S&P 500 equal-weight versus cap-weight leadership, plus ACWI, Europe, Japan, emerging-market and Nasdaq proxies.",
            "main_gap": "No true breadth, fund flows, short interest, CFTC or institutional positioning.",
        },
        {
            "dimension": "Subsector market cycle",
            "status": "missing_live_direct_evidence",
            "current_coverage": "Macro and industry-driver proxies only; deterministic sector histories are restricted to explicit sample builds.",
            "main_gap": "Requires validated global sector indices, relative returns, earnings revisions, valuation and operating evidence before a sector phase may be asserted.",
        },
        {
            "dimension": "Historical chart layer",
            "status": "partial",
            "current_coverage": "Static macro, central-bank, liquidity/credit, geopolitical and regional-market histories. Live sector charts remain empty when direct evidence is absent.",
            "main_gap": "No validated long-run sector-relative history or point-in-time backtest dataset yet.",
        },
        {
            "dimension": "Research evidence",
            "status": "limited",
            "current_coverage": "Committed reviewed public facts plus official, source-tiered institutional outlooks with publication dates, horizons, themes, risks and view dispersion. All remain non-scoring.",
            "main_gap": "Needs multiple independent claim-linked sector sources and a longer archived outlook revision history.",
        },
    ]


def _contradicting_evidence_summary(subsectors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for item in subsectors:
        for contradiction in item.get("contradicting_evidence", []):
            records.append(
                {
                    "subsector_slug": str(item.get("slug", "")),
                    "subsector_name": str(item.get("name", "")),
                    "rank": int(_rounded(item.get("rank"), 0)),
                    **contradiction,
                }
            )
    return sorted(records, key=lambda item: (-float(item.get("severity", 0)), int(item.get("rank") or 999)))[:8]


def _subsector_contradictions(name: str, signals: dict[str, Any], market_cycle: dict[str, Any]) -> list[dict[str, Any]]:
    recovery = float(signals.get("recovery_potential", 0) or 0)
    valuation = float(signals.get("valuation_proxy", 0) or 0)
    momentum = float(signals.get("momentum", 0) or 0)
    macro = float(signals.get("macro_tailwind", 0) or 0)
    confidence = float(signals.get("confidence", 0) or 0)
    relative_price = float(market_cycle.get("relative_price_index", 100) or 100)
    market_valuation = float(market_cycle.get("valuation_proxy", 100) or 100)

    records: list[dict[str, Any]] = []
    if recovery >= 0.2 and macro <= -0.15:
        records.append(
            _contradiction(
                "Recovery signal conflicts with macro backdrop",
                f"{name} has a positive recovery signal while the macro-tailwind component is negative.",
                {"recovery_potential": recovery, "macro_tailwind": macro},
            )
        )
    if recovery >= 0.2 and momentum <= -0.15:
        records.append(
            _contradiction(
                "Recovery signal lacks momentum confirmation",
                f"{name} scores positively on recovery potential, but the momentum component is negative.",
                {"recovery_potential": recovery, "momentum": momentum},
            )
        )
    if macro >= 0.2 and recovery <= -0.15:
        records.append(
            _contradiction(
                "Macro tailwind has not become a recovery signal",
                f"{name} has a positive macro backdrop, but the recovery component remains negative.",
                {"macro_tailwind": macro, "recovery_potential": recovery},
            )
        )
    if valuation >= 0.2 and market_valuation >= 110:
        records.append(
            _contradiction(
                "Cycle-position discount conflicts with sample market-cycle proxy",
                f"{name} has a positive cycle-position discount signal, but the sample-backed market-cycle proxy is elevated.",
                {"valuation_proxy": valuation, "market_cycle_valuation_pressure": (market_valuation - 100) / 100},
            )
        )
    if momentum >= 0.25 and relative_price < 95:
        records.append(
            _contradiction(
                "Momentum is improving from weak relative price",
                f"{name} has positive momentum while the sample-backed relative-price proxy remains below 95.",
                {"momentum": momentum, "relative_price_gap": (relative_price - 100) / 100},
            )
        )
    if confidence < 0.6 and (recovery >= 0.2 or valuation >= 0.2 or macro >= 0.2):
        records.append(
            _contradiction(
                "Signal depends on low-confidence coverage",
                f"{name} has at least one positive signal, but data confidence is below 60%.",
                {"confidence": confidence, "recovery_potential": recovery, "valuation_proxy": valuation, "macro_tailwind": macro},
            )
        )
    return sorted(records, key=lambda item: -float(item["severity"]))[:3]


def _contradiction(title: str, summary: str, components: dict[str, float]) -> dict[str, Any]:
    return {
        "title": title,
        "summary": summary,
        "components": {key: _rounded(value, 3) for key, value in components.items()},
        "severity": _rounded(sum(abs(float(value)) for value in components.values()) / max(len(components), 1), 3),
    }


def _source_category(source: str, has_sample_fallback: bool, deterministic_sample_build: bool = False) -> str:
    if has_sample_fallback or source == "sample_fallback":
        return "numeric_sample_fallback"
    if deterministic_sample_build or source == "sample":
        return "deterministic_sample"
    return "live_numeric"


def _freshness_status(age_days: int, expected_release_days: int = 75) -> str:
    return freshness_status(age_days, expected_release_days)


def _first_status(source_status: list[dict[str, Any]], source_slug: str) -> dict[str, Any] | None:
    for item in source_status:
        if item.get("source_slug") == source_slug:
            return item
    return None


def _public_research_facts(research_facts: pd.DataFrame) -> list[dict[str, Any]]:
    if research_facts.empty:
        return []
    frame = research_facts.copy()
    frame = frame[
        (frame["review_status"].astype(str).str.lower() == "reviewed")
        & (frame["evidence_scope"].astype(str).str.lower() == "public")
    ]
    records = []
    for _, row in frame.sort_values(["subsector_slug", "fact_id"]).iterrows():
        records.append(
            {
                "fact_id": str(row["fact_id"]),
                "subsector_slug": str(row["subsector_slug"]),
                "theme": str(row.get("theme", "")),
                "claim": str(row.get("claim", "")),
                "source_name": str(row.get("source_name", "")),
                "source_url": str(row.get("source_url", "")),
                "source_quality": str(row.get("source_quality", "")),
                "source_date": str(row.get("source_date", "")),
                "captured_at": str(row.get("captured_at", "")),
                "confidence": _rounded(row.get("confidence", 0), 3),
            }
        )
    return records


def _fact_ids_for_subsector(slug: str, research_facts: pd.DataFrame) -> list[str]:
    return [
        fact["fact_id"]
        for fact in _public_research_facts(research_facts)
        if fact["subsector_slug"] == slug
    ]


def _data_as_of(observations: pd.DataFrame, market_cycle: pd.DataFrame) -> str:
    candidates: list[pd.Timestamp] = []
    for frame, column in [(observations, "observed_at"), (market_cycle, "observed_at")]:
        if not frame.empty and column in frame:
            dates = pd.to_datetime(frame[column], errors="coerce").dropna()
            if not dates.empty:
                candidates.append(dates.max())
    if not candidates:
        return None
    return max(candidates).date().isoformat()


def _rounded(value: object, digits: int) -> float | None:
    return round(float(value), digits) if value is not None and pd.notna(value) else None


def _rounded_or_zero(value: object, digits: int) -> float:
    if value is None:
        return 0.0
    return round(float(value), digits)
