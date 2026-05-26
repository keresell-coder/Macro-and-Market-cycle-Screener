# Knowledge-base Review

Last updated: 2026-05-26

Reviewed reference:

- `docs/knowledge_base/global_macro_market_cycle_knowledge_base.md`

## Bottom Line

The knowledge-base direction is right: a useful macro/market-cycle radar must triangulate growth, inflation, policy/rates, liquidity/credit, market pricing, valuation, market internals, sector behavior, and source confidence.

The current implementation state lives in `PROJECT_STATE.md`. This review records only the durable framework judgment: the radar should triangulate growth, inflation, policy/rates, liquidity/credit, market pricing, valuation, market internals, sector behavior, and source confidence.

## Project Objective

The objective is not to collect all possible macro data.

The objective is to classify cycle status and detect transitions:

- global equity cycle;
- major regional/growth cycle;
- liquidity and credit cycle;
- inflation/rates pressure;
- risk appetite and market pricing;
- Oslo-linked sector/subsector phase;
- continuation, recovery, deterioration, exit risk, or uncertainty.

## Main Remaining Gaps

- The top-level cycle-state synthesis is rule-based and needs validation over report history.
- Transition warnings still lack true breadth, positioning, earnings, and true subsector history inputs.
- No true market breadth or positioning layer.
- No true valuation multiples for Oslo-linked subsectors.
- No analyst earnings revisions or estimate cycle.
- No real subsector price/relative-strength/valuation histories.
- Research evidence now includes committed reviewed public CSV facts, but true Oslo valuation, earnings, positioning, and subsector-history inputs remain missing.

## Recommended Next Step

Implement **Sprint 15: Report-History Validation And Signal Calibration** next, using accumulated public snapshots to validate whether phase labels, transition warnings, contradiction evidence, and confidence rules behave coherently over time.

This should:

- keep the cycle-state object as the primary report conclusion;
- use archive and change-history metadata as the validation surface;
- identify weak or unstable confidence rules before adding more indicators;
- preserve strict numeric sample-fallback failure in live builds;
- keep unreviewed, private, licensed, or restricted evidence local;
- preserve missing/proxied/sample-backed labels.

## Data Expansion Principle

Future market-internals, BIS, ECB, Eurostat, or research-data work should be admitted only when it improves the cycle synthesis. Detailed admission rules live in `docs/open_data_expansion_plan.md`.

Good reasons to add a source:

- it clarifies current phase;
- it detects a transition earlier;
- it confirms or contradicts other cycle evidence;
- it improves confidence or freshness;
- it directly improves sector/subsector cycle interpretation.

Weak reasons to add a source:

- it is interesting but not decision-relevant;
- it duplicates an existing proxy without improving confidence;
- it looks precise but is licensed, restricted, stale, or semantically misleading;
- it drifts into single-stock advice.

## Primary-source Concepts Already Reflected

- OECD CLI: useful as qualitative turning-point input, not deterministic forecast.
- Chicago Fed NFCI: tighter/looser financial-conditions proxy.
- BIS financial-cycle work: credit and property cycles matter but require tested connectors.
- NBER cycle dating: useful framework but backward-looking, not a real-time signal.
- GICS/sector taxonomy: useful reference, while this project intentionally uses Oslo-linked custom subsectors.

## Hard Boundaries

Do not promise automatic public coverage for:

- analyst revisions and EPS estimates;
- true Oslo subsector valuation multiples;
- proprietary breadth, positioning, fund-flow, or short-interest data;
- licensed shipping/freight datasets;
- restricted PMI components;
- automated paywalled or bot-blocked research extraction.

These can only enter through reviewed manual inputs or licensed data the user has rights to use.
