from __future__ import annotations

import pandas as pd

from cycle_screener.cycle_state import build_cycle_state


def test_cycle_state_classifies_constructive_public_evidence() -> None:
    observations = _observations(
        {
            "g20_cli": "up",
            "g7_cli": "up",
            "us_cli": "up",
            "china_cli": "up",
            "europe_cli": "up",
            "global_pmi": "up",
            "china_growth_proxy": "up",
            "norway_cpi": "down",
            "rates_pressure": "down",
            "norges_bank_policy_rate": "down",
            "brent": "up",
            "us_natural_gas": "down",
            "chicago_fed_nfci": "down",
            "st_louis_financial_stress": "down",
            "nasdaq_proxy": "up",
            "copper": "up",
            "aluminum": "up",
            "oil_curve_pressure": "up",
            "us_equity_market_cap_gdp_proxy": "down",
            "vix_proxy": "down",
            "sp500_equal_weight_leadership_proxy": "up",
        }
    )

    state = build_cycle_state(
        observations=observations,
        source_freshness=_freshness(observations),
        signal_groups=[],
        subsectors=[],
        contradicting_evidence=[],
        framework_coverage=[],
    )

    assert state["global_equity_cycle"]["phase"] in {"recovery confirmation", "mid-cycle continuation"}
    assert state["global_equity_cycle"]["confidence"] == "high"
    assert any(item["dimension_id"] == "growth" and item["status"] == "growth support" for item in state["dimensions"])
    assert any(item["dimension_id"] == "liquidity_credit" and item["status"] == "liquidity tailwind" for item in state["dimensions"])


def test_cycle_state_marks_missing_data_as_insufficient_evidence() -> None:
    state = build_cycle_state(
        observations=pd.DataFrame(columns=["indicator_slug", "observed_at", "value", "source"]),
        source_freshness=[],
        signal_groups=[],
        subsectors=[],
        contradicting_evidence=[],
        framework_coverage=[
            {
                "dimension": "Market internals and positioning",
                "status": "limited",
                "main_gap": "No breadth, volatility, fund-flow, short-interest, CFTC, or positioning layer.",
            }
        ],
    )

    assert state["global_equity_cycle"]["phase"] == "insufficient evidence"
    assert all(item["phase"] == "insufficient evidence" for item in state["dimensions"])
    assert state["missing_data_caveats"][0]["dimension"] == "Market internals and positioning"


def test_cycle_state_surfaces_cycle_contradictions() -> None:
    observations = _observations(
        {
            "g20_cli": "up",
            "g7_cli": "up",
            "us_cli": "up",
            "china_cli": "up",
            "europe_cli": "up",
            "global_pmi": "up",
            "china_growth_proxy": "up",
            "norway_cpi": "down",
            "rates_pressure": "down",
            "norges_bank_policy_rate": "down",
            "brent": "up",
            "us_natural_gas": "down",
            "chicago_fed_nfci": "up",
            "st_louis_financial_stress": "up",
            "nasdaq_proxy": "up",
            "copper": "up",
            "aluminum": "up",
            "oil_curve_pressure": "up",
            "us_equity_market_cap_gdp_proxy": "up",
            "vix_proxy": "up",
            "sp500_equal_weight_leadership_proxy": "down",
        }
    )

    state = build_cycle_state(
        observations=observations,
        source_freshness=_freshness(observations),
        signal_groups=[],
        subsectors=[],
        contradicting_evidence=[],
        framework_coverage=[],
    )

    titles = {item["title"] for item in state["contradictions"]}
    assert "Risk appetite conflicts with liquidity/credit" in titles
    assert "Risk appetite conflicts with valuation/internals" in titles
    assert state["global_equity_cycle"]["phase"] in {"transition watch", "late-cycle/crowded risk"}


def _observations(slug_direction: dict[str, str]) -> pd.DataFrame:
    dates = pd.date_range("2025-01-31", periods=12, freq="ME")
    rows = []
    for slug, direction in slug_direction.items():
        for index, observed_at in enumerate(dates):
            value = 100 + index * 2 if direction == "up" else 124 - index * 2
            rows.append(
                {
                    "indicator_slug": slug,
                    "observed_at": observed_at.date().isoformat(),
                    "value": value,
                    "source": "test_live",
                    "unit": "index",
                }
            )
    return pd.DataFrame(rows)


def _freshness(observations: pd.DataFrame) -> list[dict[str, object]]:
    records = []
    for slug, group in observations.groupby("indicator_slug"):
        records.append(
            {
                "indicator_slug": slug,
                "display_slug": slug,
                "latest_observed_at": group["observed_at"].max(),
                "source_category": "live_numeric",
                "freshness_status": "current",
                "has_sample_fallback": False,
            }
        )
    return records
