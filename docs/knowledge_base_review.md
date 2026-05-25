# Knowledge-base Review

Last updated: 2026-05-25

Reviewed reference:

- `docs/knowledge_base/global_macro_market_cycle_knowledge_base.md`

## Bottom Line

The knowledge-base direction is right: a useful macro/market-cycle radar must triangulate growth, inflation, policy/rates, liquidity/credit, market pricing, valuation, market internals, sector behavior, and source confidence.

The current project now includes a synthesis layer plus broad valuation, volatility, and breadth-like reality checks. The next important gap is improving the reviewed evidence base behind subsector interpretation, especially earnings, true Oslo-linked valuation, and true subsector histories.

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

## Implemented Well

- Public/keyless data refresh.
- Source health and freshness.
- Static GitHub Pages deployment.
- Public/private boundary.
- Growth proxies through OECD CLI mirror data.
- Liquidity/credit first layer through FRED public CSV.
- Broad public valuation, volatility, and equal-weight leadership reality checks.
- Historical chart layer.
- Contradicting evidence display.
- Framework coverage matrix.
- Transparent subsector scoring.

## Main Remaining Gaps

- The top-level cycle-state synthesis is rule-based and early; it needs more validation over report history.
- Transition warnings now include broad valuation, volatility, and leadership checks, but still lack true breadth, positioning, earnings, and true subsector history inputs.
- No true market breadth or positioning layer.
- No true valuation multiples for Oslo-linked subsectors.
- No analyst earnings revisions or estimate cycle.
- No real subsector price/relative-strength/valuation histories.
- Research evidence still defaults to sample-backed facts unless reviewed local CSV evidence is supplied.

## Recommended Next Step

Implement **Sprint 13: Reviewed Public Research Evidence** next, reducing sample-backed research evidence without weakening the publication boundary.

This should:

- keep the cycle-state object as the primary report conclusion;
- add only analyst-reviewed public/manual facts that clarify subsector cycle phase, transition evidence, contradiction evidence, or caveats;
- export reviewed public facts only;
- keep unreviewed, private, licensed, or restricted evidence local;
- preserve missing/proxied/sample-backed labels.

## Data Expansion Principle

Future market-internals, BIS, ECB, Eurostat, or research-data work should be admitted only when it improves the cycle synthesis.

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
