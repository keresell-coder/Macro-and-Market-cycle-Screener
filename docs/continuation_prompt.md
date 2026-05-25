# Continuation Prompt

Use this prompt to continue in a fresh chat.

```text
You are working in `/Users/ke/Documents/Codex/Macro and Cycle Screener`.

First read:
- `PROJECT_STATE.md`
- `README.md`
- `docs/open_data_expansion_plan.md`
- `docs/knowledge_base_review.md`
- `docs/github_static_report_roadmap.md`
- `docs/github_pages_setup.md`
- `docs/publication_policy.md`

Core aim:
This project is a private-first macro and market-cycle radar. Its main purpose is to establish where global equities, major sectors, and Oslo-linked subsectors appear to be in the cycle now, and whether evidence points to continuation, transition, recovery, deterioration, or exit risk. Avoid drifting into non-core indicators. Add data only when it improves cycle-state classification, transition detection, contradiction evidence, confidence, or sector/subsector cycle interpretation.

Current implementation:
- Local Streamlit dashboard.
- DuckDB storage with SQLite fallback.
- Static GitHub Pages report generated from public-safe HTML/JSON/assets.
- Keyless live data refresh using World Bank, DB.nomics OECD CLI mirror, FRED public CSV, Norges Bank, Statistics Norway, selected market-chart proxies, and derived public series.
- Current Sprint 11 state: `schema_version=2026-05-25-sprint11`; latest live target remains `numeric_mode=live_numeric`, 24 live indicators, 0 numeric `sample_fallback`.
- Implemented views: Cycle Status And Transition Synthesis, Historical Charts, Liquidity And Credit, Source Health, Contradicting Evidence, Latest Radar, Changes Since Last Report, Archive, Methodology.
- Implemented data families: growth/turning point, commodity/inflation pressure, rates, FX, liquidity/credit, broad market-pricing proxies, source health, and Oslo-linked subsector proxy scores.
- Implemented synthesis: public-safe `cycle_state` with global equity cycle status, growth, inflation/rates, liquidity/credit, market-pricing/risk-appetite dimensions, Oslo-linked sector read-through, transition/continuation evidence, contradictions, confidence, and missing-data caveats.
- Known gaps: no true valuation multiples; no broad market internals; no analyst revisions/earnings estimates; no true Oslo subsector market histories; reviewed research evidence is still limited.

Important constraints:
- Do not bypass paywalls, CAPTCHAs, bot blocks, or restricted content.
- Do not assume Codex has API keys.
- Keep private notes, credentials, manual reports, raw licensed data, local databases, and unpublished research out of GitHub and public exports.
- Missing dimensions must be shown as missing/proxied/sample-backed.
- The GitHub Pages target must remain static HTML/JSON/assets, not hosted Streamlit.

Next requested sprint:
Sprint 12: Valuation And Market Internals Reality Check.

Add only public-safe valuation, volatility, breadth-like, or risk-appetite proxies that improve:
- cycle-state classification;
- transition or exit-risk detection;
- contradiction evidence;
- confidence/source-health assessment;
- Oslo-linked sector/subsector cycle interpretation.

Keep broad proxies clearly labeled. Do not imply true Oslo subsector valuation multiples, analyst revisions, earnings estimates, positioning, or true subsector histories unless reviewed public or licensed data is connected.

Run tests, build the static site, run static-site QA, update docs, commit, push, dispatch a live GitHub Actions workflow, and verify Pages still shows `live_numeric` with 0 numeric `sample_fallback`.
```
