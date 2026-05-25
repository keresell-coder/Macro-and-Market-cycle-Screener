# GitHub Pages Weekly Report Setup

Last updated: 2026-05-25

Sprint 5 adds `.github/workflows/weekly-report.yml`, which builds and deploys the static report in `exports/site/`.

GitHub repository:

```text
https://github.com/keresell-coder/Macro-and-Market-cycle-Screener
```

Live GitHub Pages URL:

```text
https://keresell-coder.github.io/Macro-and-Market-cycle-Screener/
```

Current status: GitHub Pages is enabled with GitHub Actions as the deployment source. The published Pages JSON reports schema `2026-05-25-sprint11`, `live_numeric` mode, 24 live indicators, 0 numeric `sample_fallback` indicators, cycle-state phase `late-cycle/crowded risk`, cycle-state confidence `high`, chart layer version `sprint10-credit-liquidity-chart-layer`, and 168 chart-layer series. Repository secrets named `FRED_API_KEY` and `EIA_API_KEY` are configured, though the current FRED public CSV indicators do not require a key.

## What The Workflow Does

- Runs on manual dispatch and weekly on Saturdays at 07:15 UTC.
- Scheduled runs default to `live` mode using keyless public data.
- Manual dispatch can choose `live` or deterministic `sample` mode.
- Installs the Python project and test dependencies.
- Runs the test suite.
- Attempts to download the previous public `data/report_state.json` from GitHub Pages for change tracking.
- Builds the static report site.
- In live mode, fails the build if numeric indicators fall back to deterministic `sample_fallback` rows.
- Runs static-site QA against `exports/site/` after generation.
- Publishes the Sprint 11 cycle-state synthesis as static HTML/JSON.
- Uploads only `exports/site/` to GitHub Pages.
- Stores a short-lived debug artifact named `static-radar-site`.

## API Keys

No API keys are included in this project, and Codex does not have your API keys.

The workflow scheduled run defaults to `live` data mode and can run without any API keys. The current `live` mode uses keyless public sources by default and has been verified locally without `FRED_API_KEY` or `EIA_API_KEY`. Manual workflow dispatch can still choose deterministic `sample` mode for debugging.

If you later add connectors that need API access, add repository secrets named:

- `FRED_API_KEY`
- `EIA_API_KEY`

For local dashboard and command-line runs, put the same names in a private `.env` file in the project folder. The app loads `.env` automatically and the file is ignored by git. For GitHub Actions, add the values in repository Settings -> Secrets and variables -> Actions -> New repository secret, then manually run the workflow with `data_mode` set to `live`. Without those secrets, current live mode still uses keyless public data; if a live numeric source fails, fallback rows are marked as `sample_fallback` in source status and should be treated as a visible data-quality issue.

## GitHub Repository Settings

Deployment has already been configured for this repository. For a fresh repository, the setup steps are:

1. Go to repository `Settings`.
2. Open `Pages`.
3. Set the build and deployment source to `GitHub Actions`.
4. Run the workflow manually from the `Actions` tab.

The official GitHub Pages custom-workflow pattern uses `actions/configure-pages`, `actions/upload-pages-artifact`, and `actions/deploy-pages`.

## Previous Report State

By default, the workflow tries this URL pattern for the previous report:

- project site: `https://OWNER.github.io/REPO/data/report_state.json`
- user or organization site: `https://OWNER.github.io/data/report_state.json`

If your Pages URL is different, set a repository variable:

- `CYCLE_RADAR_PREVIOUS_STATE_URL`

Example value:

```text
https://example.com/data/report_state.json
```

If no previous report is found, the site still builds and the Changes view says no previous snapshot was supplied.

## Current Deployment Recommendation

The scheduled workflow is set to `live`. After material workflow or data-source changes, run one manual GitHub Actions dispatch with `data_mode=live` and inspect:

- the generated static site;
- `exports/site/data/latest.json`;
- source status rows for numeric fallback;
- the debug artifact named `static-radar-site`.

In live mode the workflow passes `--fail-on-numeric-sample-fallback`, so numeric fallback will block publication instead of silently affecting the radar.

## Publication Boundary

The workflow deploys only `exports/site/`. It does not deploy:

- local databases or cache files;
- `.env` files or credentials;
- `data/manual_reports/`;
- `data/private_notes/`;
- `data/raw_licensed/`;
- `data/research_evidence/`.
