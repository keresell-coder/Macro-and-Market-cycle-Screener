from __future__ import annotations

from pathlib import Path


PUBLIC_EXPORT_ALLOWLIST = (
    Path("exports/opportunity_radar.html"),
    Path("exports/site"),
    Path("exports/public"),
)

PRIVATE_PATH_PARTS = {
    ".env",
    "cache",
    "manual_reports",
    "private_notes",
    "raw_licensed",
    "research_evidence",
}


def is_public_export_path(path: str | Path) -> bool:
    candidate = Path(path)
    parts = set(candidate.parts)
    if parts & PRIVATE_PATH_PARTS:
        return False
    return any(candidate == allowed or candidate.is_relative_to(allowed) for allowed in PUBLIC_EXPORT_ALLOWLIST)
