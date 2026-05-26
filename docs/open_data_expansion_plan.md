# Open Data Expansion Plan

Last updated: 2026-05-26

## Aim

The radar exists to establish current macro and market-cycle status, then detect continuation, transition, recovery, deterioration, or exit-risk evidence.

Open data expansion should support that aim directly. Do not add indicators just because they are available.

## Operating Model

- Public/open-data first.
- Keyless by default.
- GitHub Actions refreshes data and builds static HTML/JSON.
- GitHub Pages publishes only `exports/site/`.
- Private notes, credentials, manual reports, raw licensed data, local databases, and unreviewed evidence stay out of public exports.
- Current coverage, sprint history, and latest verification live in `PROJECT_STATE.md`.

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

## Current Reviewed Research Evidence Layer

Sprint 13 added committed reviewed public CSV evidence under `data/public_research_evidence/`.

Current scope:

- 13 reviewed public facts, one per Oslo-linked subsector.
- 13 public-reviewed profiles for local dashboard context.
- Facts are claim data only; they do not affect numeric scoring.
- Public exports include reviewed public facts only.

Rules remain:

- Keep unreviewed claims, private notes, licensed data, and raw report content out of public exports.
- Export reviewed public facts only.
- Prioritize facts that clarify sector/subsector cycle phase, transition evidence, contradiction evidence, or missing-data caveats.
- Do not let unreviewed research claims change numeric scoring.

## Current Archive And Monitoring Layer

Sprint 14 added static publication metadata and archive continuity:

- `publication_status` in public report-state JSON.
- Run-status and data-vintage display in the static site.
- Previous `archive.json` reuse in GitHub Actions.
- Archived report-page download before rebuild, so historical report links can persist across static deployments.
- Enhanced archive rows with cycle phase, numeric mode, fallback count, data vintage, and commit metadata.

## Near-Term Admission Priority

### Report-History Validation And Signal Calibration

- Review accumulated public snapshots for phase-label stability.
- Check whether transition and contradiction rules behave coherently as evidence changes.
- Use archive and change-history metadata to identify weak confidence rules.
- BIS, ECB, and Eurostat credit/property/monetary layers remain later candidates only after connector testing proves they improve the cycle read.

## Candidate Sources For Testing

- BIS Data Portal: credit, property prices, debt, global liquidity.
- ECB Data Portal: euro-area monetary/credit/rates data.
- Eurostat: EU macro/regional detail.
- FRED public CSV: selected public market, credit, volatility, or valuation proxies.
- IMF APIs: only after accountless endpoint tests pass.

Sources that are blocked, paywalled, licensed, CAPTCHA-protected, or bot-blocked must not be bypassed.
