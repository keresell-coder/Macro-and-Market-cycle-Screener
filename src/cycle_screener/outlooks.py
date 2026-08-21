from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

from .config import Settings
from .connectors import SourceStatus


OUTLOOK_COLUMNS = (
    "outlook_id",
    "institution",
    "institution_type",
    "title",
    "published_at",
    "horizon",
    "growth_bias",
    "inflation_bias",
    "policy_bias",
    "market_bias",
    "key_themes",
    "risks",
    "summary",
    "source_url",
    "source_tier",
    "review_status",
    "captured_at",
)

OFFICIAL_DOMAINS = {
    "bis.org",
    "blackrock.com",
    "goldmansachs.com",
    "imf.org",
    "jpmorgan.com",
    "morganstanley.com",
    "oecd.org",
    "vanguard.com",
    "worldbank.org",
}

BIAS_VALUES = {"positive", "neutral", "negative", "mixed", "not_stated"}
TIER_VALUES = {"multilateral_primary", "central_bank_primary", "institution_primary"}


def load_institutional_outlooks(settings: Settings) -> tuple[pd.DataFrame, list[SourceStatus]]:
    path = settings.public_research_evidence_dir / "institutional_outlooks.csv"
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if not path.exists():
        return _empty_frame(), [SourceStatus("institutional_outlooks", "missing", f"Missing reviewed outlook file: {path}", now)]

    frame = pd.read_csv(path, dtype=str).fillna("")
    missing = [column for column in OUTLOOK_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Institutional outlook file is missing columns: {', '.join(missing)}")
    frame = frame[list(OUTLOOK_COLUMNS)].copy()
    _validate(frame, path)
    frame["published_at"] = pd.to_datetime(frame["published_at"], errors="raise").dt.date.astype(str)
    frame["captured_at"] = pd.to_datetime(frame["captured_at"], errors="raise", utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    frame = frame.sort_values(["published_at", "institution", "outlook_id"], ascending=[False, True, True]).reset_index(drop=True)
    return frame, [SourceStatus("institutional_outlooks", "ok", f"Loaded {len(frame)} reviewed official outlook records; non-scoring by policy.", now)]


def outlook_summary(frame: pd.DataFrame) -> dict[str, object]:
    if frame.empty:
        return {
            "policy": "reviewed_non_scoring_context",
            "record_count": 0,
            "institution_count": 0,
            "latest_published_at": "",
            "consensus": {},
            "dispersion": {},
            "timeline": [],
        }

    reviewed = frame[frame["review_status"].str.lower() == "reviewed"].copy()
    latest = reviewed.sort_values("published_at").groupby("institution", as_index=False).tail(1)
    dimensions = ("growth_bias", "inflation_bias", "policy_bias", "market_bias")
    consensus: dict[str, str] = {}
    dispersion: dict[str, dict[str, int]] = {}
    for dimension in dimensions:
        counts = latest[dimension].value_counts().to_dict()
        dispersion[dimension] = {str(key): int(value) for key, value in sorted(counts.items())}
        consensus[dimension] = str(latest[dimension].mode().iloc[0]) if not latest.empty else "not_stated"

    records = []
    for _, row in reviewed.sort_values("published_at", ascending=False).iterrows():
        records.append({column: str(row[column]) for column in OUTLOOK_COLUMNS})
    return {
        "policy": "reviewed_official_sources_non_scoring_context",
        "reliability_note": "Multilateral and BIS publications are primary macro-policy sources; bank and asset-manager outlooks are attributed house views. Agreement is context, not independent scientific validation or a return forecast.",
        "record_count": int(len(reviewed)),
        "institution_count": int(reviewed["institution"].nunique()),
        "latest_published_at": str(reviewed["published_at"].max()),
        "consensus": consensus,
        "dispersion": dispersion,
        "timeline": records,
    }


def _validate(frame: pd.DataFrame, path: Path) -> None:
    if frame["outlook_id"].eq("").any() or frame["outlook_id"].duplicated().any():
        raise ValueError(f"Outlook IDs must be non-empty and unique: {path}")
    if not frame["review_status"].str.lower().eq("reviewed").all():
        raise ValueError(f"Only reviewed outlooks may be published: {path}")
    if not frame["source_tier"].isin(TIER_VALUES).all():
        raise ValueError(f"Outlook source_tier must use the governed tier vocabulary: {path}")
    for column in ("growth_bias", "inflation_bias", "policy_bias", "market_bias"):
        if not frame[column].isin(BIAS_VALUES).all():
            raise ValueError(f"Invalid {column} value in {path}")
    invalid_urls = []
    for value in frame["source_url"]:
        parsed = urlparse(value)
        host = parsed.netloc.lower().removeprefix("www.")
        if parsed.scheme != "https" or not any(host == domain or host.endswith(f".{domain}") for domain in OFFICIAL_DOMAINS):
            invalid_urls.append(value)
    if invalid_urls:
        raise ValueError(f"Outlook URLs must use approved official domains: {invalid_urls}")


def _empty_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=list(OUTLOOK_COLUMNS))
