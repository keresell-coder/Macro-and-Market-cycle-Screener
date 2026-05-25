# Knowledge-base Review

Last updated: 2026-05-25

Reviewed reference:

- `docs/knowledge_base/global_macro_market_cycle_knowledge_base.md`

## Bottom Line

The knowledge-base direction is right: a useful macro/market-cycle radar must triangulate growth, inflation, policy/rates, liquidity/credit, market pricing, valuation, market internals, sector behavior, and source confidence.

The current project now includes a first synthesis layer. The next important gap is improving the evidence base behind that synthesis, especially valuation, market internals, earnings, and true Oslo-linked subsector histories.

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
- Historical chart layer.
- Contradicting evidence display.
- Framework coverage matrix.
- Transparent subsector scoring.

## Main Remaining Gaps

- The top-level cycle-state synthesis is rule-based and early; it needs more validation over report history.
- Transition warnings now exist, but they still lack valuation, breadth, volatility, positioning, earnings, and true subsector history inputs.
- No broad market internals or breadth layer.
- No true valuation multiples for Oslo-linked subsectors.
- No analyst earnings revisions or estimate cycle.
- No real subsector price/relative-strength/valuation histories.
- Research evidence still defaults to sample-backed facts unless reviewed local CSV evidence is supplied.

## Recommended Next Step

Implement **Sprint 12: Valuation And Market Internals Reality Check** next, adding only data that improves the Sprint 11 synthesis.

This should:

- keep the cycle-state object as the primary report conclusion;
- test public valuation, volatility, breadth-like, and risk-appetite proxies;
- admit new sources only when they improve phase classification, transition warnings, contradictions, or confidence;
- keep broad proxies clearly labeled and avoid implying true Oslo subsector valuation coverage;
- preserve missing/proxied/sample-backed labels.

## Data Expansion Principle

Future valuation, market-internals, BIS, ECB, Eurostat, or research-data work should be admitted only when it improves the cycle synthesis.

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
