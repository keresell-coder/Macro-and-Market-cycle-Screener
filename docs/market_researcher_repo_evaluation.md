# Evaluation: Anthropic `market-researcher` Repo Elements

Last updated: 2026-05-23

Source reviewed: <https://github.com/anthropics/financial-services/tree/main/plugins/agent-plugins/market-researcher>

## Bottom Line

It is feasible and relevant to adapt selected concepts from the public `market-researcher` plugin into this dashboard, but it should not be copied as-is.

The plugin is built for analyst-style sector primers: industry overview, competitive landscape, peer comps, idea shortlist, and optional research note/slides. The dashboard's goal is different: continuous macro, geopolitical, and market-cycle monitoring at subsector level, with explainable signals that help decide where to research next.

Recommended approach: adapt the research workflow, schemas, source-quality guardrails, and review discipline; do not make the dashboard depend on paid institutional data connectors or single-name idea generation in the core v1 radar.

## Feasibility

High feasibility for process and data-model elements:

- Add a structured `sector_research` layer per subsector: market structure, value chain, cycle drivers, key debates, catalysts, risks, and source-backed claims.
- Add a research-job workflow that periodically refreshes subsector primers from public sources and owned/manual reports.
- Store extracted claims as structured facts with source, date, confidence, and theme tags.
- Add source-quality hierarchy and source freshness scoring.
- Add human-review status for generated research notes before they affect dashboard scores.
- Add guardrails treating third-party reports and issuer materials as untrusted input.

Medium feasibility for peer-comps concepts:

- Peer comps and valuation outlier logic are relevant, but the referenced plugin assumes CapIQ/FactSet-style data. Without paid feeds, this should be limited to broad sector proxies or manually supplied peer data.
- For Oslo Bors use, peer sets can be useful in drilldowns, but should remain secondary to sector-cycle signals until reliable data sources are available.

Low feasibility for exact managed-agent architecture:

- The repo's managed-agent version uses Claude Managed Agents, CapIQ/FactSet MCP servers, and subagents. This project is currently a local Python/Streamlit app. Recreating that architecture is unnecessary for now.

## Relevance To This Dashboard

Most relevant elements:

- `sector-overview`: highly relevant. Its market structure, key drivers, trends, valuation context, key debates, and catalysts map directly to subsector drilldowns.
- `competitive-analysis`: partly relevant. Useful for subsector structure, value chain maps, basis of competition, and industry-defining metrics. Less central because the dashboard is not a company-positioning deck.
- `idea-generation`: relevant only as a downstream phase. Its "theme to beneficiaries" and "what the market is missing" logic fits the user's goal, but individual stock ideas should remain outside the core dashboard for now.
- `comps-analysis`: relevant later, if reliable market and financial data become available. Its source hierarchy, outlier flags, formulas-over-hardcodes mindset, and audit trail are valuable.
- `pptx-author`: low relevance for the dashboard. Could be useful later for generating sector-primer slide exports, but not needed for the radar.

## Reliability And Credibility

Credibility positives:

- The repo is public under Apache 2.0 and published by Anthropic.
- The repo README explicitly frames the agents as draft analyst work product requiring qualified human review, not autonomous investment advice.
- The `market-researcher` agent includes sensible guardrails: cite every number, treat third-party reports as untrusted, stop for review after important artifacts, and avoid distribution.
- The managed-agent cookbook separates untrusted document reading from writing, and makes only the note-writer able to write files.
- The comps skill strongly prioritizes institutional data sources and warns against using web search as a primary financial-data source.

Reliability limits:

- The plugin is a reference workflow, not validated financial data.
- Its highest-quality outputs depend on paid/institutional data sources such as CapIQ or FactSet.
- Its idea-generation examples are company-level and could drift toward stock recommendations if not constrained.
- Web-derived market-size, share, valuation, and forecast numbers remain weak unless source quality, date, and methodology are captured.
- It is designed for research artifacts, not continuous time-series monitoring or cycle detection.

## Recommended Adaptation

Add a "sector research layer" rather than a full market-researcher agent:

- Define a `subsector_research_profile` schema with:
  - subsector, scope, value chain, key drivers, cycle indicators, current phase hypothesis, bull/base/bear debate, catalysts, risks, source-backed facts, and review status.
- Add a `research_facts` table:
  - claim, source name, source URL or file, source date, captured date, theme, subsector, confidence, and whether it is public/manual/paid.
- Add source hierarchy:
  - official statistics and filings first;
  - company reports and exchange/regulator data;
  - reputable institution research;
  - industry bodies;
  - news only for recent developments and event detection.
- Add dashboard views:
  - "Why now?" panel per subsector.
  - "Key debates" panel with bull/base/bear signposts.
  - "Catalyst watch" panel for events that could change the cycle phase.
  - "Source confidence and freshness" panel.
- Add optional research jobs:
  - weekly subsector primer refresh;
  - event-triggered geopolitical/macro note;
  - quarterly sector-cycle review.

## What Not To Do Yet

- Do not add autonomous single-stock idea generation to the main radar.
- Do not make CapIQ, FactSet, or similar paid feeds required.
- Do not let unsourced web claims change scores automatically.
- Do not publish generated research notes without review.
- Do not implement deck generation before the dashboard and research store are mature.

## Suggested Next Implementation Step

If approved later, implement a first small version:

1. Add `research_facts` and `subsector_research_profiles` tables.
2. Add a manual/public-source ingestion path that extracts source-backed claims but marks them as unreviewed.
3. Add a `Research Evidence` tab in the Streamlit dashboard.
4. Add a `Why now?`, `Key debates`, and `Catalysts` section to each subsector drilldown.
5. Keep generated research evidence separate from numeric scoring until reviewed or until confidence rules are explicit.

