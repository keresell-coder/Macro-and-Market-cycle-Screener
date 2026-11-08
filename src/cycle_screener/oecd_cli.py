"""Read the original OECD CLI, rather than a potentially frozen mirror.

The key identifies the amplitude-adjusted, index-form CLI with OECD's H
methodology. The parser verifies every dimension before admitting a value.
Monthly reference periods are not retrieval dates or forecasts.
"""
from __future__ import annotations

from io import StringIO
import re

import pandas as pd
import requests

from .indicators import IndicatorDefinition


OECD_CLI_URL = "https://sdmx.oecd.org/public/rest/v1/data/OECD.SDD.STES,DSD_STES@DF_CLI,4.1/"
CLI_DIMENSIONS = {
    "FREQ": "M", "MEASURE": "LI", "UNIT_MEASURE": "IX",
    "ACTIVITY": "_Z", "ADJUSTMENT": "AA", "TRANSFORMATION": "IX",
    "TIME_HORIZ": "_Z", "METHODOLOGY": "H", "UNIT_MULT": "0",
}


def fetch_oecd_cli(indicators: list[IndicatorDefinition], timeout: int) -> tuple[dict[str, pd.DataFrame], dict[str, str]]:
    if not indicators:
        return {}, {}
    areas = sorted({item.source_key.split(".")[0] for item in indicators})
    if any(not re.fullmatch(r"[A-Z0-9]+", area) for area in areas):
        raise ValueError("Unexpected OECD reference-area key.")
    key = "+".join(areas) + ".M.LI.IX._Z.AA.IX._Z.H"
    response = requests.get(
        OECD_CLI_URL + key,
        params={"startPeriod": "1995-01", "dimensionAtObservation": "AllDimensions"},
        headers={"Accept": "text/csv", "User-Agent": "GlobalCycleScreener/0.4 public data refresh"},
        timeout=(min(timeout, 10), max(timeout, 45)),
    )
    response.raise_for_status()
    frames, errors = {}, {}
    for item in indicators:
        try:
            frames[item.slug] = parse_oecd_cli(response.text, item)
        except ValueError as exc:
            errors[item.slug] = str(exc)
    return frames, errors


def parse_oecd_cli(csv_text: str, indicator: IndicatorDefinition) -> pd.DataFrame:
    raw = pd.read_csv(StringIO(csv_text), dtype=str)
    required = {"REF_AREA", "TIME_PERIOD", "OBS_VALUE", *CLI_DIMENSIONS}
    if not required.issubset(raw.columns):
        raise ValueError("OECD CSV is missing required CLI dimensions or observations.")
    area = indicator.source_key.split(".")[0]
    selected = raw.loc[raw["REF_AREA"] == area].copy()
    if selected.empty:
        raise ValueError(f"OECD CSV has no observations for {area}.")
    for column, expected in CLI_DIMENSIONS.items():
        if not selected[column].eq(expected).all():
            raise ValueError(f"OECD CLI dimension {column} does not match {expected}.")
    if not selected["TIME_PERIOD"].str.fullmatch(r"\d{4}-\d{2}").all():
        raise ValueError("OECD CLI must have monthly reference periods.")
    selected["value"] = pd.to_numeric(selected["OBS_VALUE"], errors="coerce")
    selected = selected.dropna(subset=["value"])
    if selected.empty or not selected["value"].map(lambda value: float("-inf") < value < float("inf")).all():
        raise ValueError("OECD CLI has no usable finite numeric observations.")
    if selected["TIME_PERIOD"].duplicated().any():
        raise ValueError("OECD CLI contains duplicate monthly observations.")
    selected = selected.sort_values("TIME_PERIOD").tail(361)
    selected["observed_at"] = pd.PeriodIndex(selected["TIME_PERIOD"], freq="M").to_timestamp("M").date.astype(str)
    selected["indicator_slug"] = indicator.slug
    selected["source"] = "oecd_sdmx_cli"
    selected["unit"] = indicator.unit
    return selected[["indicator_slug", "observed_at", "value", "source", "unit"]]
