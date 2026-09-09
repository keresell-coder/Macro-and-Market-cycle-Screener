from __future__ import annotations

import argparse
import dataclasses
from datetime import datetime, timezone

import pandas as pd

from .config import get_settings
from .connectors import SourceStatus, fetch_indicator_observations, fetch_research_mentions
from .research import load_research_evidence
from .outlooks import load_institutional_outlooks
from .sample_data import generate_sample_market_cycle
from .scoring import calculate_scores
from .storage import RadarStore


def refresh(sample: bool = False) -> dict[str, int | str]:
    settings = get_settings()
    store = RadarStore(settings.database_path)
    observations, indicator_status = fetch_indicator_observations(settings, sample=sample)
    research_mentions, research_status = fetch_research_mentions(settings, sample=sample)
    research_profiles, research_facts, evidence_status = load_research_evidence(settings, sample=sample)
    institutional_outlooks, outlook_status = load_institutional_outlooks(settings)
    if sample:
        market_cycle = generate_sample_market_cycle()
    else:
        market_cycle = pd.DataFrame(
            columns=[
                "subsector_slug", "observed_at", "price_index", "benchmark_index",
                "relative_price_index", "valuation_proxy", "driver_pressure", "source", "notes",
            ]
        )
        indicator_status.append(
            SourceStatus(
                source_slug="subsector_market_cycle",
                status="missing",
                message="No validated direct subsector market-cycle feed is configured; sample histories are excluded from live builds.",
                checked_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            )
        )
    scores = calculate_scores(observations, research_mentions, sample=sample)

    statuses = [dataclasses.asdict(status) for status in [*indicator_status, *research_status, *evidence_status, *outlook_status]]
    store.replace_table("observations", observations)
    store.replace_table("research_mentions", research_mentions)
    store.replace_table("subsector_research_profiles", research_profiles)
    store.replace_table("research_facts", research_facts)
    store.replace_table("institutional_outlooks", institutional_outlooks)
    store.replace_table("subsector_market_cycle", market_cycle)
    store.replace_table("source_status", pd.DataFrame(statuses))
    store.replace_table("subsector_scores", scores)
    backend = store.backend
    store.close()
    return {
        "observations": len(observations),
        "research_mentions": len(research_mentions),
        "research_profiles": len(research_profiles),
        "research_facts": len(research_facts),
        "institutional_outlooks": len(institutional_outlooks),
        "market_cycle": len(market_cycle),
        "scores": len(scores),
        "backend": backend,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh global macro, market and sector-cycle screener data.")
    parser.add_argument("--sample", action="store_true", help="Use deterministic sample data only.")
    args = parser.parse_args()
    result = refresh(sample=args.sample)
    print(
        "Refresh complete: "
        f"{result['observations']} observations, "
        f"{result['research_mentions']} research mentions, "
        f"{result['research_profiles']} research profiles, "
        f"{result['research_facts']} research facts, "
        f"{result['institutional_outlooks']} institutional outlooks, "
        f"{result['market_cycle']} market-cycle rows, "
        f"{result['scores']} subsector scores "
        f"({result['backend']})."
    )


if __name__ == "__main__":
    main()
