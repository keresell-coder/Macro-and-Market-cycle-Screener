from __future__ import annotations

from cycle_screener.sample_data import generate_sample_observations, generate_sample_research_mentions
from cycle_screener.scoring import calculate_scores
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

