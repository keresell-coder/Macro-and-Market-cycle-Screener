# Continuation Prompt

Use this prompt to continue in a fresh chat.

```text
You are working in `/Users/ke/Documents/Codex/Macro and Cycle Screener`.

First read:
- `PROJECT_STATE.md`
- `README.md`
- `docs/open_data_expansion_plan.md`
- `docs/knowledge_base_review.md`
- `docs/github_pages_setup.md`
- `docs/publication_policy.md`

Core aim:
This project is a private-first macro and market-cycle radar. Its main purpose is to establish where global equities, major sectors, and Oslo-linked subsectors appear to be in the cycle now, and whether evidence points to continuation, transition, recovery, deterioration, or exit risk. Avoid drifting into non-core indicators. Add data only when it improves cycle-state classification, transition detection, contradiction evidence, confidence, or sector/subsector cycle interpretation.

Current implementation:
Use `PROJECT_STATE.md` as the source of truth for latest schema, live verification, implemented views, data families, known gaps, and next sprint.

Important constraints:
- Do not bypass paywalls, CAPTCHAs, bot blocks, or restricted content.
- Do not assume Codex has API keys.
- Keep private notes, credentials, manual reports, raw licensed data, local databases, and unpublished research out of GitHub and public exports.
- Missing dimensions must be shown as missing/proxied/sample-backed.
- The GitHub Pages target must remain static HTML/JSON/assets, not hosted Streamlit.

Next requested sprint:
Sprint 15: Report-History Validation And Signal Calibration.

Use accumulated public snapshots to review whether phase labels, transition evidence, contradictions, and confidence rules behave coherently over time. Keep it static/public-safe and do not add new indicators unless they directly improve cycle-state validation.

Keep private notes, restricted content, unreviewed claims, and raw licensed material out of public exports. Do not let unreviewed research claims affect numeric scoring.

Run tests, build the static site, run static-site QA, update docs, commit, push, dispatch a live GitHub Actions workflow, and verify Pages still shows `live_numeric` with 0 numeric `sample_fallback`.
```
