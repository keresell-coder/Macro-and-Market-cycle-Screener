from __future__ import annotations

import os

import pandas as pd

from cycle_screener.connectors import _dbnomics_series_to_monthly_frame, _derive_public_indicators, _fred_csv_to_monthly_frame
from cycle_screener.config import _load_dotenv_file
from cycle_screener.config import Settings
from cycle_screener.indicators import IndicatorDefinition
from cycle_screener.publication import is_public_export_path
from cycle_screener.research import load_research_evidence
from cycle_screener.config import get_settings
from cycle_screener.refresh import refresh
from cycle_screener.storage import RadarStore


def test_sample_refresh_persists_scores() -> None:
    result = refresh(sample=True)
    store = RadarStore(get_settings().database_path)
    scores = store.table("subsector_scores")
    statuses = store.table("source_status")
    store.close()

    assert result["scores"] == len(scores)
    assert not scores.empty
    assert not statuses.empty


def test_fred_public_csv_parser_returns_monthly_observations() -> None:
    indicator = IndicatorDefinition("brent", "Brent", "fred_public", "DCOILBRENTEU", "USD/bbl", "mixed", "Oil proxy")
    frame = _fred_csv_to_monthly_frame(
        "observation_date,DCOILBRENTEU\n2026-01-02,75.1\n2026-01-31,77.4\n2026-02-01,.\n2026-02-27,79.2\n",
        indicator,
    )

    assert frame["indicator_slug"].tolist() == ["brent", "brent"]
    assert frame["observed_at"].tolist() == ["2026-01-31", "2026-02-28"]
    assert frame["value"].tolist() == [77.4, 79.2]
    assert set(frame["source"]) == {"fred_public"}


def test_dbnomics_oecd_cli_parser_returns_monthly_observations() -> None:
    indicator = IndicatorDefinition("g20_cli", "G20 OECD CLI", "dbnomics_oecd_cli", "G20.M.LI...AA...H", "index", "higher_tailwind", "CLI")
    payload = {
        "series": {
            "docs": [
                {
                    "period": ["2026-01", "2026-02", "2026-03"],
                    "value": [100.42, None, 100.58],
                }
            ]
        }
    }

    frame = _dbnomics_series_to_monthly_frame(payload, indicator)

    assert frame["indicator_slug"].tolist() == ["g20_cli", "g20_cli"]
    assert frame["observed_at"].tolist() == ["2026-01-31", "2026-03-31"]
    assert frame["value"].tolist() == [100.42, 100.58]
    assert set(frame["source"]) == {"dbnomics_oecd_cli"}


def test_public_derived_indicators_use_fetched_series() -> None:
    observations = pd.DataFrame(
        [
            {"indicator_slug": "brent", "observed_at": "2026-01-31", "value": 80.0},
            {"indicator_slug": "wti", "observed_at": "2026-01-31", "value": 75.0},
        ]
    )
    indicator = IndicatorDefinition("oil_curve_pressure", "Oil spread", "derived_public", "DCOILBRENTEU-DCOILWTICO", "USD/bbl", "higher_tailwind", "Oil spread")

    frame, statuses = _derive_public_indicators([indicator], observations, Settings())

    assert frame["indicator_slug"].tolist() == ["oil_curve_pressure"]
    assert frame["value"].tolist() == [5.0]
    assert statuses[0].status == "ok"


def test_sample_refresh_persists_research_evidence() -> None:
    result = refresh(sample=True)
    store = RadarStore(get_settings().database_path)
    profiles = store.table("subsector_research_profiles")
    facts = store.table("research_facts")
    market_cycle = store.table("subsector_market_cycle")
    scores = store.table("subsector_scores")
    store.close()

    assert result["research_profiles"] == len(profiles)
    assert result["research_facts"] == len(facts)
    assert result["market_cycle"] == len(market_cycle)
    assert set(scores["slug"]).issubset(set(profiles["subsector_slug"]))
    assert {"reviewed", "unreviewed"}.issubset(set(facts["review_status"]))
    assert facts["confidence"].between(0, 1).all()
    assert not market_cycle.empty
    assert {"price_index", "benchmark_index", "relative_price_index", "valuation_proxy"}.issubset(market_cycle.columns)


def test_structured_research_evidence_ingestion_sanitizes_rows(tmp_path) -> None:
    evidence_dir = tmp_path / "research_evidence"
    evidence_dir.mkdir()
    pd.DataFrame(
        [
            {
                "subsector_slug": "oil_services",
                "theme": "catalyst",
                "claim": "Backlog commentary is a catalyst to review, not a score input.",
                "source_name": "Public filing",
                "source_url": "https://example.com/filing",
                "source_quality": "official",
                "confidence": 1.4,
                "review_status": "draft",
            },
            {
                "subsector_slug": "not_a_subsector",
                "theme": "risk",
                "claim": "This invalid subsector should be dropped.",
                "source_name": "Unknown",
            },
        ]
    ).to_csv(evidence_dir / "research_facts.csv", index=False)
    pd.DataFrame(
        [
            {
                "subsector_slug": "oil_services",
                "scope": "Oil-services research profile.",
                "why_now": "Orders and margins are the watch items.",
                "review_status": "reviewed",
            }
        ]
    ).to_csv(evidence_dir / "subsector_research_profiles.csv", index=False)

    settings = Settings(database_path=tmp_path / "radar.duckdb", research_evidence_dir=evidence_dir)
    profiles, facts, statuses = load_research_evidence(settings, sample=False)

    assert len(profiles) == 1
    assert len(facts) == 1
    assert facts["subsector_slug"].iloc[0] == "oil_services"
    assert facts["confidence"].iloc[0] == 1.0
    assert facts["review_status"].iloc[0] == "unreviewed"
    assert statuses[0].status == "ok"


def test_public_export_allowlist_blocks_private_paths() -> None:
    assert is_public_export_path("exports/opportunity_radar.html")
    assert is_public_export_path("exports/site/index.html")
    assert is_public_export_path("exports/public/data/latest.json")
    assert not is_public_export_path("data/cache/cycle_radar.duckdb")
    assert not is_public_export_path("data/manual_reports/report.pdf")
    assert not is_public_export_path("data/private_notes/thesis.md")
    assert not is_public_export_path("data/raw_licensed/vendor.csv")
    assert not is_public_export_path("data/research_evidence/research_facts.csv")


def test_local_dotenv_loader_preserves_existing_environment(tmp_path, monkeypatch) -> None:
    dotenv = tmp_path / ".env"
    dotenv.write_text(
        "FRED_API_KEY=from_file\n"
        "EIA_API_KEY='quoted_eia_key'\n"
        "REQUEST_TIMEOUT_SECONDS=30\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("FRED_API_KEY", "from_environment")
    monkeypatch.delenv("EIA_API_KEY", raising=False)
    monkeypatch.delenv("REQUEST_TIMEOUT_SECONDS", raising=False)

    _load_dotenv_file(dotenv)

    assert os.environ["FRED_API_KEY"] == "from_environment"
    assert os.environ["EIA_API_KEY"] == "quoted_eia_key"
    assert os.environ["REQUEST_TIMEOUT_SECONDS"] == "30"
