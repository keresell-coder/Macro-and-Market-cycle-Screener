# Open Data Expansion Plan

Last updated: 2026-05-25

## Aim

The radar exists to establish current macro and market-cycle status, then detect continuation, transition, recovery, deterioration, or exit-risk evidence.

Open data expansion should support that aim directly. Do not add indicators just because they are available.

## Operating Model

- Public/open-data first.
- Keyless by default.
- GitHub Actions refreshes data and builds static HTML/JSON.
- GitHub Pages publishes only `exports/site/`.
- Private notes, credentials, manual reports, raw licensed data, local databases, and unreviewed evidence stay out of public exports.

## Indicator Admission Rule

A new source or indicator is useful only if it improves at least one of these:

- cycle-state classification;
- transition or turning-point detection;
- contradiction evidence;
- confidence/source-health assessment;
- Oslo-linked sector/subsector cycle read-through.

Every new connector must include:

- source registry entry;
- clear source-status rows;
- freshness metadata;
- parser tests;
- visible fallback behavior;
- strict live failure on numeric `sample_fallback`;
- public methodology note.

## Current Coverage

Implemented:

- Growth/turning point: OECD CLI mirror via DB.nomics; World Bank annual GDP growth background.
- Inflation/commodity pressure: Norway CPI and World Bank commodity proxies.
- Rates/policy: Norges Bank policy rate and US 10-year proxy.
- Liquidity/credit: Chicago Fed NFCI and St. Louis Fed Financial Stress Index via FRED public CSV.
- Market pricing: selected broad chart proxies.
- Oslo-linked subsector radar: proxy-based scores and sample-backed market-cycle histories.
- Source health: freshness, failures, fallback, and strict live guard.

Still missing or weak:

- valuation and market-internals inputs that can improve the new cycle-state synthesis;
- true market breadth, volatility, positioning, and valuation internals;
- true Oslo subsector valuation multiples;
- analyst revisions, earnings estimates, and margin-cycle data;
- BIS/ECB/Eurostat credit/property/monetary layers;
- reviewed public/manual research evidence.

## Completed Sprints

- Sprint 1: research evidence schema and dashboard display.
- Sprint 2: GitHub/public-private boundary.
- Sprint 3: report-state JSON and change engine.
- Sprint 4: static site generator.
- Sprint 5: GitHub Actions and Pages.
- Sprint 6: source health, freshness, QA, strict fallback guard.
- Sprint 7: proxy-label cleanup and contradiction evidence.
- Sprint 8: OECD CLI growth proxies through DB.nomics.
- Sprint 9: historical chart layer and drilldown.
- Sprint 10: first liquidity/credit proxies through FRED public CSV.
- Sprint 11: cycle status and transition synthesis.

## Next Sprint

### Sprint 12: Valuation And Market Internals Reality Check

Goal:

Add only robust public proxies that improve the Sprint 11 cycle-state synthesis.

Scope:

- Keep the existing `cycle_state` report-state metadata as the top-level conclusion layer.
- Test public valuation, volatility, breadth-like, and risk-appetite proxies only if they improve:
  - cycle-state classification;
  - transition or exit-risk detection;
  - contradiction evidence;
  - confidence/source-health assessment.
- Label broad proxies clearly and do not imply true Oslo subsector valuation multiples.
- Preserve missing/proxied/sample-backed labels in the static report.
- Add tests for any phase, confidence, or contradiction changes caused by the new inputs.

Acceptance:

The report should make the cycle read more robust without becoming a broad market-data catalog or overstating proxy precision.

## Later Sprints

### Sprint 13: Reviewed Research Evidence

Reduce sample research evidence by adding reviewed public/manual CSV facts for priority subsectors. Export reviewed public facts only.

### Sprint 14: Archive, Monitoring, And Deployment Maturity

Improve archive navigation, run-status display, data-vintage summaries, and weekly monitoring after more reports accumulate.

## Candidate Sources For Later Testing

- BIS Data Portal: credit, property prices, debt, global liquidity.
- ECB Data Portal: euro-area monetary/credit/rates data.
- Eurostat: EU macro/regional detail.
- FRED public CSV: selected public market, credit, volatility, or valuation proxies.
- IMF APIs: only after accountless endpoint tests pass.

Sources that are blocked, paywalled, licensed, CAPTCHA-protected, or bot-blocked must not be bypassed.
