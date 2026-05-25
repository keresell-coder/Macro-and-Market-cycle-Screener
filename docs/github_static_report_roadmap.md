# GitHub Static Report Roadmap

Last updated: 2026-05-25

## Purpose

Use GitHub Actions and GitHub Pages to publish a recurring static report that answers:

> What is the current macro/market-cycle state, what is changing, and which Oslo-linked subsectors deserve further work?

GitHub Pages remains a static HTML/JSON target. It must not host Streamlit, databases, credentials, private notes, manual reports, raw licensed data, or unpublished research.

## Current Workflow

- Workflow: `.github/workflows/weekly-report.yml`
- Schedule: Saturday 07:15 UTC
- Manual dispatch: `live` or `sample`
- Default scheduled mode: `live`
- Strict live guard: fail if numeric `sample_fallback` appears
- Published directory: `exports/site/`
- Public URL: `https://keresell-coder.github.io/Macro-and-Market-cycle-Screener/`

Latest verified published state:

- GitHub Actions run: `26391185166`
- deployed commit: `ea0307a`
- schema: `2026-05-25-sprint11`
- numeric mode: `live_numeric`
- live indicators: 24
- numeric fallback: 0
- cycle-state phase: `late-cycle/crowded risk`
- cycle-state confidence: `high`
- chart layer: `sprint10-credit-liquidity-chart-layer`
- chart-layer series: 168

## Current Static Views

- Cycle Status And Transition Synthesis.
- Historical Charts.
- Liquidity And Credit.
- Source Health.
- Contradicting Evidence.
- Latest Radar.
- Changes Since Last Report.
- Archive.
- Methodology.

## Current Synthesis View

**Cycle Status And Transition Synthesis** is now a first-class report section before Latest Radar. It makes the report’s main conclusion explicit:

- current global equity cycle state;
- current growth/rates/liquidity/market-pricing states;
- Oslo-linked sector/subsector phase read-through;
- continuation or transition evidence;
- contradictions;
- confidence and missing data.

## Completed Build Roadmap

- Sprint 1: research evidence schema.
- Sprint 2: GitHub readiness and publication boundary.
- Sprint 3: report-state JSON and change tracking.
- Sprint 4: static site generator.
- Sprint 5: GitHub Actions Pages deployment.
- Sprint 6: source health, freshness, QA, strict fallback guard.
- Sprint 7: proxy labels and contradiction evidence.
- Sprint 8: OECD CLI growth proxies.
- Sprint 9: historical chart layer.
- Sprint 10: liquidity/credit proxies.
- Sprint 11: cycle status and transition synthesis.

## Forward Roadmap

### Sprint 12: Valuation And Market Internals Reality Check

Add only public proxies that improve cycle-state synthesis. Avoid pretending broad proxies are true subsector valuation or institutional market internals.

### Sprint 13: Reviewed Research Evidence

Add reviewed public/manual evidence for priority subsectors.

### Sprint 14: Archive, Monitoring, And Deployment Maturity

Improve archive navigation, run history, data-vintage summaries, and weekly monitoring.

## Change Tracking

Current change tracking covers:

- rank changes;
- score changes;
- signal changes;
- source-status changes;
- research-fact changes;
- market-cycle deltas.

After Sprint 11 it also tracks:

- cycle-state changes;
- phase label changes;
- new transition warnings;
- resolved or new contradictions;
- confidence changes.
