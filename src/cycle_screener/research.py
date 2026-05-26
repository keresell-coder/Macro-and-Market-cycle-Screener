from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .config import Settings
from .sample_data import generate_sample_research_facts, generate_sample_research_profiles
from .taxonomy import subsector_by_slug


PROFILE_COLUMNS = [
    "subsector_slug",
    "scope",
    "cycle_conclusion",
    "current_phase_hypothesis",
    "valuation_context",
    "market_cycle_watch",
    "why_now",
    "key_debates",
    "catalysts",
    "risks",
    "review_status",
    "updated_at",
]

FACT_COLUMNS = [
    "fact_id",
    "subsector_slug",
    "theme",
    "claim",
    "source_name",
    "source_url",
    "source_type",
    "source_quality",
    "source_date",
    "captured_at",
    "confidence",
    "review_status",
    "evidence_scope",
]

REVIEW_STATUSES = {"reviewed", "unreviewed", "needs_review"}
SOURCE_QUALITIES = {
    "official",
    "exchange_regulator",
    "public_institution",
    "industry_body",
    "reputable_research",
    "public_limited",
    "manual_public",
    "sample",
}


@dataclass(frozen=True)
class ResearchIngestionStatus:
    source_slug: str
    status: str
    message: str
    checked_at: str


def load_research_evidence(settings: Settings, sample: bool = False) -> tuple[pd.DataFrame, pd.DataFrame, list[ResearchIngestionStatus]]:
    """Load structured research evidence.

    This path intentionally ingests rows as data. Claims from public/manual files
    are never interpreted as dashboard instructions and never affect scores.
    """
    if sample:
        return (
            generate_sample_research_profiles(),
            generate_sample_research_facts(),
            [_status("sample_research_evidence", "ok", "Loaded deterministic sample research profiles and source-backed facts.")],
        )

    public_profiles_path = settings.public_research_evidence_dir / "subsector_research_profiles.csv"
    public_facts_path = settings.public_research_evidence_dir / "research_facts.csv"
    local_profiles_path = settings.research_evidence_dir / "subsector_research_profiles.csv"
    local_facts_path = settings.research_evidence_dir / "research_facts.csv"
    statuses: list[ResearchIngestionStatus] = []

    public_profiles = _read_optional_csv(public_profiles_path, PROFILE_COLUMNS)
    public_facts = _read_optional_csv(public_facts_path, FACT_COLUMNS)
    local_profiles = _read_optional_csv(local_profiles_path, PROFILE_COLUMNS)
    local_facts = _read_optional_csv(local_facts_path, FACT_COLUMNS)

    profiles = pd.concat([public_profiles, local_profiles], ignore_index=True)
    facts = pd.concat([local_facts, public_facts], ignore_index=True)

    if profiles.empty and facts.empty:
        statuses.append(
            _status(
                "research_evidence_fallback",
                "degraded",
                "No structured public/manual research evidence files found; used sample evidence.",
            )
        )
        return generate_sample_research_profiles(), generate_sample_research_facts(), statuses

    profiles = _clean_profiles(profiles)
    facts = _clean_facts(facts)
    statuses.append(
        _status(
            "research_evidence_files",
            "ok",
            "Ingested "
            f"{len(public_profiles)} public-reviewed profiles, {len(public_facts)} public-reviewed claim rows, "
            f"{len(local_profiles)} local profiles, and {len(local_facts)} local claim rows from structured CSV evidence files.",
        )
    )
    return profiles, facts, statuses


def _read_optional_csv(path: Path, columns: list[str]) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=columns)
    frame = pd.read_csv(path)
    for column in columns:
        if column not in frame:
            frame[column] = ""
    return frame[columns]


def _clean_profiles(profiles: pd.DataFrame) -> pd.DataFrame:
    if profiles.empty:
        return pd.DataFrame(columns=PROFILE_COLUMNS)

    valid_slugs = set(subsector_by_slug())
    frame = profiles.copy()
    frame["subsector_slug"] = frame["subsector_slug"].astype(str).str.strip()
    frame = frame[frame["subsector_slug"].isin(valid_slugs)]
    for column in PROFILE_COLUMNS:
        frame[column] = frame[column].fillna("").astype(str)
    frame["review_status"] = frame["review_status"].str.lower().where(frame["review_status"].str.lower().isin(REVIEW_STATUSES), "unreviewed")
    frame["updated_at"] = frame["updated_at"].where(frame["updated_at"].str.len() > 0, _now())
    return frame.drop_duplicates(subset=["subsector_slug"], keep="last").reset_index(drop=True)


def _clean_facts(facts: pd.DataFrame) -> pd.DataFrame:
    if facts.empty:
        return pd.DataFrame(columns=FACT_COLUMNS)

    valid_slugs = set(subsector_by_slug())
    frame = facts.copy()
    frame["subsector_slug"] = frame["subsector_slug"].astype(str).str.strip()
    frame = frame[frame["subsector_slug"].isin(valid_slugs)]
    frame = frame[frame["claim"].fillna("").astype(str).str.strip().ne("")]
    frame = frame[frame["source_name"].fillna("").astype(str).str.strip().ne("")]

    for column in FACT_COLUMNS:
        if column != "confidence":
            frame[column] = frame[column].fillna("").astype(str)
    frame["confidence"] = pd.to_numeric(frame["confidence"], errors="coerce").fillna(0.5).clip(0.0, 1.0)
    frame["review_status"] = frame["review_status"].str.lower().where(frame["review_status"].str.lower().isin(REVIEW_STATUSES), "unreviewed")
    frame["source_quality"] = frame["source_quality"].str.lower().where(frame["source_quality"].str.lower().isin(SOURCE_QUALITIES), "manual_public")
    frame["evidence_scope"] = frame["evidence_scope"].str.lower().where(frame["evidence_scope"].str.lower().isin({"public", "manual_public"}), "manual_public")
    frame["captured_at"] = frame["captured_at"].where(frame["captured_at"].str.len() > 0, _now())
    frame["fact_id"] = frame["fact_id"].where(
        frame["fact_id"].str.len() > 0,
        frame["subsector_slug"] + "-" + frame.index.astype(str),
    )
    return frame[FACT_COLUMNS].drop_duplicates(subset=["fact_id"], keep="last").reset_index(drop=True)


def _status(source_slug: str, status: str, message: str) -> ResearchIngestionStatus:
    return ResearchIngestionStatus(source_slug, status, message, _now())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
