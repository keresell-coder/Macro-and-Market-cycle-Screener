# Global Macro, Market and Sector-Cycle Screener

Private-first global research screener for macro, market and sector-cycle work. Oslo-listed subsectors remain one implementation lens, not the geographic boundary of the model.

The core objective is to identify where global equities, major sectors, and Oslo-linked subsectors appear to be in the cycle now, and whether evidence points to continuation, transition, recovery, deterioration, or exit risk.

This is not a stock-picking or investment-advice engine. It is a structured research starting point.

## What It Does Today

- Refreshes open/public macro, market, growth, rates, FX, commodity, liquidity/credit, valuation, volatility, and broad leadership proxies.
- Builds local Streamlit views for private analysis.
- Builds a static GitHub Pages report from public-safe HTML/JSON/PDF assets.
- Synthesizes current cycle status and transition evidence from public/proxied inputs.
- Opens with a decision-first view: current state, direction, change, invalidation evidence, and separate trust measures.
- Shows separate economic, inflation/rates, liquidity/credit, market-pricing and sector-operating clocks, plus 18 properly split subsector research screens. The map is not a timing forecast.
- Gives every subsector an expandable investor-use summary, confirmation requirement, evidence boundary, and primary missing-data gap.
- Separates data quality, model support, and historical validation instead of presenting one ambiguous confidence label.
- Tracks source freshness, source failures, and numeric sample fallback.
- Shows static run status, data vintage, deployment metadata, and archive continuity.
- Checks phase stability, phase-rule replay, transition evidence, contradictions, and confidence-label consistency against accumulated public report snapshots. This is implementation replay, not independent calibration.
- Shows historical charts for global, liquidity/credit, valuation/internals, regional, and sector/subsector views.
- Uses a transparent research-priority index for triage. It is not expected return, valuation, or an entry/exit signal.
- Shows contradiction evidence when signals disagree.
- Includes reviewed public research facts and a dated, source-tiered timeline of major institutional global outlooks without changing numeric scoring.
- Keeps private notes, credentials, manual reports, local databases, and unreviewed evidence out of public exports.
- Generates a public-safe, one-page A4 weekly PDF with a fixed mobile-friendly URL.

## Live Sources

Keyless/default live refresh includes:

- World Bank Pink Sheet commodity data.
- World Bank annual GDP growth proxies.
- DB.nomics mirror of OECD CLI data for G20, G7, US, China, and major Europe.
- BIS central-bank policy rates via DB.nomics for the Fed, ECB, BoE, BoJ, PBoC, BoC, RBA, SNB and Riksbank.
- FRED public CSV for inflation, nominal/real yields, the yield curve, NFCI, financial stress, credit spreads and the broad dollar.
- Norges Bank FX and policy-rate data.
- Statistics Norway CPI.
- US EIA petroleum inventories and the Caldara-Iacoviello Geopolitical Risk Index.
- Selected public market-chart proxies.
- Derived public valuation and leadership proxies.
- Committed reviewed public research-evidence CSVs under `data/public_research_evidence/`.

Current schema, latest verification, known source issues, and next sprint live in `PROJECT_STATE.md`.

## Current Limitations

The project is intentionally honest about missing or proxied dimensions:

- The public `global_growth_proxy` is annual World Bank GDP growth, not PMI.
- OECD direct SDMX access is blocked from this environment; DB.nomics is used as a public mirror.
- Live builds exclude deterministic subsector histories. A sector phase remains evidence-gated until validated sector returns, valuation, earnings/revisions and operating data are connected.
- Broad valuation, volatility and equal-weight leadership proxies are connected, but true global sector valuation multiples, analyst revisions, positioning and breadth are not implemented.
- Reviewed public research facts improve subsector interpretation and caveats, but they do not override numeric scoring.
- Report history currently has too few independent, time-separated full states for empirical calibration or a long-horizon backtest.
- Subsector outputs are explicitly labeled proxy research screens until direct evidence is connected.
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

The build also creates:

- local latest brief: `output/pdf/weekly-cycle-brief.pdf`;
- public latest brief: `exports/site/weekly/weekly-cycle-brief.pdf`;
- a dated public PDF alongside the fixed latest copy.

## GitHub Pages

Live site:

```text
https://keresell-coder.github.io/Macro-and-Market-cycle-Screener/
```

Fixed weekly one-page PDF:

```text
https://keresell-coder.github.io/Macro-and-Market-cycle-Screener/weekly/weekly-cycle-brief.pdf
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
- `docs/model_governance_and_evidence.md`: audited construct map, scoring controls, scientific references, and evidence boundaries.
- `src/cycle_screener/connectors.py`: public data refresh.
- `src/cycle_screener/report_state.py`: public-safe report-state builder.
- `src/cycle_screener/decision_support.py`: investor-use framing, cycle-map records, trust separation, and subsector evidence boundaries.
- `src/cycle_screener/signal_metrics.py`: frequency-aware percentile and momentum transformations.
- `src/cycle_screener/weekly_pdf.py`: public-safe one-page weekly PDF.
- `src/cycle_screener/charts.py`: historical chart layer.
- `src/cycle_screener/static_site.py`: static HTML renderer.
- `src/cycle_screener/scoring.py`: current subsector scoring.
- `data/public_research_evidence/`: reviewed public CSV facts and profiles safe to commit.
- `dashboard/app.py`: local Streamlit dashboard.

## Data Policy

Do not commit or publish credentials, `.env`, local databases, private notes, manual reports, raw licensed data, or unpublished research.

Paywalled or licensed data can be used only through reviewed manual inputs or licensed feeds when the user has rights to use it. Raw restricted content must stay out of public artifacts.
