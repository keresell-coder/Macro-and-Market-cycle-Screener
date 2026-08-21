from __future__ import annotations

from typing import Iterable

import pandas as pd

from .indicators import IndicatorDefinition, indicator_by_slug


LOOKBACK_YEARS = 10


def build_indicator_metrics(
    observations: pd.DataFrame,
    slugs: Iterable[str] | None = None,
) -> dict[str, dict[str, float | int | str]]:
    """Create comparable, economically signed metrics from explicit contracts.

    Market prices are scored on returns, CPI indices on twelve-month inflation,
    CLI data on distance from trend, and zero-centred indices on their native
    standard-deviation scale.  Momentum is a difference in rolling means divided
    by historical standard deviation; it is never a percentage change of a
    zero-centred index.
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
        definition = definitions.get(str(slug))
        ordered = group[["observed_at_sort", "value"]].drop_duplicates("observed_at_sort", keep="last")
        frequency = _frequency_bucket(ordered["observed_at_sort"])
        normalized = _normalize_frequency(ordered, frequency)
        if normalized.empty:
            continue

        raw_latest = float(normalized.iloc[-1])
        transformed = _transform_series(normalized, definition)
        if transformed.empty:
            continue
        latest_date = transformed.index.max()
        lookback_start = latest_date - pd.DateOffset(years=LOOKBACK_YEARS)
        window = transformed[transformed.index >= lookback_start]
        minimum = _minimum_percentile_observations(frequency)
        if len(window) < minimum:
            window = transformed
        if len(window) < minimum:
            continue

        values = window.astype(float).dropna()
        latest = float(values.iloc[-1])
        percentile = float((values <= latest).mean())
        recent_count, damping, momentum_horizon = _momentum_policy(frequency)
        momentum = _standardized_momentum(values, recent_count, damping)

        higher_is = definition.higher_is if definition else "mixed"
        economic_momentum = polarity_adjusted_momentum(momentum, higher_is)
        result[str(slug)] = {
            "raw_latest": raw_latest,
            "latest": latest,
            "percentile": percentile,
            "momentum": momentum,
            "economic_momentum": economic_momentum,
            "tailwind_score": tailwind_score(percentile, momentum, higher_is),
            "higher_is": higher_is,
            "transform": definition.transform if definition else "level",
            "family": definition.family if definition else "other",
            "scoring_role": definition.scoring_role if definition else "scoring",
            "frequency_bucket": frequency,
            "momentum_horizon": momentum_horizon,
            "observation_count_used": int(len(values)),
            "lookback_years": LOOKBACK_YEARS,
        }
    return result


def tailwind_score(percentile: float, momentum: float, higher_is: str) -> float:
    if higher_is == "higher_tailwind":
        return _clip((percentile - 0.5) * 1.2 + momentum * 0.5)
    if higher_is == "lower_tailwind":
        return _clip((0.5 - percentile) * 1.2 - momentum * 0.5)
    # Ambiguous variables have no automatic positive baseline.  Extremes are a
    # modest risk flag and direction is left to a documented sector mapping.
    return _clip(-abs(percentile - 0.5) * 0.5)


def polarity_adjusted_momentum(momentum: float, higher_is: str) -> float:
    if higher_is == "higher_tailwind":
        return _clip(momentum)
    if higher_is == "lower_tailwind":
        return _clip(-momentum)
    return 0.0


def _transform_series(series: pd.Series, definition: IndicatorDefinition | None) -> pd.Series:
    transform = definition.transform if definition else "level"
    clean = series.astype(float).sort_index()
    if transform == "level" or transform == "standardized_index":
        return clean.dropna()
    if transform == "gap_from_100":
        return (clean - 100.0).dropna()
    if transform == "yoy_pct":
        return (clean.pct_change(12, fill_method=None) * 100.0).replace([float("inf"), float("-inf")], pd.NA).dropna()
    if transform == "yoy_return":
        return clean.pct_change(12, fill_method=None).replace([float("inf"), float("-inf")], pd.NA).dropna()
    if transform == "yoy_change":
        return clean.diff(12).dropna()
    raise ValueError(f"Unsupported indicator transform: {transform}")


def _standardized_momentum(values: pd.Series, recent_count: int, damping: float) -> float:
    if len(values) < recent_count * 2:
        return 0.0
    recent = float(values.tail(recent_count).mean())
    prior = float(values.iloc[-recent_count * 2 : -recent_count].mean())
    scale = float(values.std(ddof=0))
    if not pd.notna(scale) or scale <= 1e-9:
        return 0.0
    return _clip(((recent - prior) / scale) * damping)


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
        return (2, 0.35, "two-year mean change in historical-standard-deviation units; damped context")
    if frequency == "quarterly":
        return (2, 0.75, "two-quarter mean change in historical-standard-deviation units")
    return (3, 1.0, "three-month mean change in historical-standard-deviation units")


def _clip(value: float) -> float:
    return max(min(float(value), 1.0), -1.0)
