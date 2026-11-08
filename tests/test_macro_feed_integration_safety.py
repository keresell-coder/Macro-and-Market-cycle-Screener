"""Regression checks for primary-feed integration; no database/network access."""
import pandas as pd
import pytest

from cycle_screener.bis_sources import bis_csv_series
from cycle_screener.config import Settings
from cycle_screener.connectors import _fetch_oecd_cli, _fetch_oecd_cli_mirror
from cycle_screener.indicators import indicator_by_slug
from cycle_screener.source_health import observation_health


@pytest.mark.parametrize("slug,area,unit,dataset", [
    ("fed_policy_rate", "US", "368", "WS_CBPOL"),
    ("uk_cpi", "GB", "628", "WS_LONG_CPI"),
])
@pytest.mark.parametrize("month,expected", [("2025-01", "very_stale"), ("2026-12", "future_dated")])
def test_primary_bis_success_does_not_override_health_gate(slug, area, unit, dataset, month, expected):
    definition = indicator_by_slug()[slug]
    raw = pd.DataFrame([{"FREQ": "M", "REF_AREA": area, "UNIT_MEASURE": unit,
                         "UNIT_MULT": "0", "TIME_PERIOD": month, "OBS_VALUE": "100"}])
    frame = bis_csv_series(raw, definition, dataset=dataset)
    health = next(row for row in observation_health(frame, as_of="2026-11-08") if row["indicator_slug"] == slug)
    assert health["freshness_status"] == expected
    assert health["reference_period"] == "month"
    assert not health["scoring_eligible"]


def test_cpi_definition_preserves_transform_and_cadence():
    definitions = indicator_by_slug()
    for slug, area in [("uk_cpi", "GB"), ("japan_cpi", "JP"), ("china_cpi", "CN")]:
        definition = definitions[slug]
        assert definition.source == "bis_cpi"
        assert definition.source_key == f"M.{area}.628"
        assert definition.transform == "yoy_pct"
        assert definition.reference_period == "month"
        assert definition.expected_release_days == 60


def test_mirror_parser_preserves_actual_mirror_provenance(monkeypatch):
    class Response:
        def raise_for_status(self):
            pass
        def json(self):
            return {"series": {"docs": [{"period": ["2025-01"], "value": [100.1]}]}}
    monkeypatch.setattr("cycle_screener.connectors.requests.Session.get", lambda *args, **kwargs: Response())
    frame, statuses = _fetch_oecd_cli_mirror([indicator_by_slug()["g20_cli"]], Settings())
    assert frame.source.tolist() == ["dbnomics_oecd_cli"]
    assert frame.observed_at.tolist() == ["2025-01-31"]
    assert statuses[0].source_slug == "dbnomics_oecd_cli:g20_cli"


def test_successful_direct_feed_is_not_overwritten_by_mirror(monkeypatch):
    definition = indicator_by_slug()["g20_cli"]
    direct = pd.DataFrame([{"indicator_slug": definition.slug, "observed_at": "2025-01-31",
                            "value": 100.1, "source": "oecd_sdmx_cli", "unit": "index"}])
    monkeypatch.setattr("cycle_screener.oecd_cli.fetch_oecd_cli", lambda *_: ({definition.slug: direct}, {}))
    def unwanted_mirror(*_):
        raise AssertionError("Do not overwrite successful primary data with mirror data")
    monkeypatch.setattr("cycle_screener.connectors._fetch_oecd_cli_mirror", unwanted_mirror)
    frame, _ = _fetch_oecd_cli([definition], Settings())
    assert frame.source.tolist() == ["oecd_sdmx_cli"]
    assert frame.observed_at.tolist() == ["2025-01-31"]
