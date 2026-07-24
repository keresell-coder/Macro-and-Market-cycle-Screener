from __future__ import annotations

from typing import Iterable

import pandas as pd

from .indicators import indicator_by_slug


LOOKBACK_YEARS = 10


def build_indicator_metrics(
    observations: pd.DataFrame,
    slugs: Iterable[str] | None = None,
) -> dict[str, dict[str, float | int | str]]:
    """Build comparable signal metrics using time-aware horizons.

    Daily and weekly observations are reduced to month-end observations before
    percentiles and momentum are calculated. Monthly, quarterly, and annual
    series use horizons suited to their release frequency. Annual GDP data is
    deliberately damped because it is structural background rather than a
    short-cycle trigger.
    """

    if observations.empty:
        return {}

    frame = observations.copy()
    frame["observed_at_sort"] = pd.to_datetime(frame["observed_at"], errors="coerce")
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame.dropna(subset=["indicator_slug", "observed_at_sort", "value"]).sort_values(
        ["indicator_slug", "observed_at_sort"]
    )
    if slugs is not None:
        allowed = {str(slug) for slug in slugs}
        frame = frame[frame["indicator_slug"].astype(str).isin(allowed)]

    definitions = indicator_by_slug()
    result: dict[str, dict[str, float | int | str]] = {}
    for slug, group in frame.groupby("indicator_slug"):
        ordered = group[["observed_at_sort", "value"]].drop_duplicates(
            "observed_at_sort", keep="last"
        )
        frequency = _frequency_bucket(ordered["observed_at_sort"])
        normalized = _normalize_frequency(ordered, frequency)
        if normalized.empty:
            continue

        latest_date = normalized.index.max()
        lookback_start = latest_date - pd.DateOffset(years=LOOKBACK_YEARS)
        window = normalized[normalized.index >= lookback_start]
        minimum = _minimum_percentile_observations(frequency)
        if len(window) < minimum:
            window = normalized.tail(max(minimum, 120))

        values = window.astype(float)
        latest = float(values.iloc[-1])
        percentile = float((values <= latest).mean())
        recent_count, damping, momentum_horizon = _momentum_policy(frequency)
        if len(values) >= recent_count * 2:
            recent = float(values.tail(recent_count).mean())
            prior = float(values.iloc[-recent_count * 2 : -recent_count].mean())
            denominator = abs(prior) if abs(prior) > 1e-9 else 1.0
            momentum = _clip(((recent - prior) / denominator) * 8 * damping)
        else:
            momentum = 0.0

        definition = definitions.get(str(slug))
        higher_is = definition.higher_is if definition else "mixed"
        result[str(slug)] = {
            "latest": latest,
            "percentile": percentile,
            "momentum": momentum,
            "tailwind_score": tailwind_score(percentile, momentum, higher_is),
            "higher_is": higher_is,
            "frequency_bucket": frequency,
            "momentum_horizon": momentum_horizon,
            "observation_count_used": int(len(values)),
            "lookback_years": LOOKBACK_YEARS,
        }
    return result


def tailwind_score(percentile: float, momentum: float, higher_is: str) -> float:
    if higher_is == "higher_tailwind":
        return _clip((percentile - 0.5) * 1.4 + momentum * 0.6)
    if higher_is == "lower_tailwind":
        return _clip((0.5 - percentile) * 1.4 - momentum * 0.6)
    return _clip((0.5 - abs(percentile - 0.5)) * 0.6 + momentum * 0.4)


def _frequency_bucket(dates: pd.Series) -> str:
    ordered = dates.dropna().drop_duplicates().sort_values()
    if len(ordered) < 2:
        return "unknown"
    median_days = float(ordered.diff().dropna().dt.total_seconds().median() / 86400)
    if median_days <= 14:
        return "daily_or_weekly"
    if median_days <= 60:
        return "monthly"
    if median_days <= 150:
        return "quarterly"
    return "annual"


def _normalize_frequency(frame: pd.DataFrame, frequency: str) -> pd.Series:
    series = frame.set_index("observed_at_sort")["value"].astype(float).sort_index()
    if frequency == "daily_or_weekly":
        return series.resample("ME").last().dropna()
    return series


def _minimum_percentile_observations(frequency: str) -> int:
    if frequency == "annual":
        return 8
    if frequency == "quarterly":
        return 16
    return 36


def _momentum_policy(frequency: str) -> tuple[int, float, str]:
    if frequency == "annual":
        return (2, 0.35, "two-year average versus prior two years; damped structural context")
    if frequency == "quarterly":
        return (2, 0.75, "two-quarter average versus prior two quarters")
    return (3, 1.0, "three-month average versus prior three months")


def _clip(value: float) -> float:
    return max(min(value, 1.0), -1.0)
