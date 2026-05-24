from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from cycle_screener.build_static_site import assert_no_numeric_sample_fallback
from cycle_screener.build_static_site import build_static_site
from cycle_screener.change_tracking import compare_report_states
from cycle_screener.refresh import refresh
from cycle_screener.report_state import build_report_state
from cycle_screener.sample_data import (
    generate_sample_market_cycle,
    generate_sample_observations,
    generate_sample_research_facts,
    generate_sample_research_mentions,
    generate_sample_research_profiles,
)
from cycle_screener.scoring import calculate_scores
from cycle_screener.static_site_qa import run_static_site_qa
from cycle_screener.storage import RadarStore


def test_report_state_contains_public_safe_snapshot() -> None:
    refresh(sample=True)
    state = build_report_state()

    assert state["schema_version"]
    assert state["data_as_of"]
    assert state["subsectors"]
    assert state["source_status"]
    assert state["source_freshness"]
    assert state["source_health"]
    assert state["chart_layer"]
    assert state["chart_layer"]["version"] == "sprint9-historical-chart-layer"
    assert state["chart_layer"]["views"][0]["view_id"] == "global"
    assert state["chart_layer"]["views"][0]["series"]
    assert any(view["view_id"] == "norway_oslo" for view in state["chart_layer"]["views"])
    assert any(sector["subsectors"] for sector in state["chart_layer"]["sector_views"])
    assert "contradicting_evidence" in state
    assert state["research_facts"]
    assert state["methodology"]["scoring_version"]
    assert state["methodology"]["framework_reference"].endswith("global_macro_market_cycle_knowledge_base.md")
    assert "credit" in state["methodology"]["framework_coverage"].lower()
    assert state["framework_coverage"]
    assert any(item["dimension"] == "Liquidity and credit" and item["status"] == "missing" for item in state["framework_coverage"])
    assert any(
        item["indicator_slug"] == "global_pmi"
        and item["display_slug"] == "global_growth_proxy"
        and "GDP growth" in item["indicator_name"]
        for item in state["source_freshness"]
    )
    assert any(item["dimension"] == "Growth" and item["status"] == "partial" for item in state["framework_coverage"])
    assert any(item["dimension"] == "Historical chart layer" and item["status"] == "partial" for item in state["framework_coverage"])
    assert any(item["indicator_slug"] == "g20_cli" and "OECD CLI" in item["indicator_name"] for item in state["source_freshness"])
    global_series = state["chart_layer"]["views"][0]["series"][0]
    assert {"source", "latest_observed_at", "frequency", "data_class", "proxy_status", "scoring_inclusion"}.issubset(global_series)

    first = state["subsectors"][0]
    assert {"slug", "rank", "opportunity_score", "signals", "market_cycle", "reviewed_public_fact_ids"}.issubset(first)
    assert "relative_price_index" in first["market_cycle"]
    assert all(fact["source_url"] for fact in state["research_facts"])
    assert state["source_health"]["numeric"]["sample_build_indicator_count"] == len(state["source_freshness"])


def test_compare_report_states_tracks_core_deltas() -> None:
    previous = _state_fixture()
    current = _state_fixture()
    current["subsectors"][0]["rank"] = 2
    current["subsectors"][0]["opportunity_score"] = 57.5
    current["subsectors"][0]["signals"]["recovery_potential"] = 0.35
    current["subsectors"][0]["market_cycle"]["relative_price_index"] = 109.0
    current["source_status"][0]["status"] = "failed"
    current["research_facts"][0]["confidence"] = 0.9
    current["research_facts"].append(
        {
            "fact_id": "oil_services-new",
            "subsector_slug": "oil_services",
            "theme": "catalyst",
            "claim": "New public catalyst.",
            "source_name": "Public source",
            "source_url": "https://example.com/new",
            "source_quality": "official",
            "source_date": "2026-05-23",
            "captured_at": "2026-05-23",
            "confidence": 0.7,
        }
    )

    changes = compare_report_states(previous, current)
    subsector_change = changes["subsector_changes"][0]

    assert subsector_change["rank_delta"] == -1
    assert subsector_change["score_delta"] == 5.5
    assert subsector_change["score_move"] == "major"
    assert subsector_change["signal_delta"]["recovery_potential"] == 0.25
    assert subsector_change["market_cycle_delta"]["relative_price_index"] == 9.0
    assert changes["source_status_changes"][0]["status_delta"] == "ok -> failed"
    assert len(changes["research_fact_changes"]["new"]) == 1
    assert len(changes["research_fact_changes"]["changed"]) == 1


def test_build_static_site_writes_report_json(tmp_path) -> None:
    refresh(sample=True)
    previous = _state_fixture()
    previous_path = tmp_path / "previous_report_state.json"
    previous_path.write_text(json.dumps(previous), encoding="utf-8")

    result = build_static_site(sample=False, previous=previous_path)

    assert result["report_state"].endswith("report_state.json")
    assert result["latest"].endswith("latest.json")
    assert result["changes"].endswith("changes.json")
    assert result["site_index"].endswith("index.html")
    assert result["weekly_report"].endswith(".html")

    site_index = Path(result["site_index"])
    site_html = site_index.read_text(encoding="utf-8")
    assert "Historical Charts" in site_html
    assert "Global View And Drilldown" in site_html
    assert "Regional Drilldown" in site_html
    assert "Sector And Subsector Drilldown" in site_html
    assert "sample-backed market-cycle proxy history" in site_html
    assert "Latest Radar" in site_html
    assert "Source Health" in site_html
    assert "Freshness And Fallbacks" in site_html
    assert "Contradicting Evidence" in site_html
    assert "Scoring version" in site_html
    assert "Framework coverage" in site_html
    assert "Changes Since Last Report" in site_html
    assert "Archive" in site_html
    assert "Methodology" in site_html
    assert (site_index.parent / "data" / "latest.json").exists()
    assert (site_index.parent / "data" / "changes.json").exists()
    assert Path(result["weekly_report"]).exists()


def test_numeric_sample_fallback_is_visible_and_can_fail_live_build(tmp_path) -> None:
    store = RadarStore(tmp_path / "radar.duckdb")
    observations = generate_sample_observations()
    observations["source"] = "world_bank_commodity"
    observations.loc[observations["indicator_slug"] == "brent", "source"] = "sample_fallback"
    research_mentions = generate_sample_research_mentions()
    scores = calculate_scores(observations, research_mentions)
    now = "2026-05-24T08:00:00+00:00"

    store.replace_table("observations", observations)
    store.replace_table("research_mentions", research_mentions)
    store.replace_table("subsector_research_profiles", generate_sample_research_profiles())
    store.replace_table("research_facts", generate_sample_research_facts())
    store.replace_table("subsector_market_cycle", generate_sample_market_cycle())
    store.replace_table(
        "source_status",
        pd.DataFrame(
            [
                {
                    "source_slug": "fallback",
                    "status": "degraded",
                    "message": "Filled missing live indicators from sample data: brent.",
                    "checked_at": now,
                }
            ]
        ),
    )
    store.replace_table("subsector_scores", scores)

    state = build_report_state(store=store)
    store.close()

    numeric = state["source_health"]["numeric"]
    assert numeric["sample_fallback_indicator_count"] == 1
    assert numeric["sample_fallback_indicators"] == ["brent"]
    assert any(item["indicator_slug"] == "brent" and item["has_sample_fallback"] for item in state["source_freshness"])

    try:
        assert_no_numeric_sample_fallback(state)
    except RuntimeError as exc:
        assert "brent" in str(exc)
    else:
        raise AssertionError("Live numeric sample fallback should fail the strict build guard.")


def test_static_site_qa_serves_generated_site() -> None:
    refresh(sample=True)
    result = build_static_site(sample=False)

    qa_result = run_static_site_qa(Path(result["site_index"]).parent)

    assert qa_result["required_text_count"] >= 5
    assert qa_result["checked_url"].endswith("/index.html")
    assert qa_result["browser_screenshot"]["status"] in {"captured", "skipped"}


def _state_fixture() -> dict:
    return {
        "generated_at": "2026-05-16T08:00:00+00:00",
        "subsectors": [
            {
                "slug": "oil_services",
                "name": "Oil services",
                "rank": 1,
                "opportunity_score": 52.0,
                "signals": {
                    "recovery_potential": 0.1,
                    "valuation_proxy": 0.2,
                    "momentum": 0.0,
                    "macro_tailwind": 0.0,
                    "narrative_divergence": 0.0,
                    "confidence": 0.7,
                },
                "market_cycle": {
                    "relative_price_index": 100.0,
                    "valuation_proxy": 95.0,
                    "driver_pressure": 0.1,
                },
            }
        ],
        "source_status": [
            {
                "source_slug": "fred",
                "status": "ok",
                "message": "Fetched data.",
                "checked_at": "2026-05-16T08:00:00+00:00",
            }
        ],
        "research_facts": [
            {
                "fact_id": "oil_services-source-1",
                "subsector_slug": "oil_services",
                "theme": "macro_driver",
                "claim": "Public source claim.",
                "source_name": "Public source",
                "source_url": "https://example.com",
                "source_quality": "official",
                "source_date": "2026-05-16",
                "captured_at": "2026-05-16",
                "confidence": 0.8,
            }
        ],
    }
