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
- Sprint 11 adds public-safe cycle-state synthesis in `cycle_state`.
- Current schema is `2026-05-25-sprint11`.
- Latest live numeric target remains `live_numeric` with 24 live indicators and 0 numeric `sample_fallback`.
- Current data covers growth/turning point, inflation/commodity pressure, rates, FX, liquidity/credit, market-pricing proxies, source health, and Oslo-linked subsector proxy scores.
- Historical chart layer, liquidity/credit signal group, and Cycle Status And Transition Synthesis section are implemented.
- True valuation multiples, market internals, analyst revisions, earnings estimates, positioning, and true subsector market histories remain missing or sample-backed.

Important constraints:
- Do not bypass paywalls, CAPTCHAs, bot blocks, or restricted content.
- Do not assume Codex has API keys.
- Keep private notes, credentials, manual reports, local databases, raw licensed data, and unpublished research out of GitHub and public exports.
- Missing dimensions must be shown as missing/proxied/sample-backed, not treated as neutral.
- Preserve static GitHub Pages HTML/JSON/assets; do not build hosted Streamlit.

Requested next sprint:
Implement Sprint 12: Valuation And Market Internals Reality Check.

Scope:
1. Keep Sprint 11 `cycle_state` as the top-level report read.
2. Evaluate public valuation, volatility, breadth-like, and risk-appetite proxies only if they improve cycle classification, transition warnings, contradictions, or confidence.
3. Do not present broad proxies as true Oslo subsector valuation multiples.
4. Wire admitted indicators through source registry, freshness/source health, static methodology notes, and strict fallback handling.
5. Extend synthesis rules only where new inputs change phase, confidence, contradiction, continuation, or exit-risk evidence.
6. Add tests for connector parsing, phase impact, missing-data handling, contradiction visibility, and static rendering.
7. Run local tests and static-site QA.
8. Update docs and the continuation prompt after implementation.
9. Commit, push, dispatch a live GitHub Actions workflow, and verify Pages still shows `live_numeric` with 0 numeric `sample_fallback`.

Acceptance:
The report should make the Sprint 11 cycle read more robust without turning into a broad data catalog or overstating proxy precision.
```
