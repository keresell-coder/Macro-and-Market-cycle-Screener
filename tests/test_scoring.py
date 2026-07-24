from __future__ import annotations

import pandas as pd

from cycle_screener.sample_data import generate_sample_observations, generate_sample_research_mentions
from cycle_screener.scoring import calculate_scores
from cycle_screener.signal_metrics import build_indicator_metrics
from cycle_screener.taxonomy import SUBSECTORS


def test_calculate_scores_returns_every_subsector() -> None:
    scores = calculate_scores(generate_sample_observations(), generate_sample_research_mentions())

    assert len(scores) == len(SUBSECTORS)
    assert scores["opportunity_score"].between(0, 100).all()
    assert scores["confidence"].between(0, 1).all()


def test_scores_are_explainable() -> None:
    scores = calculate_scores(generate_sample_observations(), generate_sample_research_mentions())

    assert scores["explanation"].str.contains("Evidence:").all()
    assert scores["name"].iloc[0]


def test_signal_metrics_use_frequency_aware_horizons() -> None:
    rows = []
    for date_index, observed_at in enumerate(pd.date_range("2025-01-01", periods=365, freq="D")):
        rows.append(
            {
                "indicator_slug": "nasdaq_proxy",
                "observed_at": observed_at.date().isoformat(),
                "value": 100 + date_index / 10,
                "source": "test",
            }
        )
    for year_index, year in enumerate(range(2015, 2026)):
        rows.append(
            {
                "indicator_slug": "global_pmi",
                "observed_at": f"{year}-12-31",
                "value": 2 + year_index / 10,
                "source": "test",
            }
        )

    metrics = build_indicator_metrics(pd.DataFrame(rows))

    assert metrics["nasdaq_proxy"]["frequency_bucket"] == "daily_or_weekly"
    assert metrics["nasdaq_proxy"]["observation_count_used"] <= 13
    assert metrics["nasdaq_proxy"]["momentum_horizon"].startswith("three-month")
    assert metrics["global_pmi"]["frequency_bucket"] == "annual"
    assert "damped structural context" in metrics["global_pmi"]["momentum_horizon"]
