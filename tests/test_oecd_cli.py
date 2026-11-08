from io import StringIO

import pandas as pd
import pytest

from cycle_screener.config import Settings
from cycle_screener.connectors import _fetch_oecd_cli
from cycle_screener.indicators import indicator_by_slug
from cycle_screener.oecd_cli import CLI_DIMENSIONS, parse_oecd_cli
from cycle_screener.source_health import observation_health


def fixture_csv(**changes):
    rows = [{**CLI_DIMENSIONS, "REF_AREA": "G20", "TIME_PERIOD": month,
             "OBS_VALUE": value, **changes}
            for month, value in [("2026-09", "100.1"), ("2026-08", "99.9")]]
    return pd.DataFrame(rows).to_csv(index=False)


def test_official_cli_sorts_reference_months_and_preserves_provenance():
    frame = parse_oecd_cli(fixture_csv(), indicator_by_slug()["g20_cli"])
    assert frame.observed_at.tolist() == ["2026-08-31", "2026-09-30"]
    assert frame.value.tolist() == [99.9, 100.1]
    assert frame.source.eq("oecd_sdmx_cli").all()


@pytest.mark.parametrize("column,value", [("FREQ", "Q"), ("MEASURE", "GDP"),
    ("UNIT_MULT", "3"), ("ADJUSTMENT", "Y"), ("TRANSFORMATION", "GY"),
    ("METHODOLOGY", "X"), ("TIME_PERIOD", "2026-09-01")])
def test_official_cli_rejects_wrong_series_or_period(column, value):
    with pytest.raises(ValueError):
        parse_oecd_cli(fixture_csv(**{column: value}), indicator_by_slug()["g20_cli"])


def test_official_cli_rejects_missing_country_duplicate_month_and_nonfinite():
    definition = indicator_by_slug()["g20_cli"]
    for csv in [fixture_csv(REF_AREA="USA"), fixture_csv(TIME_PERIOD="2026-09"), fixture_csv(OBS_VALUE="inf")]:
        with pytest.raises(ValueError):
            parse_oecd_cli(csv, definition)


def test_official_cli_does_not_make_stale_or_future_months_usable():
    definition = indicator_by_slug()["g20_cli"]
    for month, expected in [("2025-01", "very_stale"), ("2026-12", "future_dated")]:
        raw = pd.read_csv(StringIO(fixture_csv())).head(1)
        raw["TIME_PERIOD"] = month
        frame = parse_oecd_cli(raw.to_csv(index=False), definition)
        row = next(r for r in observation_health(frame, as_of="2026-11-08") if r["indicator_slug"] == "g20_cli")
        assert row["freshness_status"] == expected
        assert not row["scoring_eligible"]


def test_optional_cli_failure_does_not_discard_successful_critical_cli(monkeypatch):
    definitions = indicator_by_slug()
    g20 = parse_oecd_cli(fixture_csv(), definitions["g20_cli"])
    monkeypatch.setattr("cycle_screener.oecd_cli.fetch_oecd_cli", lambda *_: ({"g20_cli": g20}, {"g7_cli": "missing"}))
    calls = []
    def mirror(items, settings):
        calls.extend(item.slug for item in items)
        return pd.DataFrame(), []
    monkeypatch.setattr("cycle_screener.connectors._fetch_oecd_cli_mirror", mirror)
    frame, statuses = _fetch_oecd_cli([definitions["g20_cli"], definitions["g7_cli"]], Settings())
    assert set(frame.indicator_slug) == {"g20_cli"}
    assert calls == ["g7_cli"]
    assert any(s.status == "degraded" for s in statuses)


def test_direct_cli_transport_failure_keeps_stale_mirror_excluded(monkeypatch):
    definition = indicator_by_slug()["g20_cli"]
    stale = parse_oecd_cli(fixture_csv(), definition)
    stale["observed_at"] = ["2026-04-30", "2026-05-31"]
    stale["source"] = "dbnomics_oecd_cli"
    def fail(*_):
        raise RuntimeError("source unavailable")
    monkeypatch.setattr("cycle_screener.oecd_cli.fetch_oecd_cli", fail)
    monkeypatch.setattr("cycle_screener.connectors._fetch_oecd_cli_mirror", lambda *_: (stale, []))
    frame, _ = _fetch_oecd_cli([definition], Settings())
    row = next(r for r in observation_health(frame, as_of="2026-11-08") if r["indicator_slug"] == "g20_cli")
    assert row["latest_observed_at"] == "2026-05-31"
    assert not row["scoring_eligible"]
