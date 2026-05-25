# Oslo-Linked Macro and Market-cycle Opportunity Radar

Private-first research radar for macro and market-cycle work.

The core objective is to identify where global equities, major sectors, and Oslo-linked subsectors appear to be in the cycle now, and whether evidence points to continuation, transition, recovery, deterioration, or exit risk.

This is not a stock-picking or investment-advice engine. It is a structured research starting point.

## What It Does Today

- Refreshes open/public macro, market, growth, rates, FX, commodity, and liquidity/credit indicators.
- Builds local Streamlit views for private analysis.
- Builds a static GitHub Pages report from public-safe HTML/JSON.
- Synthesizes current cycle status and transition evidence from public/proxied inputs.
- Tracks source freshness, source failures, and numeric sample fallback.
- Shows historical charts for global, liquidity/credit, regional, and sector/subsector views.
- Ranks Oslo-linked subsectors using transparent proxy signals.
- Shows contradiction evidence when signals disagree.
- Keeps private notes, credentials, manual reports, local databases, and unreviewed evidence out of public exports.

## Current Live Sources

Current keyless/default live data includes:

- World Bank Pink Sheet commodity data.
- World Bank annual GDP growth proxies.
- DB.nomics mirror of OECD CLI data for G20, G7, US, China, and major Europe.
- FRED public CSV for Chicago Fed NFCI and St. Louis Fed Financial Stress Index.
- Norges Bank FX and policy-rate data.
- Statistics Norway CPI.
- Selected public market-chart proxies.

Latest published Sprint 10 verification before the Sprint 11 deployment:

- `schema_version`: `2026-05-24-sprint10`
- `numeric_mode`: `live_numeric`
- live indicators: 24
- numeric `sample_fallback`: 0
- chart layer: `sprint10-credit-liquidity-chart-layer`
- chart-layer series: 168

Known visible non-OK statuses:

- UBS public research page returns 403.
- Research evidence falls back to sample evidence if no reviewed local CSV evidence exists.

## Current Limitations

The project is intentionally honest about missing or proxied dimensions:

- The public `global_growth_proxy` is annual World Bank GDP growth, not PMI.
- OECD direct SDMX access is blocked from this environment; DB.nomics is used as a public mirror.
- Subsector market-cycle histories are sample-backed proxies, not true Oslo subsector price or valuation histories.
- True valuation multiples, analyst revisions, earnings estimates, positioning, breadth, and many market internals are not yet implemented.
- Missing data should be read as a blind spot, not as neutral evidence.

## Current Direction

Sprint 11 adds **Cycle Status And Transition Synthesis**.

The report now synthesizes existing indicators into explicit conclusions:

- global equity cycle status;
- growth cycle status;
- inflation/rates pressure status;
- liquidity/credit status;
- risk appetite and market-pricing status;
- sector/subsector phase;
- transition or continuation warnings;
- confidence and contradicting evidence.

Future valuation or market-internals data should be added only when it improves this cycle synthesis. The next sprint should be **Valuation And Market Internals Reality Check**.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install ".[dev]"
python -m cycle_screener.refresh --sample
streamlit run dashboard/app.py
```

Live refresh:

```bash
python -m cycle_screener.refresh
```

Build static report:

```bash
python -m cycle_screener.build_static_site --fail-on-numeric-sample-fallback
python -m cycle_screener.static_site_qa exports/site
```

## GitHub Pages

Live site:

```text
https://keresell-coder.github.io/Macro-and-Market-cycle-Screener/
```

Workflow:

- `.github/workflows/weekly-report.yml`
- manual dispatch or weekly Saturday 07:15 UTC
- scheduled runs default to live data
- strict live builds fail on numeric `sample_fallback`
- deploys only `exports/site/`

## Project Map

- `PROJECT_STATE.md`: current state and next step.
- `docs/open_data_expansion_plan.md`: concise sprint plan.
- `docs/next_step_prompt.md`: immediate next-sprint copy/paste prompt.
- `docs/continuation_prompt.md`: fresh-chat handoff prompt.
- `docs/publication_policy.md`: public/private boundary.
- `src/cycle_screener/connectors.py`: public data refresh.
- `src/cycle_screener/report_state.py`: public-safe report-state builder.
- `src/cycle_screener/charts.py`: historical chart layer.
- `src/cycle_screener/static_site.py`: static HTML renderer.
- `src/cycle_screener/scoring.py`: current subsector scoring.
- `dashboard/app.py`: local Streamlit dashboard.

## Data Policy

Do not commit or publish credentials, `.env`, local databases, private notes, manual reports, raw licensed data, or unpublished research.

Paywalled or licensed data can be used only through reviewed manual inputs or licensed feeds when the user has rights to use it. Raw restricted content must stay out of public artifacts.
