# Next Step Prompt

Copy/paste this into a fresh chat to start the next open-data expansion step.

```text
You are working in the project folder `/Users/ke/Documents/Codex/Macro and Cycle Screener`.

Please first read:
- `PROJECT_STATE.md`
- `README.md`
- `docs/open_data_expansion_plan.md`
- `docs/knowledge_base_review.md`
- `docs/github_static_report_roadmap.md`
- `docs/github_pages_setup.md`
- `docs/publication_policy.md`

Current project intent:
Build a private-first Oslo-linked Macro and Market-cycle Opportunity Radar that gets as close as practical to the reviewed global macro/market-cycle framework while using only open, reliable, credible, robust, keyless or no-credential data sources. The dashboard should monitor macro, geopolitical, market-cycle, credit/liquidity, market-pricing, source-health, and Oslo-linked subsector signals to identify where phase changes, sentiment shifts, recoveries, or exit warnings may be emerging. It is a research radar and starting point for further single-stock work, not an automatic stock-picking or investment-advice engine.

Current implementation:
- Python/Streamlit local dashboard.
- DuckDB storage with SQLite fallback.
- Keyless live numeric refresh using World Bank Pink Sheet, World Bank Indicators, DB.nomics mirror of OECD CLI data, FRED public CSV financial-conditions proxies, Norges Bank CSV API, Statistics Norway API, and selected public market chart data.
- Latest local live verification after Sprint 10: 24/24 numeric indicators covered, 7,732 observations, 0 numeric `sample_fallback` rows.
- Static HTML report site under `exports/site/` with Historical Charts, Liquidity And Credit, Latest Radar, Source Health, Contradicting Evidence, Changes Since Last Report, Archive, and Methodology views.
- Public-safe report-state JSON includes `chart_layer`, `signal_groups`, `source_freshness`, `source_health`, `framework_coverage`, scoring version, radar state, source statuses, market-cycle summaries, `contradicting_evidence`, and reviewed public facts.
- Sprint 10 added Chicago Fed NFCI and St. Louis Fed Financial Stress Index through public FRED CSV, a dedicated non-scoring liquidity/credit signal group, expanded supported chart histories toward 30 years, and chart layer version `sprint10-credit-liquidity-chart-layer`.
- True valuation multiples, market internals, BIS credit/property data, and licensed subsector market histories remain missing until reviewed public or licensed data is connected.
- `FRED_API_KEY` and `EIA_API_KEY` are configured locally in `.env` and as GitHub Actions repository secrets. Do not print, commit, or publish the key values. Current FRED public CSV indicators do not require a key.
- GitHub Actions workflow runs weekly Saturday 07:15 UTC. Scheduled runs default to live keyless public data and fail if numeric `sample_fallback` is used. Manual sample mode remains available.
- GitHub repository: `https://github.com/keresell-coder/Macro-and-Market-cycle-Screener`.
- Live Pages URL: `https://keresell-coder.github.io/Macro-and-Market-cycle-Screener/`.
- Remaining known non-OK source statuses: UBS public research page blocks scanning with 403; structured research evidence falls back to sample evidence when no reviewed CSV files exist.

Important constraints:
- Do not bypass paywalls, CAPTCHAs, bot blocks, or restricted content.
- Do not assume Codex has API keys; it does not.
- Do not implement paid-data integrations unless explicitly requested later.
- Use official APIs, official bulk downloads, or stable public CSV endpoints where possible.
- Every new connector must produce source-status rows, freshness metadata, clear failure messages, and tests.
- New indicators should enter scoring only after fallback behavior is visible and strict live builds fail on numeric `sample_fallback`.
- Missing dimensions must be shown as missing/proxied/sample-backed, not silently treated as neutral.
- Keep private notes, credentials, manual reports, raw licensed data, local databases, and unpublished research out of public exports.
- Keep unreviewed research claims separate from numeric scoring unless explicit confidence rules are implemented.

Requested next task:
Implement Sprint 11 from `docs/open_data_expansion_plan.md`: Valuation And Market Internals Reality Check.

Scope:
1. Evaluate open, terms-compliant sources for broad valuation proxies and market-internals proxies.
2. Add only one or two robust public proxies first, not a broad fragile catalog.
3. Keep true Oslo subsector valuation multiples out of scoring unless reviewed public or licensed data is available.
4. Label any broad index, ETF, volatility, breadth, or valuation proxy as a proxy, not true subsector data.
5. Add source-status rows, freshness metadata, source registry notes, parser tests, and strict live fallback behavior.
6. Add new series to the historical chart layer before considering scoring use.
7. Update framework coverage, methodology, source-health display, tests, and docs.
8. Preserve static GitHub Pages HTML/JSON/assets; do not build hosted Streamlit.
9. Run local tests and static-site QA.
10. Commit and push.
11. Dispatch the live GitHub Actions workflow and verify Pages still shows `live_numeric` with 0 numeric `sample_fallback`.

After Sprint 11, the next planned sprints are:
- Sprint 12: reviewed public/manual research evidence.
- Sprint 13: archive, monitoring, and deployment maturity.
```
