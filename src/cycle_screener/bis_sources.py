"""Official BIS feeds, without the frozen DBnomics/FRED mirrors.

Policy data preserve BIS WS_CBPOL monthly end-of-period definitions. CPI data
are national all-items indices (2010=100), not HICP, core CPI or inflation rates.
The downstream yoy_pct transform remains responsible for twelve-month changes.
See https://data.bis.org/topics/CBPOL and https://data.bis.org/topics/CPI and
https://www.bis.org/statistics/cp/cp_long_documentation.pdf .
"""
from __future__ import annotations

from io import StringIO
import re
from typing import Iterable

import pandas as pd
import requests

from .config import Settings
from .indicators import IndicatorDefinition

BIS_API = "https://stats.bis.org/api/v1/data"


def bis_csv_series(raw: pd.DataFrame, indicator: IndicatorDefinition, *, dataset: str) -> pd.DataFrame:
    """Validate dimensions/units before accepting a single monthly series."""
    from .connectors import _finalize_indicator_frame

    if dataset not in {"WS_CBPOL", "WS_LONG_CPI"}:
        raise ValueError(f"Unsupported BIS dataset: {dataset}")
    required = {"FREQ", "REF_AREA", "UNIT_MEASURE", "UNIT_MULT", "TIME_PERIOD", "OBS_VALUE"}
    if not required.issubset(raw.columns):
        raise ValueError(f"BIS CSV missing columns: {sorted(required - set(raw.columns))}")
    parts = indicator.source_key.split(".")
    expected_unit = "368" if dataset == "WS_CBPOL" else "628"
    expected_parts = 2 if dataset == "WS_CBPOL" else 3
    if len(parts) != expected_parts or parts[0] != "M" or not re.fullmatch(r"[A-Z]{2}", parts[1]):
        raise ValueError(f"Invalid monthly BIS series key: {indicator.source_key}")
    if dataset == "WS_LONG_CPI" and parts[2] != expected_unit:
        raise ValueError("CPI input must be an index (BIS unit 628), not a change rate")
    frame = raw[(raw["FREQ"].astype(str) == "M") & (raw["REF_AREA"].astype(str) == parts[1])].copy()
    if frame.empty:
        raise ValueError(f"BIS response missing requested series {indicator.source_key}")
    if not pd.to_numeric(frame["UNIT_MEASURE"], errors="coerce").eq(int(expected_unit)).all():
        raise ValueError("BIS response contains unexpected unit measure")
    if not pd.to_numeric(frame["UNIT_MULT"], errors="coerce").eq(0).all():
        raise ValueError("BIS response contains unexpected unit multiplier")
    if not frame["TIME_PERIOD"].astype(str).str.fullmatch(r"\d{4}-\d{2}").all():
        raise ValueError("BIS monthly response contains invalid reference periods")
    if frame["TIME_PERIOD"].duplicated().any():
        raise ValueError("BIS response contains duplicate monthly observations")
    frame["value"] = pd.to_numeric(frame["OBS_VALUE"], errors="coerce").replace([float("inf"), -float("inf")], float("nan"))
    # Month-end denotes the supplied reference month, never the retrieval date.
    frame["observed_at"] = pd.PeriodIndex(frame["TIME_PERIOD"], freq="M").to_timestamp("M")
    return _finalize_indicator_frame(frame[["observed_at", "value"]], indicator, indicator.source)


def _fetch_bis(indicators: Iterable[IndicatorDefinition], settings: Settings, *, dataset: str):
    from .connectors import _status

    indicators = list(indicators)
    if not indicators:
        return pd.DataFrame(), []
    frames, statuses = [], []
    areas = "+".join(sorted({i.source_key.split(".")[1] for i in indicators}))
    key = f"M.{areas}" + (".628" if dataset == "WS_LONG_CPI" else "")
    url = f"{BIS_API}/{dataset}/{key}"
    try:
        response = requests.get(url, params={"format": "csv"}, headers={"Accept": "text/csv"},
                                timeout=(min(settings.request_timeout_seconds, 10), max(settings.request_timeout_seconds, 90)))
        response.raise_for_status()
        raw = pd.read_csv(StringIO(response.text), dtype=str)
    except Exception as exc:
        return pd.DataFrame(), [_status(f"{i.source}:{i.slug}", "failed", f"Could not fetch official BIS {dataset}: {exc}") for i in indicators]
    for indicator in indicators:
        try:
            frame = bis_csv_series(raw, indicator, dataset=dataset)
            frames.append(frame)
            statuses.append(_status(f"{indicator.source}:{indicator.slug}", "ok", f"Fetched {len(frame)} monthly observations from official BIS {dataset}/{indicator.source_key}; latest reference date {frame.observed_at.iloc[-1]}."))
        except Exception as exc:
            statuses.append(_status(f"{indicator.source}:{indicator.slug}", "failed", f"Could not parse official BIS {dataset}/{indicator.source_key}: {exc}"))
    return (pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()), statuses


def fetch_bis_policy(indicators: Iterable[IndicatorDefinition], settings: Settings):
    return _fetch_bis(indicators, settings, dataset="WS_CBPOL")


def fetch_bis_cpi(indicators: Iterable[IndicatorDefinition], settings: Settings):
    return _fetch_bis(indicators, settings, dataset="WS_LONG_CPI")
