from __future__ import annotations

from datetime import datetime
from typing import Any

from .taxonomy import SUBSECTORS


PHASE_LANES = (
    {
        "phase": "deterioration/downturn",
        "label": "Deterioration",
        "short_label": "Protect",
        "interpretation": "Avoid assuming low prices are enough; wait for stabilization and improving evidence.",
        "x": 7,
        "y": 76,
    },
    {
        "phase": "early recovery candidate",
        "label": "Early recovery",
        "short_label": "Investigate",
        "interpretation": "Contrarian research zone. Require evidence that deterioration is slowing and momentum is turning.",
        "x": 24,
        "y": 55,
    },
    {
        "phase": "recovery confirmation",
        "label": "Recovery confirmation",
        "short_label": "Build evidence",
        "interpretation": "Recovery and momentum agree. Continue diligence rather than treating the label as an entry signal.",
        "x": 42,
        "y": 30,
    },
    {
        "phase": "mid-cycle continuation",
        "label": "Continuation",
        "short_label": "Let strength run",
        "interpretation": "Positive trend remains supported. Monitor invalidation instead of exiting solely because prices rose.",
        "x": 60,
        "y": 18,
    },
    {
        "phase": "late-cycle/crowded risk",
        "label": "Late-cycle risk",
        "short_label": "Do not chase",
        "interpretation": "Momentum may persist, but crowding or hostile conditions raise reversal and exit risk.",
        "x": 78,
        "y": 35,
    },
    {
        "phase": "transition watch",
        "label": "Transition / unclear",
        "short_label": "Wait for confirmation",
        "interpretation": "Signals conflict or sit near boundaries. Preserve optionality and identify the next confirming evidence.",
        "x": 94,
        "y": 62,
    },
)


PRIMARY_DATA_GAPS = {
    "crude_tankers": "No direct freight-rate, ton-mile, fleet-supply, orderbook, or scrapping history.",
    "product_chemical_tankers": "No direct product-tanker freight, refinery-margin, product-inventory, or fleet history.",
    "dry_bulk": "No direct dry-bulk freight, vessel-supply, steel-output, or commodity-flow history.",
    "lng_lpg_shipping": "No direct shipping-rate, gas-spread, export-capacity, or fleet-delivery history.",
    "offshore_vessels_drilling": "No direct dayrate, utilization, tender, fleet-supply, or offshore-capex history.",
    "oil_gas_ep": "No true forward-curve, reserve-replacement, earnings, tax-sensitivity, or subsector valuation history.",
    "oil_services": "No direct order-intake, backlog-quality, margin, tender, or earnings-revision history.",
    "seafood_aquaculture": "No direct salmon-price, biomass, disease, feed-cost, or regulatory history.",
    "metals_aluminum": "No direct power-cost, regional-premium, utilization, earnings, or subsector valuation history.",
    "renewables": "No direct power-price, project-return, auction, financing-spread, or company-balance-sheet history.",
    "norwegian_banks": "No direct credit-loss, funding-spread, housing, CRE-performance, or earnings-revision history.",
    "real_estate": "No direct rent, vacancy, refinancing, credit-spread, transaction, or asset-value history.",
    "industrial_tech_exporters": "No direct order-intake, semiconductor, export-volume, margin, or earnings-revision history.",
}


def build_decision_support(
    report_state: dict[str, Any],
    changes: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cycle_state = dict(report_state.get("cycle_state", {}))
    global_cycle = dict(cycle_state.get("global_equity_cycle", {}))
    subsectors = list(report_state.get("subsectors", []))
    taxonomy = {item.slug: item for item in SUBSECTORS}
    facts_by_slug: dict[str, list[dict[str, str]]] = {}
    for fact in report_state.get("research_facts", []):
        slug = str(fact.get("subsector_slug", ""))
        facts_by_slug.setdefault(slug, []).append(
            {
                "claim": str(fact.get("claim", "")),
                "source_name": str(fact.get("source_name", "")),
                "source_url": str(fact.get("source_url", "")),
                "source_date": str(fact.get("source_date", "")),
                "review_status": str(fact.get("review_status", "")),
            }
        )

    subsector_map = []
    for item in subsectors:
        slug = str(item.get("slug", ""))
        signals = dict(item.get("signals", {}))
        phase = str(item.get("cycle_phase", "transition watch"))
        definition = taxonomy.get(slug)
        contradiction_count = len(item.get("contradicting_evidence", []))
        data_support = float(item.get("data_support", signals.get("data_support", signals.get("confidence", 0))) or 0)
        market_source = str(item.get("market_cycle", {}).get("source", ""))
        proxy_only = str(item.get("evidence_gate", "")).startswith("insufficient") or not market_source or "sample" in market_source
        subsector_map.append(
            {
                "slug": slug,
                "name": str(item.get("name", "")),
                "group_name": str(item.get("group_name", "")),
                "phase": phase,
                "direction": str(item.get("cycle_direction", "stable/mixed")),
                "research_priority_band": _priority_band(
                    float(item.get("research_priority_score", item.get("opportunity_score", 0)) or 0),
                    phase,
                ),
                "research_priority_score": float(item.get("research_priority_score", item.get("opportunity_score", 0)) or 0),
                "investor_stance": _investor_stance(phase),
                "synthesis": _subsector_synthesis(item),
                "confirmation_needed": _confirmation_needed(phase, definition.drivers if definition else ()),
                "primary_data_gap": PRIMARY_DATA_GAPS.get(slug, "Primary subsector data remains incomplete."),
                "signal_data_quality": _label(data_support),
                "data_support": data_support,
                "evidence_gate": str(item.get("evidence_gate", "insufficient_direct_sector_evidence")),
                "evidence_boundary": (
                    "Macro-proxy screen; direct sector evidence is insufficient"
                    if proxy_only
                    else "Macro-proxy screen with reviewed market-history input"
                ),
                "reviewed_public_fact_count": len(facts_by_slug.get(slug, [])),
                "reviewed_public_facts": facts_by_slug.get(slug, [])[:3],
                "contradiction_count": contradiction_count,
                "signals": {
                    "recovery": float(signals.get("recovery_potential", 0) or 0),
                    "momentum": float(signals.get("momentum", 0) or 0),
                    "macro": float(signals.get("macro_tailwind", 0) or 0),
                    "cycle_position_discount": float(signals.get("valuation_proxy", 0) or 0),
                },
            }
        )

    sector_map = []
    for item in cycle_state.get("oslo_sector_read_through", []):
        sector_map.append(
            {
                "name": str(item.get("group_name", "")),
                "phase": str(item.get("phase", "transition watch")),
                "direction": _direction(float(item.get("momentum", 0) or 0)),
                "model_support": str(item.get("confidence", "unknown")),
                "read_through": str(item.get("read_through", "")),
            }
        )

    return {
        "version": "decision-support-v1-sprint16",
        "strategy": (
            "Use depressed or deteriorating areas as research candidates only when stabilization and improving "
            "momentum appear; let supported positive trends continue while their invalidation evidence remains "
            "absent; treat late-cycle/crowded configurations as do-not-chase and exit-risk alerts."
        ),
        "global": {
            "phase": str(global_cycle.get("phase", "unknown")),
            "status": str(global_cycle.get("status", "unknown")),
            "direction": str(global_cycle.get("direction", "unknown")),
            "summary": str(global_cycle.get("summary", "")),
            "classification_boundary": _global_boundary_message(str(global_cycle.get("phase", ""))),
            "what_changed": _change_summary(changes),
        },
        "trust": _trust_summary(report_state),
        "phase_lanes": list(PHASE_LANES),
        "sectors": sector_map,
        "subsectors": subsector_map,
        "research_groups": {
            "investigate": [
                item["slug"]
                for item in subsector_map
                if item["phase"] in {"early recovery candidate", "recovery confirmation"}
            ],
            "continuation": [
                item["slug"] for item in subsector_map if item["phase"] == "mid-cycle continuation"
            ],
            "risk_alert": [
                item["slug"]
                for item in subsector_map
                if item["phase"] in {"late-cycle/crowded risk", "deterioration/downturn"}
            ],
            "transition": [
                item["slug"] for item in subsector_map if item["phase"] == "transition watch"
            ],
        },
        "curve_boundary": (
            "The curve is a state map, not a price forecast or timing model. Marker positions come from the "
            "published rule-based phase labels. Subsector markers remain macro-proxy classifications until "
            "true subsector market, valuation, earnings, and positioning histories are connected."
        ),
    }


def _trust_summary(report_state: dict[str, Any]) -> dict[str, Any]:
    numeric = dict(report_state.get("source_health", {}).get("numeric", {}))
    indicator_count = max(1, int(numeric.get("indicator_count", 0) or 0))
    live_count = int(numeric.get("live_indicator_count", 0) or 0)
    fallback_count = int(numeric.get("sample_fallback_indicator_count", 0) or 0)
    stale_count = int(numeric.get("stale_indicator_count", 0) or 0)
    data_score = max(
        0.0,
        min(
            1.0,
            live_count / indicator_count
            - min(0.45, fallback_count * 0.15)
            - min(0.2, stale_count / indicator_count * 0.6),
        ),
    )

    cycle_confidence = dict(report_state.get("cycle_state", {}).get("confidence", {}))
    model_score = float(cycle_confidence.get("score", 0) or 0)
    contradictions = len(report_state.get("cycle_state", {}).get("contradictions", []))
    caveats = len(report_state.get("cycle_state", {}).get("missing_data_caveats", []))

    validation = dict(report_state.get("report_history_validation", {}))
    full_count = int(validation.get("full_state_snapshot_count", 0) or 0)
    start = _date(validation.get("coverage_start"))
    end = _date(validation.get("coverage_end"))
    span_days = max(0, (end - start).days) if start and end else 0
    history_score = min(1.0, full_count / 12) * 0.7 + min(1.0, span_days / 180) * 0.3
    history_label = (
        "insufficient"
        if full_count < 6 or span_days < 28
        else "developing"
        if full_count < 12 or span_days < 90
        else "established"
    )

    return {
        "data_quality": {
            "label": _label(data_score),
            "score": round(data_score, 3),
            "detail": (
                f"{live_count} of {indicator_count} indicators are live; {fallback_count} numeric fallback; "
                f"{stale_count} stale."
            ),
        },
        "model_support": {
            "label": _label(model_score),
            "score": round(model_score, 3),
            "detail": (
                f"Rule-based signal agreement after {contradictions} contradictions and {caveats} visible caveats. "
                "This is not a probability of being correct."
            ),
        },
        "historical_validation": {
            "label": history_label,
            "score": round(history_score, 3),
            "detail": (
                f"{full_count} full report states across {span_days} calendar days. "
                "Current replay checks implementation consistency, not predictive accuracy."
            ),
        },
    }


def _subsector_synthesis(item: dict[str, Any]) -> str:
    phase = str(item.get("cycle_phase", "transition watch"))
    signals = dict(item.get("signals", {}))
    recovery = float(signals.get("recovery_potential", 0) or 0)
    momentum = float(signals.get("momentum", 0) or 0)
    macro = float(signals.get("macro_tailwind", 0) or 0)
    return (
        f"{phase.replace('_', ' ')}: recovery {recovery:+.2f}, momentum {momentum:+.2f}, "
        f"macro {macro:+.2f}. Treat this as a research-state classification, not an entry or exit instruction."
    )


def _confirmation_needed(phase: str, drivers: tuple[str, ...]) -> str:
    driver_text = ", ".join(drivers[:3]) if drivers else "primary subsector drivers"
    if phase == "deterioration/downturn":
        return f"Require stabilization plus improving momentum in {driver_text} before treating weakness as opportunity."
    if phase == "early recovery candidate":
        return f"Seek momentum and fundamental confirmation from {driver_text}; low prices alone are insufficient."
    if phase == "recovery confirmation":
        return f"Confirm persistence through {driver_text} and check that valuation or crowding has not replaced recovery."
    if phase == "mid-cycle continuation":
        return f"Monitor {driver_text} for deterioration; supported momentum can continue longer than expected."
    if phase == "late-cycle/crowded risk":
        return f"Avoid chasing. Watch {driver_text} and breadth/momentum for rollover or evidence that the warning is easing."
    return f"Wait for agreement between momentum, macro evidence, and {driver_text}."


def _investor_stance(phase: str) -> str:
    return {
        "deterioration/downturn": "Protect capital; weakness is not yet a contrarian trigger.",
        "early recovery candidate": "Investigate contrarian setup; require confirmation.",
        "recovery confirmation": "Deepen diligence; recovery and momentum are beginning to agree.",
        "mid-cycle continuation": "Let supported strength run; monitor invalidation.",
        "late-cycle/crowded risk": "Do not chase; review exposure and exit-risk evidence.",
        "transition watch": "Keep on watch; conflicting signals need resolution.",
        "insufficient evidence": "Do not infer a state from missing evidence.",
    }.get(phase, "Use as a research prompt, not a trading instruction.")


def _priority_band(score: float, phase: str) -> str:
    if phase == "insufficient evidence":
        return "insufficient evidence"
    if phase in {"late-cycle/crowded risk", "deterioration/downturn"}:
        return "risk review"
    if phase == "transition watch":
        return "watch"
    if phase == "mid-cycle continuation":
        return "continuation review"
    if phase in {"early recovery candidate", "recovery confirmation"}:
        return "priority review" if score >= 55 else "investigate"
    if score >= 60:
        return "priority review"
    if score >= 55:
        return "watch"
    if score >= 48:
        return "neutral"
    return "deprioritized"


def _global_boundary_message(phase: str) -> str:
    if phase == "late-cycle/crowded risk":
        return (
            "The warning would ease if rates pressure and market internals improve while growth holds. "
            "It would worsen if growth or liquidity deteriorates enough to confirm downturn risk."
        )
    if phase in {"recovery confirmation", "mid-cycle continuation"}:
        return (
            "Continuation remains supported while growth, liquidity, and market direction agree. "
            "A rates, liquidity, or internals reversal would weaken it."
        )
    if phase == "deterioration/downturn":
        return (
            "The downturn read requires stabilization in growth/liquidity and improving direction before a "
            "contrarian recovery interpretation is credible."
        )
    return "The classification is near a decision boundary; require persistence and confirming evidence."


def _change_summary(changes: dict[str, Any] | None) -> str:
    if not changes:
        return "No comparable prior full state was supplied for this build."
    summary = dict(changes.get("summary", {}))
    cycle_changes = int(summary.get("cycle_state_changes", 0) or 0)
    subsector_changes = int(summary.get("subsector_changes", 0) or 0)
    source_changes = int(summary.get("source_status_changes", 0) or 0)
    return (
        f"{cycle_changes} cycle-state changes, {subsector_changes} subsector changes, "
        f"and {source_changes} source-status changes versus the prior report."
    )


def _direction(momentum: float) -> str:
    if momentum >= 0.15:
        return "improving"
    if momentum <= -0.15:
        return "deteriorating"
    return "stable/mixed"


def _label(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.55:
        return "medium"
    if score >= 0.3:
        return "low"
    return "very low"


def _date(value: Any):
    try:
        return datetime.fromisoformat(str(value)[:10]).date()
    except ValueError:
        return None
