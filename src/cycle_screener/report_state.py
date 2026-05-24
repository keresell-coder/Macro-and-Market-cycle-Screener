from __future__ import annotations

from datetime import date, datetime, timezone
import json
from pathlib import Path
from typing import Any

import pandas as pd

from .config import EXPORT_DIR, get_settings
from .indicators import indicator_by_slug
from .publication import is_public_export_path
from .sources import SOURCE_DEFINITIONS
from .storage import RadarStore


SIGNAL_COLUMNS = (
    "cycle_pressure",
    "recovery_potential",
    "valuation_proxy",
    "momentum",
    "macro_tailwind",
    "narrative_divergence",
    "confidence",
)

MARKET_COLUMNS = (
    "price_index",
    "benchmark_index",
    "relative_price_index",
    "valuation_proxy",
    "driver_pressure",
)

REPORT_STATE_VERSION = "2026-05-24-sprint6"
SCORING_METHODOLOGY_VERSION = "score-v1-public-cycle-radar"


def build_report_state(store: RadarStore | None = None) -> dict[str, Any]:
    owns_store = store is None
    if store is None:
        store = RadarStore(get_settings().database_path)

    scores = store.table("subsector_scores")
    observations = store.table("observations")
    source_status = store.table("source_status")
    research_facts = store.table("research_facts")
    market_cycle = store.table("subsector_market_cycle")

    if owns_store:
        store.close()

    ranked_scores = scores.sort_values("opportunity_score", ascending=False).reset_index(drop=True)
    subsectors = [_subsector_record(rank, row, market_cycle, research_facts) for rank, (_, row) in enumerate(ranked_scores.iterrows(), start=1)]

    source_status_records = _latest_source_status(source_status)
    source_freshness = _source_freshness(observations, source_status_records)

    return {
        "schema_version": REPORT_STATE_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "data_as_of": _data_as_of(observations, market_cycle),
        "methodology": {
            "scoring_version": SCORING_METHODOLOGY_VERSION,
            "report_state_version": REPORT_STATE_VERSION,
            "framework_reference": "docs/knowledge_base/global_macro_market_cycle_knowledge_base.md",
            "framework_coverage": "Partial implementation of a broader macro and market-cycle framework. Current scoring covers public macro, rates, FX, commodity, market-proxy, source-health, and reviewed-public-research evidence, but does not yet include full credit, earnings-revisions, valuation-multiple, positioning, or licensed subsector market data.",
            "implementation_boundary": "Opportunity scores are research triage signals, not cycle-state labels, return forecasts, or investment advice. Missing dimensions should be treated as explicit blind spots rather than neutral evidence.",
            "scoring": "Transparent subsector scoring from public/free indicators and sample fallbacks.",
            "research_policy": "Only reviewed public research facts are included in public report state. Unreviewed and manual evidence remain local.",
            "not_investment_advice": True,
        },
        "subsectors": subsectors,
        "source_status": source_status_records,
        "source_freshness": source_freshness,
        "source_health": _source_health_summary(source_freshness, source_status_records),
        "framework_coverage": _framework_coverage(),
        "research_facts": _public_research_facts(research_facts),
    }


def export_report_state(output_path: Path | None = None, store: RadarStore | None = None) -> Path:
    output = output_path or EXPORT_DIR / "public" / "data" / "report_state.json"
    output = output.resolve()
    root_relative = output.relative_to(get_settings().database_path.parents[2]) if output.is_absolute() else output
    if not is_public_export_path(root_relative):
        raise ValueError(f"Report state output is not public-allowlisted: {output}")

    state = build_report_state(store=store)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def _subsector_record(rank: int, row: pd.Series, market_cycle: pd.DataFrame, research_facts: pd.DataFrame) -> dict[str, Any]:
    slug = str(row["slug"])
    return {
        "slug": slug,
        "name": str(row["name"]),
        "group_name": str(row["group_name"]),
        "rank": rank,
        "opportunity_score": _rounded(row["opportunity_score"], 1),
        "signals": {column: _rounded(row[column], 3) for column in SIGNAL_COLUMNS if column in row},
        "data_confidence": str(row.get("data_confidence", "")),
        "explanation": str(row.get("explanation", "")),
        "market_cycle": _latest_market_cycle(slug, market_cycle),
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
    if observations.empty or "indicator_slug" not in observations or "observed_at" not in observations:
        return []

    indicator_lookup = indicator_by_slug()
    deterministic_sample_build = any(item.get("source_slug") == "sample" for item in source_status)
    today = datetime.now(timezone.utc).date()
    frame = observations.copy()
    frame["observed_at_sort"] = pd.to_datetime(frame["observed_at"], errors="coerce")
    frame = frame.dropna(subset=["observed_at_sort"])
    records = []

    for indicator_slug, group in frame.groupby("indicator_slug"):
        group = group.sort_values("observed_at_sort")
        latest = group.iloc[-1]
        observed_date = latest["observed_at_sort"].date()
        source = str(latest.get("source", ""))
        sources_seen = sorted({str(value) for value in group.get("source", pd.Series(dtype=str)).dropna().unique()})
        has_sample_fallback = "sample_fallback" in sources_seen
        source_category = _source_category(source, has_sample_fallback, deterministic_sample_build)
        age_days = max(0, (today - observed_date).days)
        indicator = indicator_lookup.get(str(indicator_slug))
        records.append(
            {
                "indicator_slug": str(indicator_slug),
                "indicator_name": indicator.name if indicator else str(indicator_slug),
                "latest_observed_at": observed_date.isoformat(),
                "age_days": age_days,
                "observation_count": int(len(group)),
                "source": source,
                "sources_seen": sources_seen,
                "source_category": source_category,
                "has_sample_fallback": has_sample_fallback,
                "freshness_status": _freshness_status(indicator.source if indicator else source, age_days),
            }
        )

    return sorted(records, key=lambda item: item["indicator_slug"])


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
        "numeric": {
            "mode": numeric_mode,
            "indicator_count": len(source_freshness),
            "live_indicator_count": len(live_indicators),
            "sample_build_indicator_count": len(sample_indicators),
            "sample_fallback_indicator_count": len(fallback_indicators),
            "sample_fallback_indicators": fallback_indicators,
            "stale_indicator_count": len(stale_indicators),
            "stale_indicators": stale_indicators,
        },
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


def _framework_coverage() -> list[dict[str, str]]:
    return [
        {
            "dimension": "Growth",
            "status": "proxied",
            "current_coverage": "World Bank annual global and China growth proxies plus commodity and market proxies.",
            "main_gap": "No true live PMI, OECD CLI, industrial-production, or new-orders feed yet.",
        },
        {
            "dimension": "Inflation",
            "status": "partial",
            "current_coverage": "Norway CPI plus commodity and input-cost proxies.",
            "main_gap": "No broad core inflation, wage, inflation-expectations, or supplier-delivery layer.",
        },
        {
            "dimension": "Policy and rates",
            "status": "partial",
            "current_coverage": "Norges Bank policy rate and US 10-year yield proxy.",
            "main_gap": "No full yield curve, real yields, policy-path, or central-bank balance-sheet layer.",
        },
        {
            "dimension": "Liquidity and credit",
            "status": "missing",
            "current_coverage": "No direct live credit or financial-conditions series in scoring.",
            "main_gap": "Needs terms-compliant credit spreads, NFCI/financial conditions, lending standards, loan growth, or credit-to-GDP data.",
        },
        {
            "dimension": "Earnings and margins",
            "status": "missing",
            "current_coverage": "No live earnings revision, margin, order-intake, or analyst-estimate feed.",
            "main_gap": "Likely requires paid data, manual reviewed evidence, or limited public filing/statement extraction.",
        },
        {
            "dimension": "Valuation and risk premium",
            "status": "proxied",
            "current_coverage": "Uses scoring proxy and deterministic market-cycle valuation history.",
            "main_gap": "No true Oslo subsector valuation multiples or equity-risk-premium feed.",
        },
        {
            "dimension": "Market internals and positioning",
            "status": "limited",
            "current_coverage": "NASDAQ and broad market chart proxies only.",
            "main_gap": "No breadth, volatility, fund-flow, short-interest, CFTC, or positioning layer.",
        },
        {
            "dimension": "Subsector market cycle",
            "status": "sample_backed",
            "current_coverage": "Deterministic price, relative-price, valuation, and driver-pressure histories.",
            "main_gap": "Needs reviewed public or licensed Oslo subsector market data before being treated as real market history.",
        },
        {
            "dimension": "Research evidence",
            "status": "sample_backed",
            "current_coverage": "Reviewed public sample facts plus optional local reviewed CSV ingestion.",
            "main_gap": "Needs analyst-reviewed public/manual CSV evidence for priority subsectors.",
        },
    ]


def _source_category(source: str, has_sample_fallback: bool, deterministic_sample_build: bool = False) -> str:
    if has_sample_fallback or source == "sample_fallback":
        return "numeric_sample_fallback"
    if deterministic_sample_build or source == "sample":
        return "deterministic_sample"
    return "live_numeric"


def _freshness_status(indicator_source: str, age_days: int) -> str:
    stale_after, very_stale_after = (550, 800) if indicator_source == "world_bank_indicator" else (75, 125)
    if age_days > very_stale_after:
        return "very_stale"
    if age_days > stale_after:
        return "stale"
    return "current"


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
        return date.today().isoformat()
    return max(candidates).date().isoformat()


def _rounded(value: object, digits: int) -> float:
    return round(float(value), digits)
