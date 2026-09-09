from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from .indicators import indicator_by_slug
from .signal_metrics import build_indicator_metrics
from .taxonomy import SUBSECTORS
from .source_health import observation_health


def calculate_scores(observations: pd.DataFrame, research_mentions: pd.DataFrame | None = None, *, as_of=None, sample: bool = False) -> pd.DataFrame:
    """Build a research-priority heuristic, never an expected-return score.

    Unreviewed narrative is deliberately ignored.  Correlated indicators first
    collapse to one observation per economic family, so adding countries or
    aliases cannot silently increase a family's weight.
    """

    raw_metrics = build_indicator_metrics(observations)
    health = observation_health(observations, as_of=as_of, sample=sample, supported_slugs=set(raw_metrics))
    eligible = {r["indicator_slug"] for r in health if r["scoring_eligible"] or (sample and r["source_category"] == "deterministic_sample" and r["history_supported"] and not r["future_dated_observation"])}
    metrics = {slug: value for slug, value in raw_metrics.items() if slug in eligible}
    rows: list[dict[str, object]] = []
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    for subsector in SUBSECTORS:
        available = [metrics[slug] for slug in subsector.proxy_indicators if slug in metrics]
        family_metrics = _family_metrics(available)
        expected_families = {
            indicator_by_slug()[slug].family
            for slug in subsector.proxy_indicators
            if slug in indicator_by_slug()
        }
        coverage = len(family_metrics) / max(len(expected_families), 1)
        data_support = min(0.45, coverage * min(1.0, len(family_metrics) / 3.0) * 0.55)

        if not family_metrics:
            cycle_pressure = reversal_watch = cycle_position = momentum = macro_tailwind = 0.0
        else:
            percentile_values = [float(item["percentile"]) for item in family_metrics]
            tailwinds = [float(item["tailwind_score"]) for item in family_metrics]
            economic_momenta = [float(item["economic_momentum"]) for item in family_metrics]
            macro_tailwind = _clip(_mean(tailwinds))
            momentum = _clip(_mean(economic_momenta))
            cycle_pressure = _clip(_mean(percentile_values) * 2.0 - 1.0)
            cycle_position = _clip(-cycle_pressure)
            reversal_watch = _clip(max(-macro_tailwind, 0.0) * 0.65 + max(momentum, 0.0) * 0.35)

        research_priority = _clip_100(
            50.0
            + reversal_watch * 18.0
            + abs(cycle_pressure) * 8.0
            + max(momentum, 0.0) * 8.0
            - max(macro_tailwind, 0.0) * 4.0
        )

        if not family_metrics:
            research_priority = cycle_pressure = reversal_watch = cycle_position = momentum = macro_tailwind = None

        rows.append(
            {
                "slug": subsector.slug,
                "name": subsector.name,
                "group_name": subsector.group,
                # Backward-compatible aliases remain until consumers migrate.
                "opportunity_score": round(research_priority, 1) if research_priority is not None else None,
                "research_priority_score": round(research_priority, 1) if research_priority is not None else None,
                "cycle_pressure": round(cycle_pressure, 3) if cycle_pressure is not None else None,
                "recovery_potential": round(reversal_watch, 3) if reversal_watch is not None else None,
                "reversal_watch": round(reversal_watch, 3) if reversal_watch is not None else None,
                "valuation_proxy": round(cycle_position, 3) if cycle_position is not None else None,
                "cycle_position_score": round(cycle_position, 3) if cycle_position is not None else None,
                "momentum": round(momentum, 3) if momentum is not None else None,
                "macro_tailwind": round(macro_tailwind, 3) if macro_tailwind is not None else None,
                "narrative_divergence": 0.0,
                "confidence": round(data_support, 3),
                "data_support": round(data_support, 3),
                "data_confidence": "proxy_only",
                "score_status": "usable" if family_metrics else "unavailable",
                "included_indicator_count": len(available),
                "expected_indicator_count": len(subsector.proxy_indicators),
                "excluded_indicators": ", ".join(slug for slug in subsector.proxy_indicators if slug not in metrics),
                "evidence_gate": "insufficient_direct_sector_evidence",
                "explanation": _explain(subsector.proxy_indicators, metrics, subsector.thesis_prompt),
                "refreshed_at": now,
            }
        )

    return pd.DataFrame(rows).sort_values("research_priority_score", ascending=False).reset_index(drop=True)


def _family_metrics(items: list[dict[str, float | int | str]]) -> list[dict[str, float]]:
    grouped: dict[str, list[dict[str, float | int | str]]] = {}
    for item in items:
        grouped.setdefault(str(item.get("family", "other")), []).append(item)
    records = []
    for family, family_items in grouped.items():
        records.append(
            {
                "family": family,
                "percentile": _mean([float(item["percentile"]) for item in family_items]),
                "tailwind_score": _mean([float(item["tailwind_score"]) for item in family_items]),
                "economic_momentum": _mean([float(item.get("economic_momentum", 0.0)) for item in family_items]),
            }
        )
    return records


def _explain(proxy_indicators: tuple[str, ...], metrics: dict[str, dict[str, float | int | str]], thesis: str) -> str:
    definitions = indicator_by_slug()
    parts = []
    for slug in proxy_indicators[:5]:
        metric = metrics.get(slug)
        if not metric:
            continue
        label = definitions[slug].name if slug in definitions else slug
        parts.append(
            f"{label}: {metric.get('transform', 'level')} percentile {float(metric['percentile']):.0%}, "
            f"economic momentum {float(metric.get('economic_momentum', 0)):+.2f}"
        )
    evidence = ", ".join(parts) if parts else "insufficient validated proxy history"
    return f"{thesis} Proxy evidence: {evidence}. Reviewed outlooks are non-scoring."


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _clip(value: float) -> float:
    return max(min(float(value), 1.0), -1.0)


def _clip_100(value: float) -> float:
    return max(min(float(value), 100.0), 0.0)
