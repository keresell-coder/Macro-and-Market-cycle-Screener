from datetime import datetime, timezone

import pandas as pd
import pytest

from cycle_screener.connectors import _monthly_last, _yahoo_completed_daily_frame
from cycle_screener.indicators import indicator_by_slug
from cycle_screener.scoring import calculate_scores
from cycle_screener.signal_metrics import build_indicator_metrics
from cycle_screener.source_health import observation_health, numeric_health, assert_publication_health, public_health
from cycle_screener.decision_support import _trust_summary
from cycle_screener.change_tracking import compare_report_states
from cycle_screener.static_site_qa import run_static_site_qa
from cycle_screener.blocked_publication import build_blocked_site

NOW = datetime(2026, 9, 9, 10, tzinfo=timezone.utc)


def history(slug, end="2026-08-31", scale=1):
    return pd.DataFrame([
        {"indicator_slug": slug, "observed_at": d.date().isoformat(), "value": scale * (100 + i + i * i / 10), "source": "official", "unit": "index"}
        for i, d in enumerate(pd.date_range(end=end, periods=72, freq="ME"))
    ])


def health(frame):
    return observation_health(frame, as_of=NOW, supported_slugs=set(build_indicator_metrics(frame)))


def test_stale_sector_signal_cannot_move_rank_or_raise_data_support():
    fresh = history("copper")
    stale = history("g20_cli", end="2025-05-31")
    baseline = calculate_scores(fresh, as_of=NOW).set_index("slug")
    contaminated = calculate_scores(pd.concat([fresh, stale]), as_of=NOW).set_index("slug")
    pd.testing.assert_series_equal(baseline["research_priority_score"], contaminated["research_priority_score"])
    assert baseline.loc["metals_aluminum", "data_support"] == contaminated.loc["metals_aluminum", "data_support"]
    assert "g20_cli" in contaminated.loc["metals_aluminum", "excluded_indicators"]


@pytest.mark.parametrize("frame", [pd.DataFrame(), history("g20_cli", "2020-01-31"), history("g20_cli", "2026-10-31")])
def test_absent_stale_and_future_only_inputs_have_no_neutral_score(frame):
    scores = calculate_scores(frame, as_of=NOW)
    assert scores["research_priority_score"].isna().all()
    assert scores["score_status"].eq("unavailable").all()
    assert scores["data_support"].eq(0).all()
    records = health(frame)
    numeric = numeric_health(records)
    assert numeric["status"] == "blocked"
    assert numeric["usable_indicator_count"] == 0
    trust = _trust_summary({"source_health": {"numeric": numeric}})
    assert trust["data_quality"]["score"] == 0
    assert trust["historical_validation"]["score"] is None
    from cycle_screener.cycle_state import build_cycle_state
    cycle = build_cycle_state(frame, records, [], [], [], [])
    assert cycle["global_equity_cycle"]["score"] is None
    assert all(d["score"] is None and d["direction"] == "unavailable" and d["coverage"]["available_count"] == 0 for d in cycle["dimensions"])
    with pytest.raises(RuntimeError, match="blocks publication"):
        assert_publication_health({"source_freshness": records, "source_health": {"numeric": numeric}})


def test_future_timestamp_is_not_clamped_and_short_history_is_not_usable():
    records = health(pd.concat([history("g20_cli", "2026-10-31"), history("copper").tail(2)]))
    by_slug = {r["indicator_slug"]: r for r in records}
    assert by_slug["g20_cli"]["latest_observed_at"] == "2026-10-31"
    assert by_slug["g20_cli"]["age_days"] < 0
    assert by_slug["copper"]["exclusion_reason"] == "insufficient_history"
    assert by_slug["usd_nok"]["freshness_status"] == "missing"
    assert len(records) == len(indicator_by_slug())


def test_monthly_reference_dates_and_release_lag_do_not_become_fetch_dates():
    monthly = history("us_cpi", "2026-07-31")
    monthly["observed_at"] = pd.to_datetime(monthly["observed_at"]).dt.to_period("M").dt.start_time.dt.date.astype(str)
    record = next(r for r in health(monthly) if r["indicator_slug"] == "us_cpi")
    assert record["latest_observed_at"] == "2026-07-01"
    assert record["observation_period_start"] == "2026-07-01"
    assert record["observation_period_end"] == "2026-07-31"
    assert record["age_days"] == 70
    assert record["age_since_reference_period_end_days"] == 40
    assert record["scoring_eligible"] is True
    future = monthly.copy()
    future.loc[future.index[-1], "observed_at"] = "2026-09-01"
    record = next(r for r in health(future) if r["indicator_slug"] == "us_cpi")
    assert record["latest_observed_at"] == "2026-09-01"
    assert record["observation_period_end"] == "2026-09-30"
    assert record["scoring_eligible"] is False


def test_monthly_reduction_preserves_actual_source_date():
    frame = pd.DataFrame({"observed_at": ["2026-08-28", "2026-08-31", "2026-09-04"], "value": [10, 20, 30]})
    actual = _monthly_last(frame, indicator_by_slug()["rates_pressure"], "fred_public")
    assert actual["observed_at"].tolist() == ["2026-08-31", "2026-09-04"]


def test_yahoo_monthly_score_uses_completed_exchange_session_and_adjusted_close():
    dates = ["2026-08-31T13:30:00Z", "2026-09-08T13:30:00Z", "2026-09-09T13:30:00Z"]
    payload = {"meta": {"exchangeTimezoneName": "America/New_York"}, "timestamp": [int(pd.Timestamp(d).timestamp()) for d in dates], "indicators": {"adjclose": [{"adjclose": [101, 102, 999]}]}}
    frame = _yahoo_completed_daily_frame(payload, indicator_by_slug()["global_equity_proxy"], as_of=NOW)
    assert frame["observed_at"].tolist() == ["2026-08-31", "2026-09-08"]
    assert frame["value"].tolist() == [101, 102]
    payload["indicators"] = {"quote": [{"close": [1, 2, 3]}]}
    with pytest.raises(ValueError, match="Adjusted daily"):
        _yahoo_completed_daily_frame(payload, indicator_by_slug()["global_equity_proxy"], as_of=NOW)


def test_critical_coverage_gate_and_manifest_counts():
    definitions = indicator_by_slug()
    critical = [history(slug, "2026-09-08") for slug, d in definitions.items() if d.critical]
    records = health(pd.concat(critical))
    numeric = numeric_health(records)
    assert numeric["status"] == "degraded"
    assert numeric["missing_indicator_count"] > 0
    state = {"generated_at": NOW.isoformat(), "source_freshness": records, "source_health": {"numeric": numeric}}
    assert_publication_health(state)
    payload = public_health(state)
    assert payload["generated_at"] == NOW.isoformat()
    assert payload["source_observation_end"] == "2026-08-31"
    assert payload["coverage"]["configured_indicator_count"] == len(definitions)
    assert payload["research_validation"] == "not_established"
    numeric["usable_indicator_count"] += 1
    with pytest.raises(RuntimeError, match="counts/status"):
        assert_publication_health(state)


def test_all_configured_usable_is_current_and_all_stale_is_blocked():
    normal = pd.concat([history(slug, "2025-12-31" if d.source == "world_bank_indicator" else "2026-06-30" if slug == "us_equity_market_cap_gdp_proxy" else "2026-08-31") for slug, d in indicator_by_slug().items()])
    records = health(normal)
    assert numeric_health(records)["status"] == "current"
    old = normal.copy()
    old["observed_at"] = (pd.to_datetime(old["observed_at"]) - pd.DateOffset(years=5)).dt.date.astype(str)
    assert numeric_health(health(old))["usable_coverage_ratio"] == 0


def test_missing_score_change_is_not_a_market_drop():
    old = {"subsectors": [{"slug": "x", "rank": 1, "opportunity_score": 60, "score_status": "usable"}]}
    new = {"subsectors": [{"slug": "x", "rank": None, "opportunity_score": None, "score_status": "unavailable"}]}
    change = compare_report_states(old, new)["subsector_changes"][0]
    assert change["score_delta"] is None
    assert change["rank_delta"] is None
    assert change["score_move"] == "unavailable"


@pytest.mark.parametrize("previous", [None, {"generated_at": "2026-09-05T11:21:21+00:00", "data_as_of": "2026-09-04", "subsectors": [{"slug": "old", "opportunity_score": 55}]}])
def test_blocked_bootstrap_publishes_notice_and_never_new_research(tmp_path, monkeypatch, previous):
    import json
    monkeypatch.setattr("cycle_screener.blocked_publication._ensure_public_output", lambda _: None)
    records = health(history("g20_cli", "2025-05-31"))
    current = {"generated_at": NOW.isoformat(), "source_freshness": records, "source_health": {"numeric": numeric_health(records)}, "subsectors": [{"slug": "should_not_publish", "opportunity_score": 99}]}
    reports = tmp_path / "reports"
    reports.mkdir()
    archive = reports / "2026-09-05.html"
    original = '<html>Original edition, generated 2026-09-05; original limitations.</html>'
    archive.write_text(original)
    (reports / "2026-09-09.html").write_text("sample/new verdict must not leak")
    (tmp_path / "weekly").mkdir()
    (tmp_path / "weekly" / "weekly-cycle-brief.pdf").write_bytes(b"sample PDF must not leak")
    result = build_blocked_site(current, previous, [{"file": archive.name, "date": "2026-09-05"}, {"file": "missing.html"}, {"file": "../../outside.html"}], tmp_path, "Critical OECD input is stale")
    assert result["publication_status"] == "blocked"
    assert archive.read_text() == original
    assert not (reports / "2026-09-09.html").exists()
    assert not (tmp_path / "weekly").exists()
    manifest = json.loads((tmp_path / "health.json").read_text())
    assert manifest["generated_at"] == (previous or {}).get("generated_at")
    assert manifest["latest_attempt_at"] == NOW.isoformat()
    assert manifest["coverage"]["usable_indicator_count"] == 0
    assert manifest["publication_mode"] == "blocked_status_page"
    assert manifest["attempt_status"] == "failed"
    assert "should_not_publish" not in (tmp_path / "index.html").read_text()
    if previous:
        assert json.loads((tmp_path / "data" / "report_state.json").read_text()) == previous
    else:
        assert not (tmp_path / "data" / "report_state.json").exists()
    assert run_static_site_qa(tmp_path)["retained_archive_count"] == 1


def test_strict_builder_only_uses_blocked_fallback_when_explicitly_enabled(tmp_path, monkeypatch):
    import cycle_screener.build_static_site as builder
    records = health(history("g20_cli", "2025-05-31"))
    current = {"generated_at": NOW.isoformat(), "source_freshness": records, "source_health": {"numeric": numeric_health(records)}}
    monkeypatch.setattr(builder, "build_report_state", lambda: current)
    monkeypatch.setattr("cycle_screener.blocked_publication._ensure_public_output", lambda _: None)
    with pytest.raises(RuntimeError, match="blocks publication"):
        builder.build_static_site(fail_on_numeric_sample_fallback=True, site_dir=tmp_path)
    assert not (tmp_path / "index.html").exists()
    result = builder.build_static_site(fail_on_numeric_sample_fallback=True, publish_blocked_status=True, site_dir=tmp_path)
    assert result["publication_status"] == "blocked"
    assert run_static_site_qa(tmp_path)["publication_status"] == "blocked"


def test_missing_values_render_as_unavailable_instead_of_zero():
    from cycle_screener.static_site import _score_bar, _signal_cell, _rank_delta
    assert "unavailable" in _score_bar(None)
    assert "n/a" in _signal_cell("momentum", None)
    assert _rank_delta(None) == "unavailable"
