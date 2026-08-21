from __future__ import annotations

from dataclasses import replace

import pandas as pd
import pytest

from cycle_screener.config import Settings, get_settings
from cycle_screener.build_static_site import assert_no_numeric_sample_fallback
from cycle_screener.indicators import indicator_by_slug
from cycle_screener.outlooks import load_institutional_outlooks
from cycle_screener.report_state import _freshness_status
from cycle_screener.scoring import _family_metrics
from cycle_screener.signal_metrics import build_indicator_metrics, polarity_adjusted_momentum, tailwind_score


def test_critical_source_and_transform_contracts() -> None:
    definitions = indicator_by_slug()

    assert definitions["norges_bank_policy_rate"].source_key == "IR/B.KPRA.SD"
    assert definitions["norway_cpi"].source_key.startswith("14700/")
    assert definitions["norway_cpi"].unit == "% y/y"
    assert definitions["rates_pressure"].source_key == "DGS10"
    assert definitions["rates_pressure"].unit == "%"
    assert definitions["global_pmi"].name == "Global annual GDP growth background"
    assert definitions["oil_curve_pressure"].name == "Brent–WTI cross-benchmark spread"


def test_global_policy_rate_coverage_uses_bis_plus_norges_bank() -> None:
    definitions = indicator_by_slug()
    bis_policy = [item for item in definitions.values() if item.source == "dbnomics_bis_policy"]

    assert len(bis_policy) == 9
    assert {item.source_key for item in bis_policy} == {"M.US", "M.XM", "M.GB", "M.JP", "M.CN", "M.CA", "M.AU", "M.CH", "M.SE"}
    assert definitions["norges_bank_policy_rate"].critical is True


def test_lower_tailwind_momentum_has_correct_economic_polarity() -> None:
    assert polarity_adjusted_momentum(0.4, "lower_tailwind") == -0.4
    assert polarity_adjusted_momentum(-0.4, "lower_tailwind") == 0.4
    assert tailwind_score(0.9, 0.4, "lower_tailwind") < 0
    assert tailwind_score(0.1, -0.4, "lower_tailwind") > 0


def test_mixed_direction_has_no_automatic_positive_tailwind() -> None:
    assert tailwind_score(0.5, 1.0, "mixed") == 0
    assert tailwind_score(0.95, 1.0, "mixed") < 0


def test_short_history_is_not_scored() -> None:
    rows = [
        {"indicator_slug": "chicago_fed_nfci", "observed_at": date.date().isoformat(), "value": index / 10}
        for index, date in enumerate(pd.date_range("2025-01-31", periods=24, freq="ME"))
    ]
    assert "chicago_fed_nfci" not in build_indicator_metrics(pd.DataFrame(rows))


def test_zero_centred_index_momentum_is_bounded_and_not_a_ratio() -> None:
    rows = [
        {"indicator_slug": "chicago_fed_nfci", "observed_at": date.date().isoformat(), "value": -1.0 + index / 30}
        for index, date in enumerate(pd.date_range("2021-01-31", periods=60, freq="ME"))
    ]
    metric = build_indicator_metrics(pd.DataFrame(rows))["chicago_fed_nfci"]
    assert -1 <= float(metric["momentum"]) <= 1
    assert float(metric["economic_momentum"]) == -float(metric["momentum"])


def test_correlated_country_series_collapse_to_one_family() -> None:
    one = {"family": "policy_rates", "percentile": 0.2, "tailwind_score": 0.4, "economic_momentum": 0.3}
    family = _family_metrics([one, {**one, "percentile": 0.8, "tailwind_score": -0.4, "economic_momentum": -0.3}])
    assert len(family) == 1
    assert family[0]["tailwind_score"] == 0


def test_indicator_specific_freshness_thresholds() -> None:
    assert _freshness_status(200, expected_release_days=550) == "current"
    assert _freshness_status(80, expected_release_days=50) == "stale"
    assert _freshness_status(100, expected_release_days=50) == "very_stale"


def test_reviewed_outlook_file_uses_official_domains_and_is_non_scoring() -> None:
    frame, statuses = load_institutional_outlooks(get_settings())
    assert len(frame) >= 8
    assert frame["review_status"].eq("reviewed").all()
    assert set(frame["source_tier"]).issubset({"multilateral_primary", "central_bank_primary", "institution_primary"})
    assert statuses[0].status == "ok"


def test_outlook_loader_rejects_unofficial_domains(tmp_path) -> None:
    public = tmp_path / "public_research_evidence"
    public.mkdir()
    frame, _ = load_institutional_outlooks(get_settings())
    bad = frame.head(1).copy()
    bad["source_url"] = "https://example.com/opinion"
    bad.to_csv(public / "institutional_outlooks.csv", index=False)
    settings = replace(get_settings(), public_research_evidence_dir=public, database_path=tmp_path / "db.duckdb")
    with pytest.raises(ValueError, match="official domains"):
        load_institutional_outlooks(settings)


def test_strict_live_guard_rejects_deterministic_sample_database() -> None:
    state = {"source_health": {"numeric": {"mode": "deterministic_sample", "sample_fallback_indicator_count": 0}}}
    with pytest.raises(RuntimeError, match="deterministic sample"):
        assert_no_numeric_sample_fallback(state)
