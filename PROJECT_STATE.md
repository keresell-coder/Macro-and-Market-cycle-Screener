# Project State: Global Macro, Market and Sector-Cycle Screener

Last updated: 2026-08-21

## Aim and boundary

The screener organizes global macro-financial evidence into separate economic, inflation/rates, liquidity/credit, market-pricing and sector-operating clocks. It ranks sector research priorities; it does not estimate expected returns, provide market timing, or offer investment advice. Oslo-listed subsectors are an implementation lens, not the model's geographic boundary.

## Current implementation

- Report-state schema: `2026-08-21-global-v3`.
- Cycle-state rules: `cycle-state-v3-global-evidence-gated`.
- Scoring: `research-priority-v3-family-weighted-evidence-gated`.
- 51 public indicators, 18 split subsectors, five cycle dimensions and five cycle clocks.
- Strict live builds contain no deterministic numeric or sector-history fallback.
- Public static HTML/JSON plus a one-page PDF, generated locally and by GitHub Actions.
- Scheduled workflow remains active every Saturday at 07:15 UTC; scheduled runs default to live data.

## Live evidence coverage

- OECD CLIs for the G20, G7, US, China and major Europe; World Bank annual GDP as slow background only.
- Twelve-month inflation for Norway, the US, euro area, UK, Japan and China.
- BIS policy rates for the Fed, ECB, BoE, BoJ, PBoC, BoC, RBA, SNB and Riksbank, plus the official Norges Bank key policy rate.
- US nominal/real 10-year yields and 10y-2y curve.
- NFCI, financial stress, high-yield and investment-grade spreads, and broad-dollar liquidity.
- Global, European, Japanese, emerging-market and Nasdaq equity proxies; VIX and equal-weight leadership.
- World Bank commodities, US EIA crude/distillate inventories, NOK FX and the Caldara-Iacoviello Geopolitical Risk Index.

## Institutional outlook governance

Reviewed official publications from the IMF, World Bank, OECD, BIS, BlackRock, J.P. Morgan, Goldman Sachs, Morgan Stanley and Vanguard are stored in `data/public_research_evidence/institutional_outlooks.csv`. Each record carries a publication date, horizon, categorical views, themes, risks, primary-source URL, institution type and source tier. The report shows current dispersion and a dated timeline. These records are attributed context and never affect numeric scoring.

## Evidence and scoring rules

- Indicator labels, units, transformations, polarity and release cadence are explicit contracts.
- Prices use twelve-month returns, CPI indices use twelve-month inflation, OECD CLIs use distance from 100, and zero-centred conditions indices use native standard-deviation levels.
- Momentum is a rolling-mean difference scaled by historical volatility, never percentage change on a zero-centred index.
- Monthly series require at least 36 transformed observations, quarterly 16 and annual eight.
- Stale inputs remain visible but are excluded from scoring.
- Correlated country series first collapse into economic families so adding another country does not silently increase a theme's weight.
- Ambiguous-polarity variables receive no automatic positive tailwind.
- Unreviewed webpage sentiment is disabled.
- Sector rankings are capped at low data support until direct sector evidence is connected.

## Important remaining gaps

- No validated live sector/subsector price, relative-return, valuation, earnings-revision, margin, order-book, breadth or positioning surface.
- No non-US credit-spread catalogue, harmonised global lending surveys, central-bank balance-sheet layer or market-implied policy paths.
- No point-in-time database for an independent predictive backtest. Public report archives support implementation replay and outlook-history accumulation, not forecast validation.
- Institutional outlook agreement is not independent scientific confirmation; financial institutions can share data, assumptions, incentives and consensus bias.

Missing data is a blind spot, never neutral evidence. Live sector phase assertions remain blocked by the direct-evidence gate.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q
PYTHONPATH=src .venv/bin/python -m cycle_screener.refresh
PYTHONPATH=src .venv/bin/python -m cycle_screener.build_static_site --fail-on-numeric-sample-fallback
PYTHONPATH=src .venv/bin/python -m cycle_screener.static_site_qa exports/site
```
