from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from .indicators import indicator_by_slug
from .taxonomy import SUBSECTORS


CONFIDENCE_VALUE = {"high": 0.9, "medium": 0.7, "low": 0.5}


def calculate_scores(observations: pd.DataFrame, research_mentions: pd.DataFrame) -> pd.DataFrame:
    metrics = _indicator_metrics(observations)
    narrative = _narrative_by_theme(research_mentions)
    rows: list[dict[str, object]] = []
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    for subsector in SUBSECTORS:
        indicator_metrics = [metrics.get(slug) for slug in subsector.proxy_indicators if slug in metrics]
        indicator_metrics = [item for item in indicator_metrics if item is not None]
        confidence = CONFIDENCE_VALUE[subsector.data_confidence] * min(1.0, len(indicator_metrics) / max(len(subsector.proxy_indicators), 1))

        if not indicator_metrics:
            cycle_pressure = recovery_potential = valuation_proxy = momentum = macro_tailwind = 0.0
        else:
            pressure_values = [_tailwind_adjusted_metric(item) for item in indicator_metrics]
            momentum_values = [item["momentum"] for item in indicator_metrics]
            percentile_values = [item["percentile"] for item in indicator_metrics]
            cycle_pressure = _clip(_mean(percentile_values) * 2 - 1)
            momentum = _clip(_mean(momentum_values))
            macro_tailwind = _clip(_mean(pressure_values))
            valuation_proxy = _clip(1 - abs(_mean(percentile_values) - 0.35) * 2.2)
            recovery_potential = _clip((0.45 - _mean(percentile_values)) * 1.35 + max(momentum, 0) * 0.65)

        narrative_score = _narrative_score(subsector, narrative)
        narrative_divergence = _clip(max(recovery_potential, 0) - max(narrative_score, 0) * 0.45)
        opportunity_score = _clip_100(
            50
            + recovery_potential * 24
            + valuation_proxy * 12
            + momentum * 10
            + macro_tailwind * 10
            + narrative_divergence * 8
            - max(cycle_pressure, 0) * 8
        )

        rows.append(
            {
                "slug": subsector.slug,
                "name": subsector.name,
                "group_name": subsector.group,
                "opportunity_score": round(opportunity_score, 1),
                "cycle_pressure": round(cycle_pressure, 3),
                "recovery_potential": round(recovery_potential, 3),
                "valuation_proxy": round(valuation_proxy, 3),
                "momentum": round(momentum, 3),
                "macro_tailwind": round(macro_tailwind, 3),
                "narrative_divergence": round(narrative_divergence, 3),
                "confidence": round(confidence, 3),
                "data_confidence": subsector.data_confidence,
                "explanation": _explain(subsector.proxy_indicators, metrics, narrative_score, subsector.thesis_prompt),
                "refreshed_at": now,
            }
        )

    return pd.DataFrame(rows).sort_values("opportunity_score", ascending=False).reset_index(drop=True)


def _indicator_metrics(observations: pd.DataFrame) -> dict[str, dict[str, float | str]]:
    definitions = indicator_by_slug()
    metrics: dict[str, dict[str, float | str]] = {}
    if observations.empty:
        return metrics

    frame = observations.copy()
    frame["observed_at"] = pd.to_datetime(frame["observed_at"], errors="coerce")
    frame = frame.dropna(subset=["observed_at", "value"]).sort_values(["indicator_slug", "observed_at"])
    for slug, group in frame.groupby("indicator_slug"):
        values = group["value"].astype(float).tail(60)
        if values.empty:
            continue
        latest = float(values.iloc[-1])
        percentile = float((values <= latest).mean())
        if len(values) >= 7:
            recent = float(values.tail(3).mean())
            prior = float(values.iloc[-6:-3].mean())
            denominator = abs(prior) if abs(prior) > 1e-9 else 1.0
            momentum = (recent - prior) / denominator
        else:
            momentum = 0.0
        definition = definitions.get(slug)
        metrics[slug] = {
            "latest": latest,
            "percentile": percentile,
            "momentum": _clip(momentum * 8),
            "higher_is": definition.higher_is if definition else "mixed",
        }
    return metrics


def _tailwind_adjusted_metric(item: dict[str, float | str]) -> float:
    percentile = float(item["percentile"])
    momentum = float(item["momentum"])
    higher_is = str(item["higher_is"])
    if higher_is == "higher_tailwind":
        return _clip((percentile - 0.5) * 1.4 + momentum * 0.6)
    if higher_is == "lower_tailwind":
        return _clip((0.5 - percentile) * 1.4 - momentum * 0.6)
    return _clip((0.5 - abs(percentile - 0.5)) * 0.6 + momentum * 0.4)


def _narrative_by_theme(research_mentions: pd.DataFrame) -> dict[str, float]:
    if research_mentions.empty or "theme" not in research_mentions:
        return {}
    return research_mentions.groupby("theme")["sentiment"].mean().astype(float).to_dict()


def _narrative_score(subsector, narrative: dict[str, float]) -> float:
    score = 0.0
    matched = 0
    text = " ".join((*subsector.drivers, *subsector.macro_sensitivities)).lower()
    for theme, sentiment in narrative.items():
        if theme in text or (theme == "rates" and "rate" in text) or (theme == "growth" and "global" in text):
            score += sentiment
            matched += 1
    return _clip(score / matched) if matched else 0.0


def _explain(proxy_indicators: tuple[str, ...], metrics: dict[str, dict[str, float | str]], narrative_score: float, thesis: str) -> str:
    parts = []
    for slug in proxy_indicators[:4]:
        metric = metrics.get(slug)
        if not metric:
            continue
        parts.append(f"{slug}: pctile {float(metric['percentile']):.0%}, momentum {float(metric['momentum']):+.2f}")
    narrative = f"narrative {narrative_score:+.2f}"
    return f"{thesis} Evidence: {', '.join(parts) if parts else 'limited indicator coverage'}; {narrative}."


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _clip(value: float) -> float:
    return max(min(value, 1.0), -1.0)


def _clip_100(value: float) -> float:
    return max(min(value, 100.0), 0.0)

