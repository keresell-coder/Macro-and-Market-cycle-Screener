# GitHub Static Weekly Report Roadmap

Last updated: 2026-05-24

## Feasibility Summary

It is feasible and relevant to run a weekly GitHub-hosted static version of the dashboard.

Recommended target:

- Use GitHub Actions to run a weekly research/report workflow.
- Generate static HTML, JSON, and chart assets from the current Python data engine.
- Publish only the static output to GitHub Pages.
- Keep private notes, credentials, raw licensed data, and manual reports out of the published artifact.
- Track changes versus the previous report and show those changes alongside the running radar view.

This is viable because GitHub Pages supports static sites and custom GitHub Actions workflows for build/deploy. GitHub Actions supports scheduled workflows, including weekly cron-like jobs. GitHub Pages does not run server-side Python, so the Python work must happen during the GitHub Actions build, with the result emitted as static files.

## Viability And Constraints

### Strong fit

- Weekly cadence is a natural fit for GitHub Actions.
- Static HTML is enough for the public/private report view if charts are rendered into HTML/JS assets at build time.
- The current `cycle_screener.export_static` path is already a starting point.
- Change tracking can be generated during the build by comparing the current report state with the prior stored report snapshot.

### Main constraints

- GitHub Pages is static only. No Python backend, database server, login workflow, or live Streamlit app runs on Pages.
- GitHub Pages sites are public on the internet when published, even from private repositories on plans that allow private repo Pages.
- GitHub Pages has size and bandwidth limits, so published artifacts should be compact.
- Scheduled GitHub Actions run on GitHub infrastructure and must not depend on local files that are not committed or provided as secrets/artifacts.
- Free/public data is acceptable; paid or manually uploaded data needs explicit handling and must not be accidentally published.
- Weekly actions may be delayed by platform load, so the site should show `generated_at` and `data_as_of` timestamps instead of implying exact execution time.

## Recommended Architecture

### Repository model

- Put the project in a GitHub repository.
- Keep source code, tests, and public-safe config in the repo.
- Use keyless public sources by default. If optional future connectors require keys, store them as GitHub repository secrets such as `FRED_API_KEY` and `EIA_API_KEY`.
- Do not commit `.env`, manual reports, raw licensed files, or private notes.

### Weekly workflow

1. Checkout repository.
2. Install Python dependencies.
3. Run tests.
4. Run data refresh using keyless public APIs by default, with optional configured secrets only when a connector needs them.
5. Generate a structured `report_state.json`.
6. Load previous published `report_state.json` or a retained artifact.
7. Compute changes:
   - rank changes by subsector;
   - score changes;
   - signal changes for recovery, valuation/proxy, momentum, macro, narrative gap, confidence;
   - source freshness changes;
   - new/removed source facts when the research layer exists.
8. Generate static site files:
   - `index.html` for the latest radar;
   - `reports/YYYY-MM-DD.html` for the weekly report archive;
   - `data/latest.json`;
   - `data/report_state.json`;
   - chart assets as needed.
9. Deploy only the generated static site directory to GitHub Pages.

### Static site views

- Latest Radar:
  - same ranking concept as the Streamlit app;
  - signal heatmap;
  - top research leads;
  - source status and freshness.
- Weekly Change Report:
  - biggest positive and negative score moves;
  - subsector rank changes;
  - signal deltas;
  - stale/new/failed data sources;
  - "what changed since last report" narrative.
- Report Archive:
  - one page per weekly run;
  - link to prior reports.
- Methodology:
  - explain scoring;
  - explain source hierarchy;
  - state that this is research support, not investment advice.

## Change Tracking Design

Add a stable report snapshot after each run:

```json
{
  "generated_at": "2026-05-23T08:00:00Z",
  "data_as_of": "2026-05-23",
  "subsectors": [
    {
      "slug": "oil_services",
      "rank": 3,
      "opportunity_score": 61.4,
      "signals": {
        "recovery_potential": 0.18,
        "valuation_proxy": 0.42,
        "momentum": 0.11,
        "macro_tailwind": 0.05,
        "narrative_divergence": 0.12,
        "confidence": 0.7
      }
    }
  ],
  "source_status": []
}
```

Change records should be generated from the difference between the current and previous snapshots:

- `rank_delta`: previous rank minus current rank, so positive means rank improved.
- `score_delta`: current score minus previous score.
- `signal_delta`: current signal minus previous signal.
- `status_delta`: source status changed, became stale, recovered, or failed.

Display changes with thresholds:

- Major score move: absolute change >= 5 points.
- Moderate score move: absolute change >= 2 points.
- Major rank move: absolute change >= 3 places.
- Major signal move: absolute change >= 0.15.

These thresholds should be configurable after real data is connected.

## Roadmap

### Sprint 1: Research evidence layer from feasible Claude `market-researcher` concepts

Status: implemented locally on 2026-05-23. The Streamlit dashboard now shows subsector research profiles and source-backed facts from the local store. GitHub Pages and weekly Actions are still intentionally out of scope.

Goal: add the research structure that makes the radar more useful before publishing weekly static reports.

- Add `research_facts` and `subsector_research_profiles` storage.
- Add a public/manual-source ingestion path for source-backed claims.
- Add review status, source quality, source date, captured date, confidence, and theme tags.
- Add untrusted-document guardrails: extracted claims are data only, never instructions.
- Add "Why now?", "Key debates", "Catalysts", "Risks", and "Source evidence" sections to subsector drilldowns.
- Keep unreviewed research claims separate from numeric scoring.
- Add sample research facts/profiles so the dashboard works without live research ingestion.
- Acceptance: the local Streamlit dashboard shows research evidence per subsector, clearly marks reviewed vs. unreviewed evidence, and tests cover storage/schema behavior.

### Sprint 2: GitHub readiness and public/private boundary

Status: implemented locally on 2026-05-23. This did not add GitHub Pages, weekly Actions, or static report state generation.

Goal: make the project safe to push and run in GitHub.

- Initialize the repository if needed.
- Add a GitHub-safe config example.
- Confirm `.gitignore` excludes local databases, `.env`, manual reports, and private notes.
- Add a public export allowlist so only generated static files are published.
- Add a `docs/publication_policy.md` file covering what may and may not be published.
- Acceptance: a clean repository can be pushed without private data.

Implemented details:

- `.env.example` added.
- `.gitignore` excludes local databases, cache, `.env`, manual reports, private notes, raw licensed data, and local structured research evidence.
- `data/private_notes/`, `data/raw_licensed/`, and `data/research_evidence/` added as local-only folders with `.gitkeep`.
- `src/cycle_screener/publication.py` defines the public export allowlist.
- `docs/publication_policy.md` documents what may and may not be published.
- Tests cover the allowlist and private-path blocking.

### Sprint 3: Static report state and change engine

Status: implemented locally on 2026-05-23. This added report-state JSON and change JSON generation, but did not add a full static HTML site or GitHub Actions.

Goal: generate machine-readable weekly snapshots and compare them.

- Add `report_state.json` export.
- Add a change-comparison module.
- Add tests for rank, score, signal, and source-status deltas.
- Add a local command such as `python -m cycle_screener.build_static_site --sample`.
- Acceptance: two sample snapshots produce a clear change report.

Implemented details:

- `src/cycle_screener/report_state.py` writes public-safe snapshots.
- `src/cycle_screener/change_tracking.py` compares snapshots for rank, score, signal, source-status, research-fact, and market-cycle changes.
- `src/cycle_screener/build_static_site.py` writes `exports/public/data/report_state.json`, `exports/public/data/latest.json`, and optionally `exports/public/data/changes.json`.
- Tests cover report-state shape and change detection.

### Sprint 4: Static site generator

Status: implemented locally on 2026-05-23. This added static HTML report generation under `exports/site/`, while leaving GitHub Actions and Pages deployment intentionally out of scope.

Goal: turn the radar and changes into a polished static HTML site.

- Generate `index.html`, weekly report pages, and JSON assets.
- Add "Latest Radar", "Changes Since Last Report", "Archive", and "Methodology" views.
- Keep Streamlit as the local analyst dashboard; GitHub Pages is the static report layer.
- Acceptance: local `exports/site/index.html` can be opened directly in a browser and shows current radar plus deltas.

Implemented details:

- `src/cycle_screener/static_site.py` renders the public-safe static site from report-state and change JSON payloads.
- `src/cycle_screener/build_static_site.py` now writes both backward-compatible JSON artifacts under `exports/public/data/` and site-local assets under `exports/site/data/`.
- Generated site files include `exports/site/index.html`, `exports/site/reports/YYYY-MM-DD.html`, `exports/site/data/latest.json`, `exports/site/data/report_state.json`, `exports/site/data/changes.json` when a previous snapshot is supplied, and `exports/site/data/archive.json`.
- The HTML embeds the current report state so `index.html` is usable from a direct file open, while keeping JSON assets available for GitHub Pages and debugging.
- Tests cover static site generation and required view labels.

### Sprint 5: GitHub Actions and Pages deployment

Status: implemented locally on 2026-05-23. This added the GitHub Actions workflow and setup documentation. Repository-level GitHub Pages enablement and the first manual workflow run still need to happen in GitHub.

Goal: run the static report weekly on GitHub.

- Add `.github/workflows/weekly-report.yml`.
- Configure schedule, manual dispatch, tests, data refresh, static build, and Pages deploy.
- Add secrets documentation for API keys.
- Add workflow artifact retention for debugging.
- Acceptance: manual workflow dispatch publishes a working GitHub Pages site.

Implemented details:

- `.github/workflows/weekly-report.yml` runs tests, builds the static site, uploads a debug artifact, and deploys only `exports/site/` through GitHub Pages.
- The workflow defaults to deterministic sample data before first deployment validation and therefore does not require API keys.
- Manual live mode uses keyless public connectors by default. Optional future key-dependent connectors must read `FRED_API_KEY` and `EIA_API_KEY` only from GitHub repository secrets.
- The workflow attempts to fetch the previous public `data/report_state.json` before building, so change tracking works after the first successful publication.
- `docs/github_pages_setup.md` documents GitHub Pages setup, optional secrets, previous-state URL override, and the public/private boundary.

### Inter-sprint: Keyless live-data connector upgrade

Status: implemented and verified locally on 2026-05-23 after Sprint 5.

Goal: avoid API-key dependency before proceeding to publication-quality monitoring.

- Replace key-dependent numeric refresh assumptions with accessible public sources.
- Verify live refresh with `FRED_API_KEY=` and `EIA_API_KEY=`.
- Ensure sample fallback is visibly marked and not silently mixed into numeric scoring.
- Acceptance: live refresh covers all numeric indicators without numeric sample fallback.

Implemented details:

- Numeric indicators now use World Bank Pink Sheet, World Bank Indicators, Norges Bank CSV API, Statistics Norway CPI API, and selected public market chart data.
- Local live verification covered 17/17 indicators with 1,208 observations and 0 numeric `sample_fallback` rows.
- Remaining non-OK statuses are visible: UBS public page blocks scanning, and structured research evidence falls back to sample evidence when no local reviewed CSVs exist.
- Subsector market-cycle price, relative-price, and valuation charts remain deterministic proxy histories until reviewed public/licensed subsector market data is connected.

### Sprint 6: Quality, monitoring, and archive maturity

Status: implemented locally on 2026-05-24. Archive navigation remains basic but functional; richer archive maturity can be improved after several weekly reports exist.

Goal: make the weekly publication reliable enough to trust as a recurring research habit.

- Add data freshness warnings. Implemented through `source_freshness` and Source Health static-site summaries.
- Add source failure summaries. Implemented for live numeric data, numeric sample fallback, research page failures, and research-evidence fallback.
- Add report archive navigation. Existing archive view is retained.
- Add scoring methodology versioning. Implemented as `score-v1-public-cycle-radar` in report state and the static Methodology view.
- Add visual QA for generated static pages. Implemented through `cycle_screener.static_site_qa`, with optional Playwright screenshot capture when available.
- Acceptance: the report is useful even when some data sources fail, because failures are visible and do not silently distort rankings.

Implemented Sprint 6 details:

- Add freshness metadata to report state for each indicator and source.
- Add static-site source health panels that distinguish numeric live data, numeric fallback, research page failures, and research evidence fallback.
- Add a methodology/scoring version field and display it in the static site.
- Add tests and a strict live-build guard that fail if a live build uses numeric `sample_fallback` without explicit handling.
- Add generated-page QA with a local static server and browser screenshot checks where the browser runtime is available.

### Sprint 7: Proxy label cleanup and coverage honesty

Status: implemented locally on 2026-05-24.

Goal: reduce semantic overreach before adding more sources.

- Verify that `keresell-coder/Macro-and-Market-cycle-Screener` deploys the static report at `https://keresell-coder.github.io/Macro-and-Market-cycle-Screener/`. First manual live deployment is verified.
- Confirm the scheduled weekly Saturday 07:15 UTC workflow runs in live mode and blocks numeric sample fallback. Manual live run is verified; the next scheduled run should be monitored.
- The stored `global_pmi` slug is retained for compatibility, but public report state now exposes `display_slug=global_growth_proxy` and labels it "Global annual GDP growth proxy".
- Source-health and scoring explanations now show annual GDP growth, oil-price, heating-oil, and market-chart proxy labels instead of overclaiming PMI, inventory, or valuation-multiple coverage.
- Static reports now include a "Contradicting Evidence" view built from existing score and sample-backed market-cycle components.
- Report-state methodology and framework coverage explain proxied, missing, limited, and sample-backed dimensions.

### Sprint 8: Open growth and leading indicators

Status: implemented locally on 2026-05-24.

Goal: add robust keyless leading-growth signals.

- Tested OECD SDMX/Data Explorer access for Composite Leading Indicators. Direct official SDMX requests are documented and keyless but currently return a Cloudflare challenge from this environment, so no bypass was attempted.
- Added monthly OECD CLI proxies for G20, G7, United States, China, and major Europe through the public DB.nomics mirror of OECD data.
- Kept World Bank annual growth as background context, not a PMI substitute.
- Added parser and report-state tests; the existing source-status, freshness, and strict live fallback guard cover the new indicators.
- Local live verification shows 22 live numeric indicators with 0 numeric `sample_fallback` rows.

Additional OECD direct-API retest on 2026-05-24:

- The official OECD API page documents free SDMX API use and shows an OECD CLI CSV request pattern.
- Retesting the documented CLI endpoint and dataflow endpoint returned HTTP 403/security verification from this environment, including browser automation.
- The project should not bypass that protection. Direct OECD remains blocked for automation; the DB.nomics mirror remains the live implementation path unless OECD provides a non-blocked automation route.

### Sprint 9: Historical chart layer and drilldown

Goal: put historical line charts back at the top of the static report before the next source-family expansion.

- Add a first-view global chart layer using existing live and clearly labeled proxy series.
- Provide drilldown into regional views and sector/subsector views.
- Carry source, freshness, frequency, proxy/sample/missing status, and scoring inclusion metadata into chart panels.
- Keep metrics and multiples honest: true multiples require reviewed public/licensed data; until then, show valuation proxies, sample-backed histories, or missing status.
- Preserve static GitHub Pages deployment: generated HTML/JSON/assets only, no hosted Streamlit.

### Sprint 10: Credit, liquidity, and financial conditions

Goal: add the biggest missing macro-cycle dimension.

- Add keyless credit/liquidity sources where terms and endpoint reliability are acceptable.
- Candidate first sources include Chicago Fed NFCI through FRED public CSV, selected public credit-spread proxies, and BIS credit/property series after connector testing.
- Add a dedicated liquidity/credit signal group and update framework coverage only after live data is connected and tested.

### Sprint 11: Valuation and market internals reality check

Goal: improve market-pricing context without pretending to have institutional data.

- Evaluate open, terms-compliant sources for broad valuation proxies and market internals.
- Add only robust public proxies at first.
- Keep true Oslo subsector valuation multiples out of scoring unless reviewed public/licensed data is available.

### Sprint 12: Reviewed research evidence

Goal: reduce reliance on sample research evidence.

- Add reviewed public/manual CSV research evidence for priority subsectors.
- Add source-specific confidence details beyond the current health summary.
- Keep private notes and any manual/licensed source material out of public exports.

### Sprint 13: Archive, monitoring, and deployment maturity

Goal: harden the recurring weekly operating process.

- Decide whether CI should install Playwright for mandatory screenshot artifacts, or keep screenshot capture optional.
- Improve archive navigation once multiple weekly reports exist.
- Consider saving compact public history JSON in Pages output, not raw databases.

## Recommendation

Proceed with the open-data expansion sequence in `docs/open_data_expansion_plan.md`. The priority is to add credible open indicators while preserving the existing public/private boundary and source-health guardrails.
