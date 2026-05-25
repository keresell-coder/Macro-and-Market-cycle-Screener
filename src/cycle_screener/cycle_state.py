from __future__ import annotations

from collections import defaultdict
from typing import Any

import pandas as pd

from .indicators import indicator_by_slug, public_indicator_slug


CYCLE_STATE_VERSION = "cycle-state-v1-sprint11"

GROWTH_INDICATORS = ("g20_cli", "g7_cli", "us_cli", "china_cli", "europe_cli", "global_pmi", "china_growth_proxy")
INFLATION_RATES_INDICATORS = ("norway_cpi", "rates_pressure", "norges_bank_policy_rate", "brent", "us_natural_gas")
LIQUIDITY_CREDIT_INDICATORS = ("chicago_fed_nfci", "st_louis_financial_stress")
MARKET_PRICING_INDICATORS = ("nasdaq_proxy", "copper", "aluminum", "oil_curve_pressure")


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
            "OECD CLI and annual GDP-growth proxies.",
            GROWTH_INDICATORS,
            metrics,
            freshness_lookup,
            positive_label="growth support",
            negative_label="growth deterioration",
        ),
        _dimension(
            "inflation_rates",
            "Inflation and rates pressure",
            "Inflation, policy-rate, market-rate, and commodity-pressure proxies. Positive scores mean pressure is less hostile.",
            INFLATION_RATES_INDICATORS,
            metrics,
            freshness_lookup,
            positive_label="pressure easing",
            negative_label="pressure tightening",
        ),
        _dimension(
            "liquidity_credit",
            "Liquidity and credit",
            "Chicago Fed NFCI and St. Louis Fed financial-stress proxies. Positive scores mean easier conditions.",
            LIQUIDITY_CREDIT_INDICATORS,
            metrics,
            freshness_lookup,
            positive_label="liquidity tailwind",
            negative_label="credit/liquidity headwind",
        ),
        _dimension(
            "market_pricing",
            "Market pricing and risk appetite",
            "Broad market, technology, commodity, and oil-curve proxies. This is not a breadth or positioning model.",
            MARKET_PRICING_INDICATORS,
            metrics,
            freshness_lookup,
            positive_label="risk appetite supportive",
            negative_label="risk appetite fading",
            use_risk_appetite=True,
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
        "transition_evidence": _transition_evidence(global_equity, dimensions, cycle_contradictions),
        "continuation_evidence": _continuation_evidence(dimensions),
        "contradictions": cycle_contradictions,
        "confidence": _overall_confidence(global_equity, dimensions, missing_caveats),
        "missing_data_caveats": missing_caveats,
        "methodology_note": (
            "Sprint 11 synthesis uses existing public indicators, source freshness, liquidity/credit signal groups, "
            "subsector proxy scores, and contradiction evidence. It is a rule-based cycle read, not a forecast or investment advice."
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
    scores: list[float] = []
    momentum_values: list[float] = []
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
        scores.append(score)
        momentum_values.append(float(metric["momentum"]))
        source_category = str(freshness.get("source_category", "missing"))
        freshness_status = str(freshness.get("freshness_status", "missing"))
        if source_category == "live_numeric":
            live_count += 1
        if source_category in {"numeric_sample_fallback", "deterministic_sample"} or freshness.get("has_sample_fallback"):
            fallback_count += 1
        if freshness_status in {"stale", "very_stale"}:
            stale_count += 1
        definition = definitions.get(slug)
        evidence.append(
            {
                "indicator_slug": slug,
                "display_slug": public_indicator_slug(slug),
                "indicator_name": definition.name if definition else slug,
                "latest_value": _rounded(metric["latest"], 4),
                "percentile": _rounded(metric["percentile"], 3),
                "momentum": _rounded(metric["momentum"], 3),
                "score": _rounded(score, 3),
                "latest_observed_at": str(freshness.get("latest_observed_at", "")),
                "source_category": source_category,
                "freshness_status": freshness_status,
            }
        )

    coverage_ratio = len(evidence) / max(len(slugs), 1)
    score = _mean(scores)
    direction_score = _mean(momentum_values)
    direction = _direction_label(direction_score)
    status = _status_label(score, positive_label, negative_label)
    confidence_score = _confidence_score(coverage_ratio, live_count, len(evidence), fallback_count, stale_count)
    phase = _phase_label(score, direction_score, coverage_ratio, confidence_score)

    return {
        "dimension_id": dimension_id,
        "title": title,
        "description": description,
        "phase": phase,
        "status": status,
        "direction": direction,
        "score": _rounded(score, 3),
        "direction_score": _rounded(direction_score, 3),
        "confidence": _confidence_label(confidence_score),
        "confidence_score": _rounded(confidence_score, 3),
        "coverage": {
            "available_count": len(evidence),
            "expected_count": len(slugs),
            "coverage_ratio": _rounded(coverage_ratio, 3),
            "live_count": live_count,
            "fallback_or_sample_count": fallback_count,
            "stale_count": stale_count,
        },
        "evidence": sorted(evidence, key=lambda item: abs(float(item["score"])), reverse=True)[:6],
        "missing_indicators": [slug for slug in slugs if slug not in metrics],
    }


def _indicator_metrics(observations: pd.DataFrame) -> dict[str, dict[str, float]]:
    if observations.empty:
        return {}
    definitions = indicator_by_slug()
    frame = observations.copy()
    frame["observed_at_sort"] = pd.to_datetime(frame["observed_at"], errors="coerce")
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame.dropna(subset=["indicator_slug", "observed_at_sort", "value"]).sort_values(["indicator_slug", "observed_at_sort"])

    result: dict[str, dict[str, float]] = {}
    for slug, group in frame.groupby("indicator_slug"):
        values = group["value"].astype(float).tail(120)
        if values.empty:
            continue
        latest = float(values.iloc[-1])
        percentile = float((values <= latest).mean())
        if len(values) >= 7:
            recent = float(values.tail(3).mean())
            prior = float(values.iloc[-6:-3].mean())
            denominator = abs(prior) if abs(prior) > 1e-9 else 1.0
            momentum = _clip(((recent - prior) / denominator) * 8)
        else:
            momentum = 0.0
        definition = definitions.get(str(slug))
        higher_is = definition.higher_is if definition else "mixed"
        result[str(slug)] = {
            "latest": latest,
            "percentile": percentile,
            "momentum": momentum,
            "tailwind_score": _tailwind_score(percentile, momentum, higher_is),
        }
    return result


def _tailwind_score(percentile: float, momentum: float, higher_is: str) -> float:
    if higher_is == "higher_tailwind":
        return _clip((percentile - 0.5) * 1.4 + momentum * 0.6)
    if higher_is == "lower_tailwind":
        return _clip((0.5 - percentile) * 1.4 - momentum * 0.6)
    return _clip((0.5 - abs(percentile - 0.5)) * 0.6 + momentum * 0.4)


def _risk_appetite_score(metric: dict[str, float]) -> float:
    return _clip((float(metric["percentile"]) - 0.5) * 1.25 + float(metric["momentum"]) * 0.55)


def _global_equity_cycle(dimensions: dict[str, dict[str, Any]], contradictions: list[dict[str, Any]]) -> dict[str, Any]:
    weights = {
        "growth": 0.3,
        "inflation_rates": 0.2,
        "liquidity_credit": 0.25,
        "market_pricing": 0.25,
    }
    available = [key for key in weights if dimensions.get(key, {}).get("phase") != "insufficient evidence"]
    if len(available) < 3:
        return {
            "phase": "insufficient evidence",
            "status": "insufficient evidence",
            "direction": "unclear",
            "score": 0.0,
            "confidence": "low",
            "confidence_score": 0.0,
            "summary": "Not enough public indicator coverage is available to classify the global equity cycle.",
            "primary_evidence": [],
        }

    weighted_score = sum(float(dimensions[key]["score"]) * weights[key] for key in available) / sum(weights[key] for key in available)
    direction_score = _mean([float(dimensions[key]["direction_score"]) for key in available])
    growth = float(dimensions["growth"]["score"])
    rates = float(dimensions["inflation_rates"]["score"])
    liquidity = float(dimensions["liquidity_credit"]["score"])
    market = float(dimensions["market_pricing"]["score"])

    if market >= 0.25 and (rates <= -0.2 or liquidity <= -0.2) and growth >= -0.1:
        phase = "late-cycle/crowded risk"
    elif weighted_score <= -0.25 or (growth <= -0.25 and liquidity <= -0.15):
        phase = "deterioration/downturn"
    elif contradictions and abs(weighted_score) < 0.35:
        phase = "transition watch"
    elif weighted_score >= 0.28 and direction_score >= 0.12:
        phase = "recovery confirmation"
    elif weighted_score >= 0.18:
        phase = "mid-cycle continuation"
    elif weighted_score >= -0.05 and direction_score >= 0.15:
        phase = "early recovery candidate"
    elif abs(weighted_score) < 0.18:
        phase = "transition watch"
    else:
        phase = "deterioration/downturn"

    confidence_score = _mean([float(dimensions[key]["confidence_score"]) for key in available])
    confidence_score -= min(0.2, len(contradictions) * 0.04)
    confidence_score = max(0.0, confidence_score)
    status = _global_status(phase)
    direction = _direction_label(direction_score)

    return {
        "phase": phase,
        "status": status,
        "direction": direction,
        "score": _rounded(weighted_score, 3),
        "confidence": _confidence_label(confidence_score),
        "confidence_score": _rounded(confidence_score, 3),
        "summary": _global_summary(phase, weighted_score, direction, contradictions),
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


def _cycle_contradictions(dimensions: dict[str, dict[str, Any]], subsector_contradictions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    growth = float(dimensions.get("growth", {}).get("score", 0))
    rates = float(dimensions.get("inflation_rates", {}).get("score", 0))
    liquidity = float(dimensions.get("liquidity_credit", {}).get("score", 0))
    market = float(dimensions.get("market_pricing", {}).get("score", 0))

    if market >= 0.25 and liquidity <= -0.2:
        records.append(_contradiction("Risk appetite conflicts with liquidity/credit", "Market-pricing proxies are firm while liquidity/credit proxies are tight or stressed.", {"market_pricing": market, "liquidity_credit": liquidity}))
    if growth >= 0.25 and liquidity <= -0.2:
        records.append(_contradiction("Growth support conflicts with liquidity/credit", "Growth proxies are constructive while financial-condition proxies remain a headwind.", {"growth": growth, "liquidity_credit": liquidity}))
    if market >= 0.25 and rates <= -0.2:
        records.append(_contradiction("Risk appetite conflicts with rates pressure", "Risk appetite is positive while inflation/rates pressure remains hostile.", {"market_pricing": market, "inflation_rates": rates}))
    if growth <= -0.25 and market >= 0.25:
        records.append(_contradiction("Market pricing is stronger than growth evidence", "Market-pricing proxies are positive while growth proxies are deteriorating.", {"growth": growth, "market_pricing": market}))

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
        recovery = _mean([float(item.get("signals", {}).get("recovery_potential", 0) or 0) for item in items])
        momentum = _mean([float(item.get("signals", {}).get("momentum", 0) or 0) for item in items])
        macro = _mean([float(item.get("signals", {}).get("macro_tailwind", 0) or 0) for item in items])
        confidence = _mean([float(item.get("signals", {}).get("confidence", 0) or 0) for item in items])
        score = _mean([float(item.get("opportunity_score", 0) or 0) for item in items])
        phase = _subsector_phase(recovery, momentum, macro, score, confidence)
        top_items = sorted(items, key=lambda item: int(item.get("rank", 999)))[:3]
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
    return sorted(records, key=lambda item: float(item["average_score"]), reverse=True)


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
    weak_statuses = {"missing", "limited", "proxied", "sample_backed"}
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
    live_ratio = live_count / evidence_count
    fallback_penalty = min(0.3, fallback_count * 0.12)
    stale_penalty = min(0.25, stale_count * 0.08)
    return _clip01(coverage_ratio * 0.55 + live_ratio * 0.45 - fallback_penalty - stale_penalty)


def _confidence_label(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.55:
        return "medium"
    if score >= 0.3:
        return "low"
    return "very low"


def _subsector_phase(recovery: float, momentum: float, macro: float, score: float, confidence: float) -> str:
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
    return f"Global equity cycle synthesis is {phase} with a composite score of {score:+.2f} and {direction} direction.{contradiction_note}"


def _confidence_summary(score: float, low_dimensions: list[str], caveats: list[dict[str, str]]) -> str:
    parts = [f"Overall synthesis confidence is {_confidence_label(score)}."]
    if low_dimensions:
        parts.append(f"Lower-confidence dimensions: {', '.join(low_dimensions[:4])}.")
    if caveats:
        parts.append("Missing/proxied dimensions remain visible caveats, especially valuation, market internals, earnings, and true Oslo subsector histories.")
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
