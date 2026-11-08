from dataclasses import replace
from io import StringIO

import pandas as pd
import pytest

from cycle_screener.bis_sources import bis_csv_series, fetch_bis_policy
from cycle_screener.config import Settings
from cycle_screener.indicators import IndicatorDefinition


def definition(source="bis_policy", key="M.US"):
    return IndicatorDefinition("test", "Test", source, key, "%", "lower_tailwind", "Test")


def csv(unit="368", multiplier="0", period="2026-09", value="3.875"):
    return pd.read_csv(StringIO(f"FREQ,REF_AREA,UNIT_MEASURE,UNIT_MULT,TIME_PERIOD,OBS_VALUE\nM,US,{unit},{multiplier},{period},{value}\n"), dtype=str)


def test_policy_preserves_reference_month_and_numeric_value():
    result = bis_csv_series(csv(), definition(), dataset="WS_CBPOL")
    assert result.iloc[0].observed_at == "2026-09-30"
    assert result.iloc[0].value == 3.875
    assert result.iloc[0].source == "bis_policy"


def test_cpi_keeps_index_for_downstream_yoy_transform():
    result = bis_csv_series(csv(unit="628", value="120.649287"), definition("bis_cpi", "M.US.628"), dataset="WS_LONG_CPI")
    assert result.iloc[0].value == 120.649287


@pytest.mark.parametrize("raw", [csv(unit="771"), csv(multiplier="2"), csv(period="2026-Q3"), csv(value="inf"), csv(value="NaN")])
def test_invalid_policy_input_is_rejected(raw):
    with pytest.raises(ValueError):
        bis_csv_series(raw, definition(), dataset="WS_CBPOL")


def test_duplicate_period_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        bis_csv_series(pd.concat([csv(), csv()]), definition(), dataset="WS_CBPOL")


def test_wrong_country_not_used_as_fallback():
    with pytest.raises(ValueError, match="missing requested"):
        bis_csv_series(csv(), definition(key="M.GB"), dataset="WS_CBPOL")


def test_cpi_growth_rate_not_mistaken_for_index():
    with pytest.raises(ValueError, match="index"):
        bis_csv_series(csv(unit="771"), definition("bis_cpi", "M.US.771"), dataset="WS_LONG_CPI")


def test_missing_month_not_filled():
    raw = pd.concat([csv(period="2026-07"), csv(period="2026-09")])
    result = bis_csv_series(raw, definition(), dataset="WS_CBPOL")
    assert result.observed_at.tolist() == ["2026-07-31", "2026-09-30"]


def test_fetch_isolates_missing_country_and_reports_failure(monkeypatch):
    class Response:
        text = csv().to_csv(index=False)
        def raise_for_status(self):
            pass
    monkeypatch.setattr("cycle_screener.bis_sources.requests.get", lambda *args, **kwargs: Response())
    indicators = [definition(), replace(definition(key="M.GB"), slug="missing")]
    frame, statuses = fetch_bis_policy(indicators, Settings())
    assert frame.indicator_slug.tolist() == ["test"]
    assert [s.status for s in statuses] == ["ok", "failed"]
