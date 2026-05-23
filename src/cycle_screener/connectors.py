from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO, StringIO
from typing import Iterable
from urllib.parse import quote

from bs4 import BeautifulSoup
import pandas as pd
import requests

from .config import Settings
from .indicators import IndicatorDefinition, INDICATORS
from .sample_data import generate_sample_observations, generate_sample_research_mentions
from .sources import SOURCE_DEFINITIONS, RESEARCH_KEYWORDS


@dataclass(frozen=True)
class SourceStatus:
    source_slug: str
    status: str
    message: str
    checked_at: str


def fetch_indicator_observations(settings: Settings, sample: bool = False) -> tuple[pd.DataFrame, list[SourceStatus]]:
    if sample:
        return generate_sample_observations(), [_status("sample", "ok", "Loaded deterministic sample dataset.")]

    frames: list[pd.DataFrame] = []
    statuses: list[SourceStatus] = []
    sample_frame = generate_sample_observations()

    for source, fetcher in (
        ("world_bank_commodity", _fetch_world_bank_commodities),
        ("world_bank_indicator", _fetch_world_bank_indicators),
        ("norges_bank_csv", _fetch_norges_bank_csv),
        ("ssb_cpi", _fetch_ssb_cpi),
        ("yahoo_chart", _fetch_yahoo_chart),
    ):
        source_indicators = [indicator for indicator in INDICATORS if indicator.source == source]
        source_frame, source_status = fetcher(source_indicators, settings)
        statuses.extend(source_status)
        if not source_frame.empty:
            frames.append(source_frame)

    derived_indicators = [indicator for indicator in INDICATORS if indicator.source == "derived_public"]
    base_observations = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    derived_frame, derived_status = _derive_public_indicators(derived_indicators, base_observations, settings)
    statuses.extend(derived_status)
    if not derived_frame.empty:
        frames.append(derived_frame)

    fetched_slugs = set(pd.concat(frames)["indicator_slug"].unique()) if frames else set()
    missing = [indicator.slug for indicator in INDICATORS if indicator.slug not in fetched_slugs]
    if missing:
        fallback_frame = sample_frame[sample_frame["indicator_slug"].isin(missing)].copy()
        fallback_frame["source"] = "sample_fallback"
        frames.append(fallback_frame)
        statuses.append(_status("fallback", "degraded", f"Filled missing live indicators from sample data: {', '.join(sorted(missing))}."))

    observations = pd.concat(frames, ignore_index=True) if frames else sample_frame
    observations = observations.sort_values(["indicator_slug", "observed_at"]).reset_index(drop=True)
    return observations, statuses


def fetch_research_mentions(settings: Settings, sample: bool = False) -> tuple[pd.DataFrame, list[SourceStatus]]:
    if sample:
        return generate_sample_research_mentions(), [_status("sample_research", "ok", "Loaded deterministic sample research mentions.")]

    rows: list[dict[str, object]] = []
    statuses: list[SourceStatus] = []
    session = requests.Session()
    session.headers.update({"User-Agent": "OsloCycleRadar/0.1 research monitor"})
    request_timeout = min(settings.request_timeout_seconds, 6)

    for source in SOURCE_DEFINITIONS:
        if source.source_type != "research" or source.access != "public":
            continue
        try:
            response = session.get(source.url, timeout=(request_timeout, request_timeout))
            response.raise_for_status()
            page_sample = response.content[:300_000].decode(response.encoding or "utf-8", errors="replace")
            text = BeautifulSoup(page_sample, "html.parser").get_text(" ", strip=True)
            lowered = text.lower()
            found = 0
            for theme, keywords in RESEARCH_KEYWORDS.items():
                hits = [keyword for keyword in keywords if keyword in lowered]
                if not hits:
                    continue
                found += 1
                rows.append(
                    {
                        "source_slug": source.slug,
                        "theme": theme,
                        "summary": f"Public source mentions {theme}: {', '.join(hits[:4])}.",
                        "sentiment": _theme_sentiment(theme, lowered),
                        "published_at": datetime.now(timezone.utc).date().isoformat(),
                        "url": source.url,
                    }
                )
            statuses.append(_status(source.slug, "ok", f"Scanned public page; matched {found} research themes."))
        except Exception as exc:  # network and site behavior varies
            statuses.append(_status(source.slug, "failed", f"Could not scan public page: {exc}"))

    if not rows:
        mentions = generate_sample_research_mentions()
        statuses.append(_status("research_fallback", "degraded", "No public research pages could be scanned; used sample mentions."))
    else:
        mentions = pd.DataFrame(rows)
    return mentions, statuses


def _fetch_world_bank_commodities(indicators: Iterable[IndicatorDefinition], settings: Settings) -> tuple[pd.DataFrame, list[SourceStatus]]:
    indicator_list = list(indicators)
    if not indicator_list:
        return pd.DataFrame(), []
    url = "https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Historical-Data-Monthly.xlsx"
    try:
        response = requests.get(url, timeout=(min(settings.request_timeout_seconds, 8), max(settings.request_timeout_seconds, 30)))
        response.raise_for_status()
        raw = pd.read_excel(BytesIO(response.content), sheet_name="Monthly Prices", header=6)
    except Exception as exc:
        return pd.DataFrame(), [_status(f"world_bank_commodity:{indicator.slug}", "failed", f"Could not fetch World Bank Pink Sheet: {exc}") for indicator in indicator_list]

    frames = []
    statuses = []
    for indicator in indicator_list:
        try:
            frame = _wide_monthly_column(raw, "Unnamed: 0", indicator.source_key, indicator, "world_bank_commodity")
            frames.append(frame)
            statuses.append(_status(f"world_bank_commodity:{indicator.slug}", "ok", f"Fetched {indicator.name} from World Bank Pink Sheet ({len(frame)} monthly rows)."))
        except Exception as exc:
            statuses.append(_status(f"world_bank_commodity:{indicator.slug}", "failed", f"Could not parse World Bank Pink Sheet series {indicator.source_key}: {exc}"))
    return (pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()), statuses


def _fetch_world_bank_indicators(indicators: Iterable[IndicatorDefinition], settings: Settings) -> tuple[pd.DataFrame, list[SourceStatus]]:
    frames = []
    statuses = []
    for indicator in indicators:
        country, series = indicator.source_key.split("/", 1)
        url = f"https://api.worldbank.org/v2/country/{country}/indicator/{series}"
        try:
            response = requests.get(url, params={"format": "json", "per_page": 100}, timeout=(5, settings.request_timeout_seconds))
            response.raise_for_status()
            payload = response.json()
            records = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
            rows = []
            for item in records:
                if item.get("value") is None:
                    continue
                year = int(item["date"])
                rows.append({"observed_at": f"{year}-12-31", "value": float(item["value"])})
            if not rows:
                raise ValueError("World Bank returned no numeric observations.")
            frame = pd.DataFrame(rows).sort_values("observed_at").tail(72)
            frames.append(_finalize_indicator_frame(frame, indicator, "world_bank_indicator"))
            statuses.append(_status(f"world_bank_indicator:{indicator.slug}", "ok", f"Fetched {indicator.name} from World Bank Indicators ({len(frame)} annual rows)."))
        except Exception as exc:
            statuses.append(_status(f"world_bank_indicator:{indicator.slug}", "failed", f"Could not fetch World Bank indicator {indicator.source_key}: {exc}"))
    return (pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()), statuses


def _fetch_norges_bank_csv(indicators: Iterable[IndicatorDefinition], settings: Settings) -> tuple[pd.DataFrame, list[SourceStatus]]:
    frames = []
    statuses = []
    for indicator in indicators:
        start = "2020-01-01" if indicator.source_key.startswith("EXR/") else "2020-01"
        try:
            response = requests.get(
                f"https://data.norges-bank.no/api/data/{indicator.source_key}",
                params={"format": "csvfile", "startPeriod": start},
                timeout=(5, settings.request_timeout_seconds),
            )
            response.raise_for_status()
            raw = pd.read_csv(StringIO(response.text))
            frame = raw.rename(columns={"TIME_PERIOD": "observed_at", "OBS_VALUE": "value"})
            frame = _monthly_last(frame[["observed_at", "value"]], indicator, "norges_bank")
            frames.append(frame)
            statuses.append(_status(f"norges_bank:{indicator.slug}", "ok", f"Fetched {indicator.name} from Norges Bank ({len(frame)} monthly rows)."))
        except Exception as exc:
            statuses.append(_status(f"norges_bank:{indicator.slug}", "failed", f"Could not fetch Norges Bank series {indicator.source_key}: {exc}"))
    return (pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()), statuses


def _fetch_ssb_cpi(indicators: Iterable[IndicatorDefinition], settings: Settings) -> tuple[pd.DataFrame, list[SourceStatus]]:
    frames = []
    statuses = []
    for indicator in indicators:
        try:
            query = {
                "query": [
                    {"code": "Konsumgrp", "selection": {"filter": "item", "values": ["TOTAL"]}},
                    {"code": "ContentsCode", "selection": {"filter": "item", "values": ["KpiIndMnd"]}},
                    {"code": "Tid", "selection": {"filter": "top", "values": ["72"]}},
                ],
                "response": {"format": "CSV"},
            }
            response = requests.post("https://data.ssb.no/api/v0/en/table/03013", json=query, timeout=(5, settings.request_timeout_seconds))
            response.raise_for_status()
            raw = pd.read_csv(StringIO(response.text))
            values = raw.iloc[0, 1:]
            rows = []
            for label, value in values.items():
                period = str(label).rsplit(" ", 1)[-1].replace("M", "-")
                rows.append({"observed_at": pd.Period(period, freq="M").to_timestamp("M").date().isoformat(), "value": float(value)})
            frame = _finalize_indicator_frame(pd.DataFrame(rows), indicator, "ssb")
            frames.append(frame)
            statuses.append(_status(f"ssb:{indicator.slug}", "ok", f"Fetched {indicator.name} from Statistics Norway table 03013 ({len(frame)} monthly rows)."))
        except Exception as exc:
            statuses.append(_status(f"ssb:{indicator.slug}", "failed", f"Could not fetch Statistics Norway CPI: {exc}"))
    return (pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()), statuses


def _fetch_yahoo_chart(indicators: Iterable[IndicatorDefinition], settings: Settings) -> tuple[pd.DataFrame, list[SourceStatus]]:
    frames = []
    statuses = []
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    for indicator in indicators:
        try:
            symbol = quote(indicator.source_key, safe="")
            response = session.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}", params={"range": "8y", "interval": "1mo"}, timeout=(5, settings.request_timeout_seconds))
            response.raise_for_status()
            result = response.json()["chart"]["result"][0]
            timestamps = result["timestamp"]
            closes = result["indicators"]["quote"][0]["close"]
            rows = [
                {"observed_at": pd.to_datetime(ts, unit="s").to_period("M").to_timestamp("M").date().isoformat(), "value": close}
                for ts, close in zip(timestamps, closes)
                if close is not None
            ]
            frame = _finalize_indicator_frame(pd.DataFrame(rows).tail(72), indicator, "yahoo_chart")
            if indicator.slug == "rates_pressure":
                frame["value"] = frame["value"] / 10.0
            frames.append(frame)
            statuses.append(_status(f"yahoo_chart:{indicator.slug}", "ok", f"Fetched {indicator.name} from Yahoo chart data ({len(frame)} monthly rows)."))
        except Exception as exc:
            statuses.append(_status(f"yahoo_chart:{indicator.slug}", "failed", f"Could not fetch Yahoo chart series {indicator.source_key}: {exc}"))
    return (pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()), statuses


def _wide_monthly_column(raw: pd.DataFrame, date_column: str, value_column: str, indicator: IndicatorDefinition, source: str) -> pd.DataFrame:
    frame = raw[[date_column, value_column]].rename(columns={date_column: "observed_at", value_column: "value"}).copy()
    frame["observed_at"] = frame["observed_at"].astype(str).str.replace("M", "-", regex=False)
    frame["observed_at"] = frame["observed_at"].map(lambda value: pd.Period(value, freq="M").to_timestamp("M").date().isoformat())
    return _finalize_indicator_frame(frame, indicator, source)


def _monthly_last(frame: pd.DataFrame, indicator: IndicatorDefinition, source: str) -> pd.DataFrame:
    frame = frame.copy()
    frame["observed_at"] = pd.to_datetime(frame["observed_at"], errors="coerce")
    frame["value"] = pd.to_numeric(frame["value"].replace("..", pd.NA), errors="coerce")
    frame = frame.dropna(subset=["observed_at", "value"]).set_index("observed_at")["value"].resample("ME").last().dropna().tail(72).reset_index()
    frame["observed_at"] = frame["observed_at"].dt.date.astype(str)
    return _finalize_indicator_frame(frame, indicator, source)


def _finalize_indicator_frame(frame: pd.DataFrame, indicator: IndicatorDefinition, source: str) -> pd.DataFrame:
    result = frame.copy()
    result["value"] = pd.to_numeric(result["value"].replace("…", pd.NA), errors="coerce")
    result["observed_at"] = pd.to_datetime(result["observed_at"], errors="coerce")
    result = result.dropna(subset=["observed_at", "value"]).sort_values("observed_at").tail(72)
    if result.empty:
        raise ValueError("No numeric observations.")
    result["indicator_slug"] = indicator.slug
    result["observed_at"] = result["observed_at"].dt.date.astype(str)
    result["source"] = source
    result["unit"] = indicator.unit
    return result[["indicator_slug", "observed_at", "value", "source", "unit"]]


def _fetch_fred_public_csv(indicators: Iterable[IndicatorDefinition], settings: Settings) -> tuple[pd.DataFrame, list[SourceStatus]]:
    indicator_list = list(indicators)
    if not indicator_list:
        return pd.DataFrame(), []

    statuses: list[SourceStatus] = []
    frames = []
    for indicator in indicator_list:
        raw, batch_error = _fetch_fred_batch([indicator], settings)
        if raw is None:
            statuses.append(_status(f"fred_public:{indicator.slug}", "failed", f"Could not fetch public FRED CSV: {batch_error}"))
            continue
        _append_fred_series(raw, indicator, frames, statuses)

    return (pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()), statuses


def _fetch_fred_batch(indicators: list[IndicatorDefinition], settings: Settings) -> tuple[pd.DataFrame | None, str | None]:
    session = requests.Session()
    session.headers.update({"User-Agent": "OsloCycleRadar/0.1 public data refresh"})
    try:
        response = session.get(
            "https://fred.stlouisfed.org/graph/fredgraph.csv",
            params={"id": ",".join(indicator.source_key for indicator in indicators)},
            timeout=(min(settings.request_timeout_seconds, 10), max(settings.request_timeout_seconds, 45)),
        )
        response.raise_for_status()
        return pd.read_csv(StringIO(response.text)), None
    except Exception as exc:
        return None, str(exc)


def _append_fred_series(raw: pd.DataFrame, indicator: IndicatorDefinition, frames: list[pd.DataFrame], statuses: list[SourceStatus]) -> None:
    try:
        series = _fred_csv_to_monthly_frame(raw, indicator)
        frames.append(series)
        statuses.append(_status(f"fred_public:{indicator.slug}", "ok", f"Fetched {indicator.name} from public FRED CSV ({len(series)} monthly rows)."))
    except Exception as exc:
        statuses.append(_status(f"fred_public:{indicator.slug}", "failed", f"Could not parse {indicator.name} from public FRED CSV: {exc}"))


def _fred_csv_to_monthly_frame(csv_data: str | pd.DataFrame, indicator: IndicatorDefinition, max_months: int = 72) -> pd.DataFrame:
    frame = pd.read_csv(StringIO(csv_data)) if isinstance(csv_data, str) else csv_data.copy()
    if frame.shape[1] < 2 or "observation_date" not in frame:
        raise ValueError("FRED CSV did not include observation_date and value columns.")
    value_column = indicator.source_key
    if value_column not in frame.columns:
        raise ValueError(f"FRED CSV did not include {value_column}.")
    frame = frame.rename(columns={"observation_date": "observed_at", value_column: "value"})
    frame["observed_at"] = pd.to_datetime(frame["observed_at"], errors="coerce")
    frame["value"] = pd.to_numeric(frame["value"].replace(".", pd.NA), errors="coerce")
    frame = frame.dropna(subset=["observed_at", "value"]).sort_values("observed_at")
    if frame.empty:
        raise ValueError("FRED CSV contained no numeric observations.")
    monthly = frame.set_index("observed_at")["value"].resample("ME").last().dropna().tail(max_months).reset_index()
    monthly["indicator_slug"] = indicator.slug
    monthly["observed_at"] = monthly["observed_at"].dt.date.astype(str)
    monthly["source"] = "fred_public"
    monthly["unit"] = indicator.unit
    return monthly[["indicator_slug", "observed_at", "value", "source", "unit"]]


def _derive_public_indicators(indicators: Iterable[IndicatorDefinition], observations: pd.DataFrame, settings: Settings) -> tuple[pd.DataFrame, list[SourceStatus]]:
    rows: list[pd.DataFrame] = []
    statuses: list[SourceStatus] = []
    if observations.empty:
        return pd.DataFrame(), [_status("derived_public", "failed", "No public source observations available for derived indicators.")]

    wide = observations.copy()
    wide["observed_at"] = pd.to_datetime(wide["observed_at"], errors="coerce")
    wide = wide.dropna(subset=["observed_at"]).pivot_table(index="observed_at", columns="indicator_slug", values="value", aggfunc="last").sort_index()

    for indicator in indicators:
        try:
            if indicator.slug == "eur_nok":
                series = (wide["usd_nok"] * wide["EXUSEU"]) if "EXUSEU" in wide else None
                if series is None:
                    usd_eur = _extra_public_series("EXUSEU", settings_timeout=settings.request_timeout_seconds)
                    series = wide["usd_nok"].mul(usd_eur, axis=0)
                rows.append(_derived_series_frame(indicator, series, "fred_public_derived"))
                statuses.append(_status("derived_public:eur_nok", "ok", "Derived EUR/NOK from public USD/NOK and USD/EUR FRED series."))
            elif indicator.slug == "oil_curve_pressure":
                series = wide["brent"] - wide["wti"]
                rows.append(_derived_series_frame(indicator, series, "public_derived"))
                statuses.append(_status("derived_public:oil_curve_pressure", "ok", "Derived Brent-WTI spread from public Brent and WTI series."))
        except Exception as exc:
            statuses.append(_status(f"derived_public:{indicator.slug}", "failed", f"Could not derive {indicator.name}: {exc}"))

    return (pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()), statuses


def _extra_public_series(series_id: str, settings_timeout: int) -> pd.Series:
    response = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv", params={"id": series_id}, timeout=settings_timeout)
    response.raise_for_status()
    frame = pd.read_csv(StringIO(response.text))
    value_column = [column for column in frame.columns if column != "observation_date"][0]
    frame["observed_at"] = pd.to_datetime(frame["observation_date"], errors="coerce")
    frame["value"] = pd.to_numeric(frame[value_column].replace(".", pd.NA), errors="coerce")
    frame = frame.dropna(subset=["observed_at", "value"]).set_index("observed_at")["value"].resample("ME").last().dropna()
    return frame


def _derived_series_frame(indicator: IndicatorDefinition, series: pd.Series, source: str) -> pd.DataFrame:
    series = series.dropna().tail(96)
    if series.empty:
        raise ValueError("Derived series had no overlapping numeric observations.")
    frame = series.reset_index()
    frame.columns = ["observed_at", "value"]
    frame["indicator_slug"] = indicator.slug
    frame["observed_at"] = pd.to_datetime(frame["observed_at"]).dt.date.astype(str)
    frame["source"] = source
    frame["unit"] = indicator.unit
    return frame[["indicator_slug", "observed_at", "value", "source", "unit"]]


def _theme_sentiment(theme: str, text: str) -> float:
    positive_words = ("recover", "improve", "growth", "tailwind", "easing", "resilient", "support")
    negative_words = ("risk", "recession", "tight", "inflation", "weak", "slowdown", "stress")
    window_bonus = 0.05 if theme in text else 0.0
    positive = sum(word in text for word in positive_words)
    negative = sum(word in text for word in negative_words)
    return max(min((positive - negative) * 0.08 + window_bonus, 1.0), -1.0)


def _status(source_slug: str, status: str, message: str) -> SourceStatus:
    return SourceStatus(source_slug, status, message, datetime.now(timezone.utc).isoformat(timespec="seconds"))
