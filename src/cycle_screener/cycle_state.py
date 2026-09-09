from __future__ import annotations

from collections import defaultdict
from typing import Any

import pandas as pd

from .indicators import indicator_by_slug, public_indicator_slug
from .signal_metrics import build_indicator_metrics


CYCLE_STATE_VERSION = "cycle-state-v4-observation-health-gated"

GROWTH_INDICATORS = ("g20_cli", "g7_cli", "us_cli", "china_cli", "europe_cli", "global_pmi", "china_growth_proxy")
INFLATION_RATES_INDICATORS = (
    "norway_cpi", "us_cpi", "euro_cpi", "uk_cpi", "japan_cpi", "china_cpi",
    "rates_pressure", "us_real_10y_yield", "norges_bank_policy_rate", "fed_policy_rate",
    "ecb_policy_rate", "boe_policy_rate", "boj_policy_rate", "pboc_policy_rate",
    "boc_policy_rate", "rba_policy_rate", "snb_policy_rate", "riksbank_policy_rate",
    "brent", "us_natural_gas",
)
LIQUIDITY_CREDIT_INDICATORS = (
    "chicago_fed_nfci", "st_louis_financial_stress", "us_high_yield_spread",
    "us_investment_grade_spread", "broad_us_dollar",
)
MARKET_PRICING_INDICATORS = (
    "global_equity_proxy", "europe_equity_proxy", "japan_equity_proxy", "em_equity_proxy",
    "nasdaq_proxy", "copper", "aluminum", "geopolitical_risk",
)
VALUATION_INTERNALS_INDICATORS = ("us_equity_market_cap_gdp_proxy", "vix_proxy", "sp500_equal_weight_leadership_proxy")


def build_cycle_state(
    observations: pd.DataFrame,
    source_freshness: list[dict[str, Any]],
    signal_groups: list[dict[str, Any]],
    subsectors: list[dict[str, Any]],
    contradicting_evidence: list[dict[str, Any]],
    framework_coverage: list[dict[str, Any]],
) -> dict[str, Any]:
    freshness_lookup = {str(item.get("indicator_slug", "")): item for item in source_freshness}
    metrics = _indicator_metrics(observations)

    dimensions = [
        _dimension(
            "growth",
            "Growth",
            "OECD turning-point indicators across the G20, G7, US, China and Europe, with annual GDP retained only as slow background.",
            GROWTH_INDICATORS,
            metrics,
            freshness_lookup,
            positive_label="growth support",
            negative_label="growth deterioration",
        ),
        _dimension(
            "inflation_rates",
            "Inflation and rates pressure",
            "Inflation and policy-rate evidence across major economies, plus nominal/real yields and energy pressure. Country series first collapse to family-level signals.",
            INFLATION_RATES_INDICATORS,
            metrics,
            freshness_lookup,
            positive_label="pressure easing",
            negative_label="pressure tightening",
        ),
        _dimension(
            "liquidity_credit",
            "Liquidity and credit",
            "Financial conditions, stress, credit spreads and broad-dollar liquidity. Positive scores mean easier conditions.",
            LIQUIDITY_CREDIT_INDICATORS,
            metrics,
            freshness_lookup,
            positive_label="liquidity tailwind",
            negative_label="credit/liquidity headwind",
        ),
        _dimension(
            "market_pricing",
            "Market pricing and risk appetite",
            "Global, European, Japanese, emerging-market and technology equities, industrial metals and geopolitical risk.",
            MARKET_PRICING_INDICATORS,
            metrics,
            freshness_lookup,
            positive_label="risk appetite supportive",
            negative_label="risk appetite fading",
        ),
        _dimension(
            "valuation_internals",
            "Valuation and market internals reality check",
            "Broad public valuation, volatility, and breadth-like leadership proxies. This is not true Oslo subsector valuation, positioning, or analyst-revision coverage.",
            VALUATION_INTERNALS_INDICATORS,
            metrics,
            freshness_lookup,
            positive_label="valuation/internals supportive",
            negative_label="valuation/internals warning",
        ),
    ]

    dimension_lookup = {item["dimension_id"]: item for item in dimensions}
    cycle_contradictions = _cycle_contradictions(dimension_lookup, contradicting_evidence)
    global_equity = _global_equity_cycle(dimension_lookup, cycle_contradictions)
    oslo_read = _oslo_read_through(subsectors)
    missing_caveats = _missing_data_caveats(framework_coverage, source_freshness)

    return {
        "version": CYCLE_STATE_VERSION,
        "global_equity_cycle": global_equity,
        "dimensions": dimensions,
        "oslo_sector_read_through": oslo_read,
        "cycle_clocks": _cycle_clocks(dimension_lookup, subsectors),
        "transition_evidence": _transition_evidence(global_equity, dimensions, cycle_contradictions),
        "continuation_evidence": _continuation_evidence(dimensions),
        "contradictions": cycle_contradictions,
        "confidence": _overall_confidence(global_equity, dimensions, missing_caveats),
        "data_support": _overall_confidence(global_equity, dimensions, missing_caveats),
        "missing_data_caveats": missing_caveats,
        "methodology_note": (
            "Version 4 applies one observation-health gate across economic, inflation/rates, financial/liquidity, market-pricing and sector-operating clocks; "
            "uses explicit source/transform contracts; averages correlated indicators at family level; and excludes stale inputs from scores. "
            "Data support describes availability and freshness, never empirical accuracy. The global output is a heuristic risk regime, "
            "not a dated business-cycle fact, probability, return forecast, timing signal, or investment advice."
        ),
    }


def _dimension(
    dimension_id: str,
    title: str,
    description: str,
    slugs: tuple[str, ...],
    metrics: dict[str, dict[str, float]],
    freshness_lookup: dict[str, dict[str, Any]],
    *,
    positive_label: str,
    negative_label: str,
    use_risk_appetite: bool = False,
) -> dict[str, Any]:
    evidence: list[dict[str, Any]] = []
    family_scores: dict[str, list[float]] = defaultdict(list)
    family_momentum: dict[str, list[float]] = defaultdict(list)
    live_count = 0
    fallback_count = 0
    stale_count = 0

    definitions = indicator_by_slug()
    for slug in slugs:
        metric = metrics.get(slug)
        freshness = freshness_lookup.get(slug, {})
        if not metric:
            continue

        score = _risk_appetite_score(metric) if use_risk_appetite else float(metric["tailwind_score"])
        source_category = str(freshness.get("source_category", "missing"))
        freshness_status = str(freshness.get("freshness_status", "missing"))
        if source_category == "live_numeric":
            live_count += 1
        if source_category in {"numeric_sample_fallback", "deterministic_sample"} or freshness.get("has_sample_fallback"):
            fallback_count += 1
        if freshness_status in {"stale", "very_stale"}:
            stale_count += 1
        definition = definitions.get(slug)
        family = str(metric.get("family") or (definition.family if definition else "other"))
        scoring_status = "included" if freshness.get("scoring_eligible", freshness_status == "current") or (source_category == "deterministic_sample" and not freshness.get("future_dated_observation")) else "excluded_" + str(freshness.get("exclusion_reason", freshness_status))
        if scoring_status == "included":
            family_scores[family].append(score)
            family_momentum[family].append(float(metric.get("economic_momentum", 0.0)))
        evidence.append(
            {
                "indicator_slug": slug,
                "display_slug": public_indicator_slug(slug),
                "indicator_name": definition.name if definition else slug,
                "latest_value": _rounded(metric["raw_latest"], 4),
                "transformed_latest": _rounded(metric["latest"], 4),
                "transform": str(metric.get("transform", "level")),
                "family": family,
                "percentile": _rounded(metric["percentile"], 3),
                "momentum": _rounded(metric["momentum"], 3),
                "economic_momentum": _rounded(metric.get("economic_momentum", 0.0), 3),
                "score": _rounded(score, 3),
                "scoring_status": scoring_status,
                "frequency_bucket": str(metric.get("frequency_bucket", "unknown")),
                "momentum_horizon": str(metric.get("momentum_horizon", "unknown")),
                "observation_count_used": int(metric.get("observation_count_used", 0) or 0),
                "latest_observed_at": str(freshness.get("latest_observed_at", "")),
                "source_category": source_category,
                "freshness_status": freshness_status,
            }
        )

    expected_families = {definitions[slug].family for slug in slugs if slug in definitions}
    available_family_scores = [_mean(values) for values in family_scores.values() if values]
    available_family_momentum = [_mean(values) for values in family_momentum.values() if values]
    coverage_ratio = len(family_scores) / max(len(expected_families), 1)
    score = _mean(available_family_scores)
    direction_score = _mean(available_family_momentum)
    direction = _direction_label(direction_score)
    status = _status_label(score, positive_label, negative_label)
    confidence_score = _confidence_score(coverage_ratio, sum(len(values) for values in family_scores.values()), len(evidence), 0, 0)
    phase = _phase_label(score, direction_score, coverage_ratio, confidence_score)

    return {
        "dimension_id": dimension_id,
        "title": title,
        "description": description,
        "phase": phase,
        "status": status if family_scores else "insufficient evidence",
        "direction": direction if family_scores else "unavailable",
        "score": _rounded(score, 3) if family_scores else None,
        "direction_score": _rounded(direction_score, 3) if family_scores else None,
        "confidence": _confidence_label(confidence_score),
        "data_support": _confidence_label(confidence_score),
        "confidence_score": _rounded(confidence_score, 3),
        "confidence_type": "data_coverage_and_freshness",
        "coverage": {
            "available_count": sum(item["scoring_status"] == "included" for item in evidence),
            "observed_count": len(evidence),
            "expected_count": len(slugs),
            "coverage_ratio": _rounded(coverage_ratio, 3),
            "available_family_count": len(family_scores),
            "expected_family_count": len(expected_families),
            "live_count": live_count,
            "fallback_or_sample_count": fallback_count,
            "stale_count": stale_count,
        },
        "evidence": sorted(evidence, key=lambda item: abs(float(item["score"])), reverse=True)[:6],
        "missing_indicators": [slug for slug in slugs if slug not in metrics],
        "excluded_indicators": [item["indicator_slug"] for item in evidence if item["scoring_status"] != "included"],
    }


def _indicator_metrics(observations: pd.DataFrame) -> dict[str, dict[str, float]]:
    return build_indicator_metrics(observations)


def _risk_appetite_score(metric: dict[str, float]) -> float:
    return float(metric["tailwind_score"])


def _global_equity_cycle(dimensions: dict[str, dict[str, Any]], contradictions: list[dict[str, Any]]) -> dict[str, Any]:
    weights = {
        "growth": 0.3,
        "inflation_rates": 0.18,
        "liquidity_credit": 0.22,
        "market_pricing": 0.2,
        "valuation_internals": 0.1,
    }
    available = [key for key in weights if dimensions.get(key, {}).get("phase") != "insufficient evidence"]
    if len(available) < len(weights):
        return {
            "phase": "insufficient evidence",
            "regime": "insufficient evidence",
            "regime_type": "heuristic_global_market_risk_regime",
            "status": "insufficient evidence",
            "direction": "unclear",
            "score": None,
            "confidence": "low",
            "data_support": "low",
            "confidence_score": 0.0,
            "confidence_type": "data_coverage_and_signal_agreement",
            "summary": "One or more cycle dimensions are unavailable; missing evidence is not treated as neutral. No global regime is published.",
            "primary_evidence": [],
        }

    weighted_score = sum(float(dimensions[key]["score"]) * weights[key] for key in available) / sum(weights[key] for key in available)
    direction_score = _mean([float(dimensions[key]["direction_score"]) for key in available])
    growth = float(dimensions["growth"]["score"])
    rates = float(dimensions["inflation_rates"]["score"])
    liquidity = float(dimensions["liquidity_credit"]["score"])
    market = float(dimensions["market_pricing"]["score"])
    internals = float(dimensions.get("valuation_internals", {}).get("score") if dimensions.get("valuation_internals", {}).get("score") is not None else float("nan"))

    phase = classify_global_phase(
        growth=growth,
        rates=rates,
        liquidity=liquidity,
        market=market,
        internals=internals,
        weighted_score=weighted_score,
        direction_score=direction_score,
        has_contradictions=bool(contradictions),
    )

    confidence_score = _mean([float(dimensions[key]["confidence_score"]) for key in available])
    confidence_score -= min(0.2, len(contradictions) * 0.04)
    confidence_score = max(0.0, confidence_score)
    status = _global_status(phase)
    direction = _direction_label(direction_score)

    return {
        "phase": phase,
        "regime": phase,
        "regime_type": "heuristic_global_market_risk_regime",
        "status": status,
        "direction": direction,
        "score": _rounded(weighted_score, 3),
        "confidence": _confidence_label(confidence_score),
        "data_support": _confidence_label(confidence_score),
        "confidence_score": _rounded(confidence_score, 3),
        "confidence_type": "data_coverage_and_signal_agreement",
        "summary": _global_summary(phase, weighted_score, direction, contradictions),
        "boundary_diagnostics": _boundary_diagnostics(
            growth=growth,
            rates=rates,
            liquidity=liquidity,
            market=market,
            internals=internals,
            weighted_score=weighted_score,
        ),
        "primary_evidence": [
            {
                "dimension_id": dimensions[key]["dimension_id"],
                "title": dimensions[key]["title"],
                "phase": dimensions[key]["phase"],
                "status": dimensions[key]["status"],
                "score": dimensions[key]["score"],
                "direction": dimensions[key]["direction"],
            }
            for key in available
        ],
    }


def _boundary_diagnostics(*, growth: float, rates: float, liquidity: float, market: float, internals: float, weighted_score: float) -> dict[str, Any]:
    late_cycle_margins = {
        "market_above_trigger": market - 0.25,
        "growth_above_floor": growth + 0.10,
        "rates_from_headwind_trigger": rates + 0.20,
        "liquidity_from_headwind_trigger": liquidity + 0.20,
        "internals_from_warning_trigger": internals + 0.25,
    }
    distances = [abs(weighted_score - value) for value in (-0.25, -0.05, 0.18, 0.28)]
    return {
        "nearest_composite_threshold_distance": _rounded(min(distances), 3),
        "late_cycle_rule_margins": {key: _rounded(value, 3) for key, value in late_cycle_margins.items()},
        "interpretation": "Small absolute margins indicate classification fragility; they are not probabilities.",
    }


def classify_global_phase(
    *,
    growth: float,
    rates: float,
    liquidity: float,
    market: float,
    internals: float,
    weighted_score: float,
    direction_score: float,
    has_contradictions: bool,
) -> str:
    if market >= 0.25 and (rates <= -0.2 or liquidity <= -0.2 or internals <= -0.25) and growth >= -0.1:
        return "late-cycle/crowded risk"
    if weighted_score <= -0.25 or (growth <= -0.25 and liquidity <= -0.15):
        return "deterioration/downturn"
    if has_contradictions and abs(weighted_score) < 0.35:
        return "transition watch"
    if weighted_score >= 0.28 and direction_score >= 0.12:
        return "recovery confirmation"
    if weighted_score >= 0.18:
        return "mid-cycle continuation"
    if weighted_score >= -0.05 and direction_score >= 0.15:
        return "early recovery candidate"
    if abs(weighted_score) < 0.18:
        return "transition watch"
    return "deterioration/downturn"


def _cycle_contradictions(dimensions: dict[str, dict[str, Any]], subsector_contradictions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    growth = float(dimensions.get("growth", {}).get("score") if dimensions.get("growth", {}).get("score") is not None else float("nan"))
    rates = float(dimensions.get("inflation_rates", {}).get("score") if dimensions.get("inflation_rates", {}).get("score") is not None else float("nan"))
    liquidity = float(dimensions.get("liquidity_credit", {}).get("score") if dimensions.get("liquidity_credit", {}).get("score") is not None else float("nan"))
    market = float(dimensions.get("market_pricing", {}).get("score") if dimensions.get("market_pricing", {}).get("score") is not None else float("nan"))
    internals = float(dimensions.get("valuation_internals", {}).get("score") if dimensions.get("valuation_internals", {}).get("score") is not None else float("nan"))

    if market >= 0.25 and liquidity <= -0.2:
        records.append(_contradiction("Risk appetite conflicts with liquidity/credit", "Market-pricing proxies are firm while liquidity/credit proxies are tight or stressed.", {"market_pricing": market, "liquidity_credit": liquidity}))
    if growth >= 0.25 and liquidity <= -0.2:
        records.append(_contradiction("Growth support conflicts with liquidity/credit", "Growth proxies are constructive while financial-condition proxies remain a headwind.", {"growth": growth, "liquidity_credit": liquidity}))
    if market >= 0.25 and rates <= -0.2:
        records.append(_contradiction("Risk appetite conflicts with rates pressure", "Risk appetite is positive while inflation/rates pressure remains hostile.", {"market_pricing": market, "inflation_rates": rates}))
    if growth <= -0.25 and market >= 0.25:
        records.append(_contradiction("Market pricing is stronger than growth evidence", "Market-pricing proxies are positive while growth proxies are deteriorating.", {"growth": growth, "market_pricing": market}))
    if market >= 0.25 and internals <= -0.25:
        records.append(_contradiction("Risk appetite conflicts with valuation/internals", "Broad market-pricing proxies are firm while valuation, volatility, or leadership proxies warn about crowding or weak participation.", {"market_pricing": market, "valuation_internals": internals}))

    for item in subsector_contradictions[:3]:
        records.append(
            {
                "title": f"Subsector contradiction: {item.get('subsector_name', 'unknown')}",
                "summary": str(item.get("summary", "")),
                "components": dict(item.get("components", {})),
                "severity": float(item.get("severity", 0) or 0),
                "scope": "subsector",
            }
        )
    return sorted(records, key=lambda item: float(item.get("severity", 0)), reverse=True)[:8]


def _oslo_read_through(subsectors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in subsectors:
        groups[str(item.get("group_name", "Other"))].append(item)

    records = []
    for group_name, items in sorted(groups.items()):
        items = [item for item in items if item.get("opportunity_score") is not None]
        if not items:
            records.append({"group_name": group_name, "phase": "insufficient evidence", "average_score": None, "momentum": None, "confidence": "very low", "confidence_score": 0, "read_through": "No usable proxy evidence; sector signals are unavailable.", "top_subsectors": []})
            continue
        recovery = _mean([float(item.get("signals", {}).get("recovery_potential", 0) or 0) for item in items])
        momentum = _mean([float(item.get("signals", {}).get("momentum", 0) or 0) for item in items])
        macro = _mean([float(item.get("signals", {}).get("macro_tailwind", 0) or 0) for item in items])
        confidence = _mean([float(item.get("signals", {}).get("confidence", 0) or 0) for item in items])
        score = _mean([float(item.get("opportunity_score", 0) or 0) for item in items])
        phase = "proxy screen — insufficient direct evidence"
        top_items = sorted(items, key=lambda item: int(item.get("rank") or 999))[:3]
        records.append(
            {
                "group_name": group_name,
                "phase": phase,
                "average_score": _rounded(score, 1),
                "recovery_potential": _rounded(recovery, 3),
                "momentum": _rounded(momentum, 3),
                "macro_tailwind": _rounded(macro, 3),
                "confidence": _confidence_label(confidence),
                "confidence_score": _rounded(confidence, 3),
                "read_through": _subsector_read_through_text(group_name, phase, recovery, momentum, macro, confidence),
                "top_subsectors": [
                    {
                        "slug": str(item.get("slug", "")),
                        "name": str(item.get("name", "")),
                        "rank": int(item.get("rank", 0) or 0),
                        "opportunity_score": item.get("opportunity_score"),
                    }
                    for item in top_items
                ],
            }
        )
    return sorted(records, key=lambda item: float(item["average_score"]) if item["average_score"] is not None else -1, reverse=True)


def _cycle_clocks(dimensions: dict[str, dict[str, Any]], subsectors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def clock(clock_id: str, title: str, dimension_ids: tuple[str, ...], interpretation: str) -> dict[str, Any]:
        available = [dimensions[item] for item in dimension_ids if item in dimensions and dimensions[item].get("phase") != "insufficient evidence"]
        score = _mean([float(item.get("score", 0.0)) for item in available])
        direction_score = _mean([float(item.get("direction_score", 0.0)) for item in available])
        return {
            "clock_id": clock_id,
            "title": title,
            "status": _status_label(score, "supportive", "adverse") if available else "insufficient evidence",
            "direction": _direction_label(direction_score) if available else "unclear",
            "score": _rounded(score, 3) if available else None,
            "data_support": _confidence_label(_mean([float(item.get("confidence_score", 0.0)) for item in available])),
            "interpretation": interpretation,
            "source_dimensions": list(dimension_ids),
        }

    operating_supported = sum(1 for item in subsectors if str(item.get("evidence_gate", "")).startswith("direct"))
    clocks = [
        clock("economic", "Economic growth clock", ("growth",), "Leading activity and slow growth background; not a dated recession call."),
        clock("inflation_policy", "Inflation and policy clock", ("inflation_rates",), "Inflation, global central-bank stance and sovereign-rate pressure."),
        clock("financial", "Financial and liquidity clock", ("liquidity_credit",), "Financial conditions, credit spreads, stress and dollar liquidity."),
        clock("market", "Market-price and valuation clock", ("market_pricing", "valuation_internals"), "Global price momentum, volatility, participation and valuation context."),
    ]
    clocks.append(
        {
            "clock_id": "sector_operating",
            "title": "Sector operating-cycle clock",
            "status": "insufficient direct evidence" if operating_supported == 0 else "partial",
            "direction": "unclear",
            "score": None,
            "data_support": "very low" if operating_supported == 0 else "low",
            "interpretation": "Sector phases require direct utilisation, orders, prices/margins, earnings and balance-sheet evidence. Proxy rankings are research queues only.",
            "directly_supported_subsector_count": operating_supported,
            "subsector_count": len(subsectors),
        }
    )
    return clocks


def _transition_evidence(global_equity: dict[str, Any], dimensions: list[dict[str, Any]], contradictions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for dimension in dimensions:
        if dimension["phase"] in {"transition watch", "early recovery candidate", "deterioration/downturn", "late-cycle/crowded risk"}:
            records.append(
                {
                    "title": f"{dimension['title']}: {dimension['phase']}",
                    "summary": f"{dimension['status']} with {dimension['direction']} direction and {dimension['confidence']} confidence.",
                    "score": dimension["score"],
                }
            )
    for contradiction in contradictions[:3]:
        records.append({"title": contradiction["title"], "summary": contradiction["summary"], "score": -float(contradiction.get("severity", 0) or 0)})
    if not records and global_equity["phase"] == "mid-cycle continuation":
        records.append({"title": "No transition signal dominates", "summary": "Most public dimensions are not showing enough pressure to override the continuation read.", "score": global_equity["score"]})
    return records[:8]


def _continuation_evidence(dimensions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for dimension in dimensions:
        if dimension["phase"] in {"mid-cycle continuation", "recovery confirmation"}:
            records.append(
                {
                    "title": f"{dimension['title']}: {dimension['phase']}",
                    "summary": f"{dimension['status']} with {dimension['direction']} direction.",
                    "score": dimension["score"],
                }
            )
    return records[:6]


def _missing_data_caveats(framework_coverage: list[dict[str, Any]], source_freshness: list[dict[str, Any]]) -> list[dict[str, str]]:
    caveats = []
    weak_statuses = {"missing", "limited", "partial", "proxied", "sample_backed"}
    for item in framework_coverage:
        status = str(item.get("status", ""))
        if status in weak_statuses:
            caveats.append(
                {
                    "dimension": str(item.get("dimension", "")),
                    "status": status,
                    "caveat": str(item.get("main_gap", "")),
                }
            )
    fallback = [str(item.get("display_slug") or item.get("indicator_slug")) for item in source_freshness if item.get("has_sample_fallback")]
    if fallback:
        caveats.append({"dimension": "Numeric data", "status": "sample_fallback", "caveat": f"Numeric sample fallback is present for: {', '.join(fallback)}."})
    return caveats[:8]


def _overall_confidence(global_equity: dict[str, Any], dimensions: list[dict[str, Any]], caveats: list[dict[str, str]]) -> dict[str, Any]:
    score = float(global_equity.get("confidence_score", 0) or 0)
    score -= min(0.18, len(caveats) * 0.015)
    score = max(0.0, score)
    low_dimensions = [item["title"] for item in dimensions if item["confidence"] in {"low", "very low"}]
    return {
        "label": _confidence_label(score),
        "score": _rounded(score, 3),
        "confidence_type": "data_support_not_empirical_accuracy",
        "low_confidence_dimensions": low_dimensions,
        "summary": _confidence_summary(score, low_dimensions, caveats),
    }


def _phase_label(score: float, direction_score: float, coverage_ratio: float, confidence_score: float) -> str:
    if coverage_ratio < 0.34 or confidence_score < 0.2:
        return "insufficient evidence"
    if score <= -0.3 and direction_score <= -0.05:
        return "deterioration/downturn"
    if score >= 0.35 and direction_score >= 0.12:
        return "recovery confirmation"
    if score >= 0.28:
        return "mid-cycle continuation"
    if score >= -0.05 and direction_score >= 0.15:
        return "early recovery candidate"
    if abs(score) <= 0.22 or abs(direction_score) >= 0.18:
        return "transition watch"
    if score <= -0.22:
        return "deterioration/downturn"
    return "transition watch"


def _status_label(score: float, positive_label: str, negative_label: str) -> str:
    if score >= 0.25:
        return positive_label
    if score <= -0.25:
        return negative_label
    return "mixed/neutral"


def _direction_label(direction_score: float) -> str:
    if direction_score >= 0.15:
        return "improving"
    if direction_score <= -0.15:
        return "deteriorating"
    return "stable/mixed"


def _confidence_score(coverage_ratio: float, live_count: int, evidence_count: int, fallback_count: int, stale_count: int) -> float:
    if evidence_count <= 0:
        return 0.0
    usable_ratio = max(0, live_count - fallback_count - stale_count) / evidence_count
    return _clip01(coverage_ratio * usable_ratio)


def _confidence_label(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.55:
        return "medium"
    if score >= 0.3:
        return "low"
    return "very low"


def classify_subsector_phase(
    recovery: float,
    momentum: float,
    macro: float,
    score: float,
    confidence: float,
    direct_evidence: bool = False,
) -> str:
    if not direct_evidence:
        return "proxy screen — insufficient direct evidence"
    if confidence < 0.35:
        return "insufficient evidence"
    if momentum >= 0.25 and recovery < 0.05 and score >= 58:
        return "late-cycle/crowded risk"
    if recovery >= 0.2 and momentum >= 0.05:
        return "recovery confirmation"
    if recovery >= 0.16 or (momentum >= 0.12 and macro >= -0.05):
        return "early recovery candidate"
    if macro <= -0.2 or momentum <= -0.2:
        return "deterioration/downturn"
    if score >= 56:
        return "mid-cycle continuation"
    return "transition watch"


def _subsector_read_through_text(group_name: str, phase: str, recovery: float, momentum: float, macro: float, confidence: float) -> str:
    return (
        f"{group_name} screens as {phase}; recovery {recovery:+.2f}, momentum {momentum:+.2f}, "
        f"macro tailwind {macro:+.2f}, confidence {_confidence_label(confidence)}."
    )


def _global_status(phase: str) -> str:
    if phase in {"recovery confirmation", "mid-cycle continuation"}:
        return "continuation/recovery"
    if phase == "early recovery candidate":
        return "recovery watch"
    if phase == "late-cycle/crowded risk":
        return "exit-risk watch"
    if phase == "deterioration/downturn":
        return "deterioration"
    if phase == "insufficient evidence":
        return "insufficient evidence"
    return "transition watch"


def _global_summary(phase: str, score: float, direction: str, contradictions: list[dict[str, Any]]) -> str:
    contradiction_note = " Contradictions are material and should temper the read." if contradictions else ""
    return f"Heuristic global market-risk regime is {phase} with a composite score of {score:+.2f} and {direction} direction.{contradiction_note}"


def _confidence_summary(score: float, low_dimensions: list[str], caveats: list[dict[str, str]]) -> str:
    parts = [f"Overall data support is {_confidence_label(score)}; this is not empirical forecast confidence."]
    if low_dimensions:
        parts.append(f"Lower-confidence dimensions: {', '.join(low_dimensions[:4])}.")
    if caveats:
        parts.append("Missing/proxied dimensions remain visible caveats, especially true Oslo valuation multiples, earnings, positioning, and true subsector histories.")
    return " ".join(parts)


def _contradiction(title: str, summary: str, components: dict[str, float]) -> dict[str, Any]:
    severity = _mean([abs(value) for value in components.values()])
    return {
        "title": title,
        "summary": summary,
        "components": {key: _rounded(value, 3) for key, value in components.items()},
        "severity": _rounded(severity, 3),
        "scope": "cycle",
    }


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _clip(value: float) -> float:
    return max(min(value, 1.0), -1.0)


def _clip01(value: float) -> float:
    return max(min(value, 1.0), 0.0)


def _rounded(value: object, digits: int) -> float:
    return round(float(value), digits)
