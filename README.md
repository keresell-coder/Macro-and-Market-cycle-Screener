# Oslo-Linked Macro and Market-cycle Opportunity Radar

Private-first research radar for macro and market-cycle work.

The core objective is to identify where global equities, major sectors, and Oslo-linked subsectors appear to be in the cycle now, and whether evidence points to continuation, transition, recovery, deterioration, or exit risk.

This is not a stock-picking or investment-advice engine. It is a structured research starting point.

## What It Does Today

- Refreshes open/public macro, market, growth, rates, FX, commodity, liquidity/credit, valuation, volatility, and broad leadership proxies.
- Builds local Streamlit views for private analysis.
- Builds a static GitHub Pages report from public-safe HTML/JSON.
- Synthesizes current cycle status and transition evidence from public/proxied inputs.
- Tracks source freshness, source failures, and numeric sample fallback.
- Shows historical charts for global, liquidity/credit, valuation/internals, regional, and sector/subsector views.
- Ranks Oslo-linked subsectors using transparent proxy signals.
- Shows contradiction evidence when signals disagree.
- Includes reviewed public research facts for Oslo-linked subsector cycle interpretation without changing numeric scoring.
- Keeps private notes, credentials, manual reports, local databases, and unreviewed evidence out of public exports.

## Live Sources

Keyless/default live refresh includes:

- World Bank Pink Sheet commodity data.
- World Bank annual GDP growth proxies.
- DB.nomics mirror of OECD CLI data for G20, G7, US, China, and major Europe.
- FRED public CSV for Chicago Fed NFCI, St. Louis Fed Financial Stress Index, and valuation-proxy dependencies.
- Norges Bank FX and policy-rate data.
- Statistics Norway CPI.
- Selected public market-chart proxies.
- Derived public valuation and leadership proxies.
- Committed reviewed public research-evidence CSVs under `data/public_research_evidence/`.

Current schema, latest verification, known source issues, and next sprint live in `PROJECT_STATE.md`.

## Current Limitations

The project is intentionally honest about missing or proxied dimensions:

- The public `global_growth_proxy` is annual World Bank GDP growth, not PMI.
- OECD direct SDMX access is blocked from this environment; DB.nomics is used as a public mirror.
- Subsector market-cycle histories are sample-backed proxies, not true Oslo subsector price or valuation histories.
- Broad valuation, volatility, and equal-weight leadership proxies are now connected, but true Oslo valuation multiples, analyst revisions, earnings estimates, positioning, and true breadth are not implemented.
- Reviewed public research facts improve subsector interpretation and caveats, but they do not override numeric scoring.
- Missing data should be read as a blind spot, not as neutral evidence.

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
- `docs/open_data_expansion_plan.md`: data-admission rules and future source candidates.
- `docs/continuation_prompt.md`: fresh-chat handoff prompt.
- `docs/publication_policy.md`: public/private boundary.
- `docs/github_pages_setup.md`: GitHub Pages workflow setup and deployment mechanics.
- `docs/knowledge_base_review.md`: short review of the durable macro-cycle knowledge base.
- `docs/knowledge_base/global_macro_market_cycle_knowledge_base.md`: durable framework reference.
- `docs/market_researcher_repo_evaluation.md`: historical design note for research-layer ideas.
- `src/cycle_screener/connectors.py`: public data refresh.
- `src/cycle_screener/report_state.py`: public-safe report-state builder.
- `src/cycle_screener/charts.py`: historical chart layer.
- `src/cycle_screener/static_site.py`: static HTML renderer.
- `src/cycle_screener/scoring.py`: current subsector scoring.
- `data/public_research_evidence/`: reviewed public CSV facts and profiles safe to commit.
- `dashboard/app.py`: local Streamlit dashboard.

## Data Policy

Do not commit or publish credentials, `.env`, local databases, private notes, manual reports, raw licensed data, or unpublished research.

Paywalled or licensed data can be used only through reviewed manual inputs or licensed feeds when the user has rights to use it. Raw restricted content must stay out of public artifacts.
