from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


def _project_root() -> Path:
    configured = os.getenv("CYCLE_RADAR_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()

    cwd = Path.cwd().resolve()
    if (cwd / "pyproject.toml").exists() and (cwd / "src" / "cycle_screener").exists():
        return cwd

    source_root = Path(__file__).resolve().parents[2]
    if (source_root / "pyproject.toml").exists():
        return source_root

    return cwd


ROOT = _project_root()
DATA_DIR = ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
EXPORT_DIR = ROOT / "exports"
MANUAL_REPORT_DIR = DATA_DIR / "manual_reports"
RESEARCH_EVIDENCE_DIR = DATA_DIR / "research_evidence"


@dataclass(frozen=True)
class Settings:
    database_path: Path = CACHE_DIR / "cycle_radar.duckdb"
    research_evidence_dir: Path = RESEARCH_EVIDENCE_DIR
    fred_api_key: str | None = os.getenv("FRED_API_KEY")
    eia_api_key: str | None = os.getenv("EIA_API_KEY")
    request_timeout_seconds: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "20"))


def ensure_directories() -> None:
    for path in [DATA_DIR, CACHE_DIR, EXPORT_DIR, MANUAL_REPORT_DIR, RESEARCH_EVIDENCE_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    ensure_directories()
    return Settings()
