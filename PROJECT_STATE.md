# Project State: Oslo Macro and Market-cycle Opportunity Radar

Last updated: 2026-05-24

## Current Goal

Build a private-first research dashboard that identifies Oslo Bors-linked subsectors with potential cycle recovery or mispricing. The dashboard should surface subsectors and evidence, not single-company recommendations.

## Current Implementation

- Python project with Streamlit dashboard, DuckDB storage, keyless public live-data connectors, deterministic sample fallback, static HTML export, static report site, Sprint 6 source-health monitoring, GitHub Pages workflow, and tests.
- Main app: `dashboard/app.py`.
- Core package: `src/cycle_screener/`.
- Static export: `exports/opportunity_radar.html`.
- Static report site: `exports/site/index.html`.
- GitHub Pages workflow: `.github/workflows/weekly-report.yml`.
- GitHub repository: `https://github.com/keresell-coder/Macro-and-Market-cycle-Screener`.
- Live GitHub Pages report: `https://keresell-coder.github.io/Macro-and-Market-cycle-Screener/`.
- Manual reports folder: `data/manual_reports/`.
- Scoring version shown in public methodology: `score-v1-public-cycle-radar`.
- Saved knowledge-base reference: `docs/knowledge_base/global_macro_market_cycle_knowledge_base.md`.
- Reviewed knowledge-base assessment: `docs/knowledge_base_review.md`.

## Current Dashboard Behavior

- Name: Oslo-Linked Macro and Market-cycle Opportunity Radar.
- Top summary metrics: subsector count, top score, median confidence, data backend.
- Signal Heatmap appears before the Opportunity Radar table and excludes confidence.
- Opportunity Radar table includes signal highlighting:
  - Green: high-positive value relative to currently filtered subsectors.
  - Red: low-negative value relative to currently filtered subsectors.
  - Amber: large absolute signal.
- Subsector Drilldown shows normalized indicator lines indexed to 100 with a y-axis symmetric around 100.
- Subsector Drilldown now also shows a visible highlighted research conclusion, not hidden in tabs.
- Drilldown includes a "Sector Price, Valuation, And Driver Picture" chart with deterministic sample history for:
  - subsector price proxy;
  - Oslo benchmark proxy;
  - relative subsector price;
  - valuation proxy.
- Subsector Drilldown now includes a Research Evidence section with:
  - "Why now?";
  - "Valuation context";
  - "Market-cycle watch";
  - "Key debates";
  - "Catalysts";
  - "Risks";
  - "Source evidence" with claim, source, date, confidence, scope, and review status.
- Reviewed and unreviewed research evidence is clearly labeled. Unreviewed claims do not affect numeric scoring.
- Public export excludes private notes and manual reports.

## Data And Scoring Notes

- V1 can run either deterministic sample data or live public data.
- The default live refresh does not require API keys and was verified without `FRED_API_KEY` or `EIA_API_KEY`.
- `FRED_API_KEY` and `EIA_API_KEY` are optional future connector keys only; Codex does not have them.
- Keyless public data is preferred. The project must not bypass paywalls or scrape restricted data.
- Scoring is explainable and transparent, using indicator percentiles, momentum, macro tailwind, valuation/proxy signal, recovery potential, and narrative divergence.
- Sprint 1 research evidence tables are implemented:
  - `subsector_research_profiles`;
  - `research_facts`.
- Additional market-cycle display table is implemented:
  - `subsector_market_cycle`.
- `src/cycle_screener/research.py` ingests structured CSV evidence from `data/research_evidence/`:
  - `subsector_research_profiles.csv`;
  - `research_facts.csv`.
- If no structured evidence files exist, deterministic sample research profiles and facts are loaded.
- Research evidence is claim data only. It is not interpreted as instructions and is not included in score calculation.
- Source-backed sample facts now reference public sources including IEA, UNCTAD, Norges Bank, IMF, World Bank, Norwegian Seafood Council, and EIA.
- Subsector market-cycle price, relative-price, and valuation proxy history remains deterministic sample data until reviewed public/licensed subsector market data is connected.

## Keyless Live Source Status

Implemented and verified on 2026-05-23:

- Numeric indicator refresh now uses accessible live sources without API keys:
  - World Bank Pink Sheet monthly commodity prices for Brent, WTI, natural gas, copper, aluminum, food/input proxies, and oil price pressure inputs.
  - World Bank Indicators API for global and China growth proxies.
  - Norges Bank CSV API for USD/NOK, EUR/NOK, and policy-rate data.
  - Statistics Norway API for CPI.
  - Yahoo chart data for NASDAQ, heating oil, and US 10-year yield market proxies where no official keyless endpoint is currently wired.
- Live refresh was verified with `FRED_API_KEY=` and `EIA_API_KEY=`:
  - 1,208 observations;
  - 17/17 indicators covered;
  - 0 numeric `sample_fallback` rows;
  - latest live dates range from 2024-12-31 for annual World Bank growth proxies to 2026-05-31 for FX/rates/market proxies.
- Remaining non-OK statuses after live verification:
  - UBS public research page returns 403 and is skipped.
  - Structured research evidence falls back to sample evidence when no local reviewed CSV files exist.

Important live-data caveats:

- Yahoo chart data is used only for broad market proxies where no official keyless endpoint is currently wired: NASDAQ, heating oil, and US 10-year yield proxy.
- World Bank growth proxies are annual and therefore naturally less fresh than monthly/daily market and macro series.
- Numeric scoring uses live indicators after a live refresh, but subsector market-cycle charts still use deterministic proxy histories.

## GitHub/Public Boundary Status

Sprint 2 GitHub readiness and public/private boundary is implemented locally:

- `.env.example` added for safe configuration.
- `.gitignore` excludes `.env`, local databases, cache, manual reports, private notes, raw licensed data, and local structured research evidence.
- Local-only folders added:
  - `data/private_notes/`;
  - `data/raw_licensed/`;
  - `data/research_evidence/`.
- Public-safe export allowlist added in `src/cycle_screener/publication.py`.
- Publication policy added in `docs/publication_policy.md`.
- Tests cover public path allowlist behavior.

## Static Report State And Site Status

Sprint 3 static report state and change engine is implemented locally:

- `src/cycle_screener/report_state.py` builds public-safe report snapshots.
- `src/cycle_screener/change_tracking.py` compares report snapshots.
- `src/cycle_screener/build_static_site.py` writes JSON artifacts and the Sprint 4 static site.
- `src/cycle_screener/static_site.py` renders the static HTML pages.
- `src/cycle_screener/static_site_qa.py` serves generated static pages locally and verifies required page content, with optional Playwright screenshot capture.
- Generated artifacts:
  - `exports/public/data/report_state.json`;
  - `exports/public/data/latest.json`;
  - `exports/public/data/changes.json` when a previous snapshot is supplied.
  - `exports/site/index.html`;
  - `exports/site/reports/YYYY-MM-DD.html`;
  - `exports/site/data/report_state.json`;
  - `exports/site/data/latest.json`;
  - `exports/site/data/changes.json` when a previous snapshot is supplied;
  - `exports/site/data/archive.json`.
- Report state includes:
  - rank, score, and signal values by subsector;
  - latest source status;
  - per-indicator source freshness and source-health summaries;
  - framework coverage metadata across growth, inflation, rates, credit, earnings, valuation, market internals, subsector market-cycle data, and research evidence;
  - latest market-cycle summary per subsector;
  - reviewed public research facts only.
- Change tracking covers:
  - rank deltas;
  - score deltas;
  - signal deltas;
  - source-status changes;
  - new, removed, and changed research facts;
  - market-cycle deltas.
- Sprint 4 static site views are implemented:
  - Latest Radar;
  - Changes Since Last Report;
  - Archive;
  - Methodology.
- Sprint 5 GitHub Actions workflow is implemented locally:
  - manual dispatch;
  - weekly Saturday 07:15 UTC schedule;
  - scheduled `live` mode using keyless public connectors by default;
  - manual `sample` mode available for deterministic debugging;
  - optional live mode using repository secrets named `FRED_API_KEY` and `EIA_API_KEY`;
  - tests before build;
  - previous public report-state download attempt for change tracking;
  - deploys only `exports/site/` to GitHub Pages;
  - debug artifact retention for generated static output.
- Sprint 6 quality and monitoring is implemented locally:
  - `source_freshness` and `source_health` are exported in public report-state JSON;
  - the static Source Health section distinguishes live numeric data, numeric sample fallback, research page failures, and research-evidence fallback;
  - static Methodology displays framework reference, framework coverage, implementation boundary, and a framework coverage matrix;
  - strict live static builds can fail on numeric `sample_fallback` via `--fail-on-numeric-sample-fallback`;
  - tests cover fallback visibility and the strict guard;
  - generated static-site QA is wired into the GitHub workflow.
- GitHub repository setup status:
  - local project is initialized as a git repository on branch `main`;
  - remote `origin` points to `https://github.com/keresell-coder/Macro-and-Market-cycle-Screener.git`;
  - initial project commit and follow-up workflow fix have been pushed;
  - GitHub Pages is enabled with GitHub Actions as the build/deploy source;
  - first manual live workflow deployment completed successfully;
  - the static HTML report is accessible from other devices at the Pages URL above.
- Latest GitHub Pages verification on 2026-05-24:
  - public report URL returned HTTP 200;
  - public `data/report_state.json` returned HTTP 200;
  - `numeric_mode`: `live_numeric`;
  - `live_indicator_count`: 17;
  - numeric `sample_fallback` count: 0;
  - research page failures: 1, UBS public insights page returned 403 and remains a visible source failure.

## Verification Commands

```bash
.venv/bin/python -m cycle_screener.refresh --sample
FRED_API_KEY= EIA_API_KEY= PYTHONPATH=src .venv/bin/python -m cycle_screener.refresh
.venv/bin/python -m cycle_screener.export_static
PYTHONPATH=src .venv/bin/python -m cycle_screener.build_static_site --sample
PYTHONPATH=src .venv/bin/python -m cycle_screener.build_static_site --previous exports/public/data/report_state.json
PYTHONPATH=src .venv/bin/python -m cycle_screener.build_static_site --fail-on-numeric-sample-fallback
PYTHONPATH=src .venv/bin/python -m cycle_screener.static_site_qa exports/site
.venv/bin/python -m pytest -q
HOME="$PWD/.streamlit_home" STREAMLIT_BROWSER_GATHER_USAGE_STATS=false .venv/bin/streamlit run dashboard/app.py --server.port 8501 --server.address 127.0.0.1
```

## Next Likely Improvements

- Monitor the next scheduled Saturday 07:15 UTC live workflow run.
- Rename or replace misleading proxy labels, especially `global_pmi`, which currently uses annual World Bank GDP growth rather than true PMI data.
- Add a true "contradicting evidence" summary to the static report.
- Add keyless credit/liquidity sources where terms and endpoint reliability are acceptable, such as selected FRED public CSV series.
- Add source-specific confidence detail beyond the first research facts table.
- Add a private notes layer that is explicitly excluded from public/static exports.
- Replace deterministic market-cycle proxy history with reviewed public/licensed subsector price, constituent, and valuation data.
- Push the repository to GitHub, enable Pages source "GitHub Actions", and manually dispatch the weekly report workflow.
- Decide whether to install Playwright in CI for mandatory static-site screenshots, or keep screenshot capture optional.
- Add richer archive navigation if weekly report history becomes large.

## Current Research Evaluation

On 2026-05-23, the public Anthropic `financial-services` repo's `market-researcher` agent/plugin was reviewed for possible dashboard relevance:

- Source: `https://github.com/anthropics/financial-services/tree/main/plugins/agent-plugins/market-researcher`.
- Detailed evaluation file: `docs/market_researcher_repo_evaluation.md`.
- Recommendation: adapt the research-process elements, not the whole agent architecture.
- Most relevant concepts: sector overview workflow, source-quality hierarchy, structured facts with citations, untrusted-document guardrails, key debates, catalysts, and review gates.
- Use caution with peer comps and idea generation because the repo assumes institutional data sources such as CapIQ/FactSet and includes company-level idea workflows.
- Do not implement anything from it yet unless explicitly requested.

## GitHub Static Weekly Report Evaluation

On 2026-05-23, GitHub Pages and GitHub Actions were evaluated as a feasible target for a weekly static research report:

- Detailed roadmap file: `docs/github_static_report_roadmap.md`.
- Recommended model: keep Streamlit as the local analyst dashboard, and generate a public-safe static HTML/JSON report for GitHub Pages.
- Weekly workflow concept: scheduled GitHub Action refreshes data, builds report snapshots, computes changes since the prior report, generates static site files, and deploys only public-safe output.
- Change tracking should include rank deltas, score deltas, signal deltas, source-status changes, and later research-fact changes.
- Static Pages must not contain private notes, credentials, manual reports, raw licensed data, or paywalled content.
- GitHub Pages cannot run Python server-side, so all Python work must occur during the Actions build step.
- Roadmap update: Sprint 1, Sprint 2, Sprint 3, Sprint 4, Sprint 5, Sprint 6, and the keyless live-data connector upgrade have been implemented locally. GitHub Pages still needs repository-level enablement and a manual workflow run.

## Continuation Prompt

For fresh chats, use `docs/continuation_prompt.md`. For the immediate next implementation task, use `docs/next_step_prompt.md`.
