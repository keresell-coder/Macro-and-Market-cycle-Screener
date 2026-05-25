# Next Step Prompt

Copy/paste this into a fresh chat to start the next sprint.

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

Core aim:
Build a private-first macro and market-cycle radar that establishes where global equities, major sectors, and Oslo-linked subsectors appear to be in the cycle now, and whether evidence points to continuation, transition, recovery, deterioration, or exit risk. Do not drift into a broad data catalog. New indicators matter only if they improve cycle-state classification, transition detection, contradiction evidence, confidence, or Oslo-linked sector/subsector cycle interpretation.

Current state:
- Static GitHub Pages report is live.
- Sprint 12 adds public-safe cycle-state synthesis plus broad valuation, volatility, and breadth-like leadership reality checks in `cycle_state`.
- Current schema is `2026-05-25-sprint12`.
- Latest local state is `live_numeric` with 29 live indicators, 0 numeric `sample_fallback`, cycle-state phase `late-cycle/crowded risk`, global equity cycle confidence `high`, and overall synthesis confidence `medium`.
- Current data covers growth/turning point, inflation/commodity pressure, rates, FX, liquidity/credit, market-pricing proxies, broad valuation/market-internals reality checks, source health, and Oslo-linked subsector proxy scores.
- Historical chart layer, liquidity/credit signal group, valuation/market-internals signal group, and Cycle Status And Transition Synthesis section are implemented.
- True Oslo valuation multiples, analyst revisions, earnings estimates, positioning, true breadth, and true subsector market histories remain missing or sample-backed.

Important constraints:
- Do not bypass paywalls, CAPTCHAs, bot blocks, or restricted content.
- Do not assume Codex has API keys.
- Keep private notes, credentials, manual reports, local databases, raw licensed data, and unpublished research out of GitHub and public exports.
- Missing dimensions must be shown as missing/proxied/sample-backed, not treated as neutral.
- Preserve static GitHub Pages HTML/JSON/assets; do not build hosted Streamlit.

Requested next sprint:
Implement Sprint 13: Reviewed Public Research Evidence.

Scope:
1. Keep Sprint 12 `cycle_state` as the top-level report read.
2. Add reviewed public/manual CSV facts only where they clarify subsector cycle phase, transition evidence, contradiction evidence, or caveats.
3. Keep unreviewed claims, private notes, licensed data, and raw report content out of public exports.
4. Do not let unreviewed research claims change numeric scoring.
5. Preserve sample-backed labels where reviewed evidence is still missing.
6. Add tests for evidence ingestion, public-export filtering, source/caveat visibility, and static rendering.
7. Run local tests and static-site QA.
8. Update docs and the continuation prompt after implementation.
9. Commit, push, dispatch a live GitHub Actions workflow, and verify Pages still shows `live_numeric` with 0 numeric `sample_fallback`.

Acceptance:
The report should reduce sample research evidence without weakening the public/private boundary or overstating research precision.
```
