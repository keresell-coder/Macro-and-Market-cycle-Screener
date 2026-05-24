# Open Data Expansion Plan

Last updated: 2026-05-24

## Goal

Move the radar as close as practical to the reviewed macro and market-cycle framework while keeping the project:

- public/open-data first;
- keyless by default;
- deployed from GitHub Actions;
- published as static GitHub Pages HTML/JSON;
- free of private notes, credentials, raw licensed data, paywalled content, and hosted Streamlit services.

The operating model is:

- source code, tests, documentation, source registry, and connector logic live in the GitHub repository;
- GitHub Actions refreshes open indicators and source health weekly;
- GitHub Pages publishes the generated static report and public JSON artifacts;
- local databases, private notes, manual reports, raw licensed data, and unreviewed evidence remain out of git and out of Pages.

The public report URL is:

```text
https://keresell-coder.github.io/Macro-and-Market-cycle-Screener/
```

## Verified Open-Source Candidates

These sources have official pages or documentation indicating programmatic or downloadable access. Each source still needs connector-level testing before being included in scoring.

| Source | Candidate use | Access model | Fit | Notes |
|---|---|---:|---|---|
| OECD Composite Leading Indicators | Growth / turning-point signals | OECD SDMX API / Data Explorer; DB.nomics mirror fallback | High | OECD describes CLIs as early qualitative turning-point signals. Direct OECD SDMX requests currently return a Cloudflare challenge from this environment, so Sprint 8 uses the public DB.nomics mirror of OECD data and labels that boundary. |
| DB.nomics | Cross-provider macro time-series access and mirrors | Public web API | High as fallback/mirror | Useful when an official source is open but hard to automate reliably. Label as a mirror/aggregator, not the primary institution. Already used for OECD CLI mirror data. |
| BIS Data Portal | Credit, property prices, debt, global liquidity | BIS SDMX API and bulk downloads | High | Best open candidate for financial-cycle dimensions such as credit to non-financial sector and property prices. |
| ECB Data Portal | Euro-area rates, monetary aggregates, credit, financial data | ECB SDMX REST API | Medium/high | Strong for Europe-facing policy/liquidity context. SDMX keys can be complex, so start with a small curated set. |
| Eurostat | EU and regional macro detail | Eurostat API and bulk downloads | Medium/high | Good candidate for European inflation, production, labor, trade, and regional context. Use curated series only because dimensions can be dense. |
| FRED public CSV | US rates, financial conditions, credit proxies, inflation expectations | Public graph CSV endpoint where available | Medium/high | Existing project has FRED parser utilities. Use only stable/public series and mark as US/global proxies. |
| Chicago Fed NFCI | US financial conditions | Available via FRED and Chicago Fed | High | Useful liquidity/financial-conditions input. Positive values mean tighter-than-average conditions; negative values mean looser-than-average conditions. |
| IMF Data APIs | Global macro, external, fiscal, and financial datasets | SDMX 2.1/3.0 APIs | Medium, needs endpoint testing | Official IMF docs describe SDMX APIs, but the current Swagger explorer requires a beta portal sign-in. Treat as a candidate only after accountless endpoint tests pass. |
| World Bank | Annual macro and commodity data | Public API/downloads | Already used | Good for robust low-frequency data, but not a substitute for timely PMI/CLI. |
| Norges Bank | Norway rates and FX | Public CSV API | Already used | Strong Oslo/NOK relevance. |
| Statistics Norway | Norway CPI and macro data | Public API | Already used | Strong Norway relevance. |

Official references:

- OECD API overview: https://www.oecd.org/en/data/insights/data-explainers/2024/09/api.html
- OECD Composite Leading Indicators: https://www.oecd.org/en/data/datasets/oecd-composite-leading-indicators-clis.html
- DB.nomics documentation: https://docs.db.nomics.world/
- BIS Data Portal: https://data.bis.org/
- BIS bulk downloads: https://data.bis.org/bulkdownload
- ECB SDMX web services: https://data.ecb.europa.eu/help/getting-data-web-services-sdmx-0
- ECB API data help: https://data.ecb.europa.eu/help/api/data
- Eurostat API guidelines: https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-detailed-guidelines/api-statistics
- IMF Data APIs: https://data.imf.org/en/Resource-Pages/IMF-API
- World Bank Indicators API documentation: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
- Chicago Fed NFCI on FRED: https://fred.stlouisfed.org/series/NFCI

## Important Implementation Rules

- Do not scrape paywalled pages, bot-blocked pages, CAPTCHAs, restricted content, or licensed datasets.
- Prefer official APIs, official bulk downloads, or stable public CSV endpoints.
- Every new connector must produce source-status rows, freshness metadata, and clear failure messages.
- Every new indicator must have a source label, unit, frequency expectation, tailwind direction, and public methodology note.
- New data should be included in scoring only after tests prove fallback behavior is visible and strict live builds fail on numeric `sample_fallback`.
- Missing dimensions must be shown as missing or proxied, not silently treated as neutral.

## Sprint Plan

### Sprint 7: Proxy Label Cleanup And Coverage Honesty

Status: implemented locally on 2026-05-24.

Goal: remove misleading labels and make coverage gaps impossible to miss.

- Renamed the displayed `global_pmi` concept to `global_growth_proxy` in public report state while keeping the legacy internal slug for stored-data compatibility.
- Changed the label to "Global annual GDP growth proxy" and documented that it is World Bank annual real GDP growth, not PMI or OECD CLI data.
- Renamed other public labels that implied stronger source coverage than exists, including oil-price and heating-oil proxies with backward-compatible internal slugs.
- Kept backward-compatible slugs where needed, but made public labels and methodology precise.
- Added a "Contradicting Evidence" summary to static reports using existing recovery, macro, momentum, valuation-proxy, confidence, and sample-backed market-cycle components.
- Acceptance: a reader can tell exactly what is real live data, what is proxy data, what is sample-backed, and what is missing.

### Sprint 8: Open Growth And Leading Indicators

Status: implemented locally on 2026-05-24.

Goal: replace low-frequency growth proxies where open data is available.

- Tested OECD SDMX/Data Explorer access for Composite Leading Indicators. The official endpoint is documented and keyless, but direct requests from this environment return a Cloudflare challenge; the implementation does not bypass it.
- Added a small curated monthly OECD CLI set through the public DB.nomics mirror of OECD `DSD_STES@DF_CLI`: G20, G7, United States, China, and major Europe.
- Kept World Bank annual growth as slow-moving background context, not a PMI substitute.
- Added tests for parsing and report-state coverage; the existing source-status, freshness, and strict live fallback guard cover the new indicators.
- Acceptance: report-state growth coverage moves from "proxied" toward "partial" or "covered" for leading growth signals.

Additional OECD direct-API retest on 2026-05-24:

- Reviewed the official OECD API page, which documents free SDMX API access and shows a Python/CSV example for OECD CLI data.
- Tested the documented CLI CSV endpoint and the documented dataflow endpoint locally and in the browser.
- Result: `sdmx.oecd.org` returned an HTTP 403 Cloudflare verification page from this environment. The browser view also showed an automated security verification screen.
- Decision: do not bypass the block. Keep direct OECD CLI access marked as `public_blocked`; continue using the public DB.nomics mirror for automated live refresh unless OECD provides a non-blocked automation route.
- Manual action needed: none for the current radar, because the DB.nomics mirror already works. Manual OECD follow-up is only needed if direct OECD-hosted access becomes a requirement.

### Sprint 9: Historical Chart Layer And Drilldown

Status: implemented locally on 2026-05-24.

Goal: reintroduce historical line charts as the first analytical layer in the static report, before adding more source families.

- Added a top-of-report chart section so the first analytical layer is historical indicator lines, not only current scores.
- Added a global view using existing live series and clearly labeled proxies:
  - growth/turning point: OECD CLI mirror indicators and annual World Bank GDP growth proxy;
  - inflation/commodity pressure: CPI, oil, gas, and selected commodity indicators;
  - rates/FX/market pricing: policy-rate, NOK FX, yield, and broad market-chart proxies where already available.
- Added drilldown structure for:
  - regional views for global, United States, Europe, China, and Norway/Oslo-linked context where live data exists;
  - sector/subsector views using current scoring-proxy histories and deterministic sample-backed subsector market-cycle histories until reviewed public/licensed market data is connected.
- Added chart metadata for source, vintage/freshness, frequency, data class, proxy/sample/missing status, and scoring inclusion.
- Added chart-window policy metadata: chart x-axes target the shortest common overlap, are capped at 30 years, and are not compressed below a 10-year displayed range; short-history series are flagged until longer histories are fetched.
- Treated metrics and multiples conservatively: true valuation multiples remain missing; market-cycle valuation history is labeled as a sample-backed valuation proxy.
- Updated static-site navigation, source-health display, methodology/framework coverage, tests, and QA text while preserving static GitHub Pages HTML/JSON/assets.
- Acceptance: the report opens with a global historical chart view, supports regional and sector/subsector drilldown, and does not imply true PMI, true subsector multiples, or true licensed market data when only proxies or sample histories are present.

### Sprint 10: Credit, Liquidity, And Financial Conditions

Goal: add the most important missing framework dimension.

- Add one or two robust keyless or configured-key credit/liquidity series first, not a broad fragile catalog.
- Candidate first series:
  - Chicago Fed NFCI through FRED public CSV;
  - selected FRED public credit spread or stress proxies if stable;
  - BIS credit-to-non-financial-sector or property-price series via BIS bulk/API after connector testing.
- Use the configured GitHub Actions secrets `FRED_API_KEY` and `EIA_API_KEY` only through environment variables; do not commit keys.
- Expand historical fetch windows for charted macro/credit series toward 30 years where endpoints support it, then align chart x-axes to the shortest common range with a maximum of 30 years and a displayed minimum of 10 years.
- Add a dedicated liquidity/credit signal group.
- Update framework coverage from "missing" only after live data is connected and tested.
- Acceptance: the dashboard can identify whether liquidity/credit signals confirm or contradict macro and market signals and can show those signals in the historical chart layer.

### Sprint 11: Valuation And Market Internals Reality Check

Goal: improve market-pricing context without pretending to have institutional data.

- Evaluate open, terms-compliant sources for broad valuation proxies and market internals.
- Add only public and robust broad proxies at first, such as index valuation proxies where permitted, volatility, breadth-like series, or public ETF/index chart proxies.
- Keep true Oslo subsector valuation multiples out of scoring unless reviewed public/licensed data is available.
- Acceptance: valuation and market internals remain clearly labeled as broad proxies unless true subsector data is available.

### Sprint 12: Reviewed Research Evidence

Goal: reduce reliance on sample research evidence.

- Add reviewed public/manual CSV evidence for priority subsectors.
- Use the existing `data/research_evidence/` schema locally.
- Export only reviewed public facts to report state.
- Keep unreviewed/manual/licensed/private evidence local.
- Acceptance: static reports show fewer sample research facts and more reviewed public evidence with source URLs and dates.

### Sprint 13: Archive, Monitoring, And Deployment Maturity

Goal: make the weekly process robust as history accumulates.

- Monitor the first scheduled Saturday live run.
- Improve archive navigation after multiple reports exist.
- Add clearer run-status and data-vintage summaries to the static report.
- Decide whether to install Playwright in CI for mandatory screenshot artifacts.
- Consider saving a compact public history JSON in Pages output, not raw databases.
- Acceptance: weekly publication remains useful even when one or more sources fail.

## What Is Hard Or Not Feasible Without Paid Or Manual Data

The framework calls for several dimensions that cannot honestly be implemented as automatic open-data features today:

- analyst earnings revisions and consensus EPS estimates;
- true Oslo subsector valuation multiples;
- detailed company-level backlog, order intake, margins, and revisions;
- licensed shipping freight indices;
- detailed PMI components where only headlines are public;
- proprietary positioning, fund-flow, short-interest, or market-depth datasets;
- automated research from restricted, paywalled, or bot-blocked pages.

These can be handled only through reviewed manual inputs, licensed data that the user has rights to use, or broad public proxies clearly labeled as proxies.

## Current Priority

The next implementation sprint should start with Sprint 10: Credit, Liquidity, And Financial Conditions. Sprint 9 added the static historical chart layer first, so future credit/liquidity source families have an immediate global and regional chart context when connected.
