# Oslo-Linked Macro and Market-cycle Opportunity Radar

Private-first dashboard for spotting Oslo Bors-linked subsectors that may be entering recovery, becoming neglected, or showing favorable macro/cycle setups.

This is a research radar, not an investment recommendation engine. It ranks subsectors using transparent indicators and shows the evidence behind the score.

## What V1 Includes

- Opportunity Radar table and heatmap for Oslo-linked subsectors.
- Signal heatmap before the table, focused on opportunity drivers rather than data confidence.
- Highlighted radar-table values for signals that stand out among the currently visible subsectors.
- Drilldown charts for sector price proxy, Oslo benchmark proxy, relative price, valuation proxy, and macro/market-cycle drivers.
- Highlighted subsector research conclusion shown above the evidence details rather than hidden under tabs.
- Explainable scoring across cycle pressure, recovery potential, valuation/proxy pricing, momentum, macro tailwind, and narrative divergence.
- Research evidence profiles per subsector with "Why now?", "Key debates", "Catalysts", "Risks", and source-backed facts.
- Reviewed/unreviewed research evidence labels; unreviewed claims are kept separate from numeric scoring.
- Keyless public data connectors with deterministic sample fallback only when a live source fails.
- DuckDB data store for raw observations, normalized indicators, source status, scores, research profiles, and research facts.
- Static HTML export for private sharing across devices.
- Public-safe static report site with Latest Radar, Changes Since Last Report, Archive, and Methodology views.
- Public-safe report-state JSON export and change-comparison engine for future weekly static reports.
- Public source-health summaries covering numeric freshness, live numeric data, numeric sample fallback, research page failures, and research-evidence fallback.
- Framework coverage metadata showing which macro-cycle dimensions are implemented, proxied, sample-backed, or missing.
- Scoring methodology versioning shown in the static Methodology view.
- GitHub Actions workflow for manually or weekly building and deploying the static site to GitHub Pages.
- Static-site QA command that serves the generated site locally and runs browser/screenshot checks when Playwright is available.
- Manual report folder for documents you are entitled to use.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install ".[dev]"
python -m cycle_screener.refresh --sample
streamlit run dashboard/app.py
```

If you want a deterministic local demo, `--sample` creates a complete dataset so the dashboard works immediately. The normal live refresh also works without API keys.

## Live Data Refresh

The default live refresh does not require API keys:

```bash
python -m cycle_screener.refresh
```

Current keyless sources include World Bank commodity and macro data, Norges Bank FX and policy-rate data, Statistics Norway CPI data, and limited public market chart data for traded proxies. If a live numeric source fails, missing series are filled from deterministic sample data and marked in source status.

The live refresh was verified locally without `FRED_API_KEY` or `EIA_API_KEY`: 17/17 numeric indicators were covered with 0 numeric `sample_fallback` rows. Research evidence may still fall back to sample evidence when no local reviewed CSV files exist.

Optional future connectors may use:

```bash
export FRED_API_KEY="..."
export EIA_API_KEY="..."
```

Codex does not have these keys.

## Static Export

```bash
python -m cycle_screener.export_static
```

The export is written to `exports/opportunity_radar.html`. It excludes private notes and manual reports.

Public-safe export targets are allowlisted in `src/cycle_screener/publication.py`. Future GitHub Pages work should publish only generated files under `exports/opportunity_radar.html`, `exports/public/`, or `exports/site/`.

## Report State And Changes

Sprint 3 added public-safe JSON artifacts for future static reports, and Sprint 4 turns those artifacts into a static site:

```bash
python -m cycle_screener.build_static_site --sample
```

This writes:

- `exports/public/data/report_state.json`
- `exports/public/data/latest.json`
- `exports/site/index.html`
- `exports/site/reports/YYYY-MM-DD.html`
- `exports/site/data/report_state.json`
- `exports/site/data/latest.json`
- `exports/site/data/archive.json`

To compare with a prior snapshot:

```bash
python -m cycle_screener.build_static_site --previous path/to/previous_report_state.json
```

When a previous snapshot is supplied, `exports/public/data/changes.json` and `exports/site/data/changes.json` are written with rank, score, signal, source-status, research-fact, and market-cycle deltas. The site can be opened directly from `exports/site/index.html`.

The generated report-state JSON also includes `source_freshness`, `source_health`, `framework_coverage`, and a scoring methodology version. A strict live build can fail if numeric live refresh falls back to deterministic sample rows:

```bash
python -m cycle_screener.build_static_site --fail-on-numeric-sample-fallback
python -m cycle_screener.static_site_qa exports/site
```

## GitHub Pages Workflow

The project is configured for GitHub repository:

```text
https://github.com/keresell-coder/Macro-and-Market-cycle-Screener
```

Sprint 5 adds `.github/workflows/weekly-report.yml`.

The scheduled workflow runs weekly on Saturdays at 07:15 UTC and now defaults to `live` mode using keyless public connectors. Live builds fail if numeric indicators fall back to deterministic `sample_fallback` rows. Manual dispatch still allows `sample` mode for deterministic debugging. Optional secrets can be added later as `FRED_API_KEY` and `EIA_API_KEY`; Codex does not have those keys.

GitHub Pages is enabled and the live static report is available at:

```text
https://keresell-coder.github.io/Macro-and-Market-cycle-Screener/
```

The first verified live deployment reported 17 live numeric indicators, 0 numeric `sample_fallback` indicators, and one visible research-page failure for the UBS public insights page returning 403.

Details are in `docs/github_pages_setup.md`.

## Structured Research Evidence

Optional public/manual evidence can be added as CSV files in `data/research_evidence/`.

- `subsector_research_profiles.csv`: `subsector_slug`, `scope`, `current_phase_hypothesis`, `why_now`, `key_debates`, `catalysts`, `risks`, `review_status`, `updated_at`.
- `research_facts.csv`: `fact_id`, `subsector_slug`, `theme`, `claim`, `source_name`, `source_url`, `source_type`, `source_quality`, `source_date`, `captured_at`, `confidence`, `review_status`, `evidence_scope`.

Rows with unknown subsectors are dropped, confidence is clipped to 0-100%, and unknown review statuses become `unreviewed`.

## Project Structure

- `PROJECT_STATE.md` is the durable handoff file. Update it after each sprint or iteration so a fresh chat can continue without full conversation context.
- `docs/market_researcher_repo_evaluation.md` records the 2026-05-23 review of the public Anthropic `market-researcher` plugin and possible relevance to this project.
- `docs/github_static_report_roadmap.md` records the roadmap for a weekly GitHub Pages static report with change tracking.
- `docs/github_pages_setup.md` explains how to enable the GitHub Pages workflow and optional secrets.
- `docs/knowledge_base/global_macro_market_cycle_knowledge_base.md` stores the AI-drafted macro/market-cycle knowledge-base reference supplied for project planning.
- `docs/knowledge_base_review.md` records the project-specific review of that knowledge base, including implementable, difficult, and out-of-scope items.
- `docs/open_data_expansion_plan.md` defines the open/keyless source expansion plan and next sprint sequence.
- `docs/continuation_prompt.md` contains a copy/paste prompt for starting fresh chats in this project.
- `docs/next_step_prompt.md` contains a copy/paste prompt for the immediate next implementation step.
- `src/cycle_screener/taxonomy.py` defines subsectors, drivers, proxies, and confidence levels.
- `src/cycle_screener/sources.py` defines allowed data and research sources.
- `src/cycle_screener/connectors.py` fetches public data and research-source status.
- `src/cycle_screener/research.py` ingests structured public/manual research evidence as claim data.
- `src/cycle_screener/publication.py` defines the public export allowlist and blocks known private paths.
- `src/cycle_screener/report_state.py` builds public-safe report snapshots.
- `src/cycle_screener/change_tracking.py` compares report snapshots and classifies deltas.
- `src/cycle_screener/static_site.py` renders the static HTML report site from public-safe report snapshots.
- `src/cycle_screener/build_static_site.py` writes JSON artifacts and the static site under `exports/site/`.
- `src/cycle_screener/static_site_qa.py` serves generated static pages locally and verifies required page content, with optional Playwright screenshot capture.
- `src/cycle_screener/scoring.py` calculates explainable opportunity scores.
- `src/cycle_screener/storage.py` persists data in DuckDB, with SQLite fallback for restricted environments.
- `dashboard/app.py` is the Streamlit app.
- `data/manual_reports/` is for reports you have rights to use.
- `data/research_evidence/` may contain structured public/manual-source CSV files named `subsector_research_profiles.csv` and `research_facts.csv`.
- `data/private_notes/` and `data/raw_licensed/` are local-only folders excluded from git.
- `docs/publication_policy.md` defines what may and may not be published later.

## Data Policy

The app does not bypass paywalls or scrape restricted content. Paywalled or licensed sources should be represented as manual uploads or configured paid feeds only when you have the right to use them.

Structured research evidence is treated as data, not instructions. It is shown in the dashboard as research context and does not change opportunity scores unless explicit confidence and scoring rules are added later.
