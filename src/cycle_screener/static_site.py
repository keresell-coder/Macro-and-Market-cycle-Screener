from __future__ import annotations

from datetime import datetime
from html import escape
import json
from pathlib import Path
from typing import Any

from .config import EXPORT_DIR
from .publication import is_public_export_path
from .source_health import public_health


SIGNAL_LABELS = {
    "cycle_pressure": "Cycle pressure",
    "recovery_potential": "Recovery",
    "valuation_proxy": "Cycle-position discount",
    "momentum": "Momentum",
    "macro_tailwind": "Macro",
    "narrative_divergence": "Narrative gap",
    "data_support": "Data support",
}

SIGNAL_ORDER = tuple(SIGNAL_LABELS)


def build_site_files(
    report_state: dict[str, Any],
    changes: dict[str, Any] | None,
    site_dir: Path | None = None,
    previous_archive_entries: list[dict[str, Any]] | None = None,
) -> dict[str, str | None]:
    output_dir = site_dir or EXPORT_DIR / "site"
    _ensure_public_output(output_dir)

    data_dir = output_dir / "data"
    reports_dir = output_dir / "reports"
    data_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / ".nojekyll").write_text("", encoding="utf-8")

    report_date = _report_date(report_state)
    report_page = reports_dir / f"{report_date}.html"

    _write_json(output_dir / "health.json", public_health(report_state))
    _write_json(data_dir / "report_state.json", report_state)
    _write_json(data_dir / "latest.json", report_state)
    changes_path = data_dir / "changes.json"
    if changes is None:
        changes_path.unlink(missing_ok=True)
    else:
        _write_json(changes_path, changes)

    history_validation_path = data_dir / "history_validation.json"
    _write_json(history_validation_path, report_state.get("report_history_validation", {}))
    archive_entries = _archive_entries(reports_dir, report_page.name, report_state, previous_archive_entries or [])
    _write_json(data_dir / "archive.json", archive_entries)

    index_path = output_dir / "index.html"
    index_path.write_text(
        _render_page(
            report_state=report_state,
            changes=changes,
            archive_entries=archive_entries,
            title="Global Macro, Market and Sector-Cycle Screener",
            page_label="Latest static report",
            data_prefix="data",
            report_prefix="reports",
        ),
        encoding="utf-8",
    )
    report_page.write_text(
        _render_page(
            report_state=report_state,
            changes=changes,
            archive_entries=archive_entries,
            title=f"Weekly Radar Report: {report_date}",
            page_label=f"Report archive: {report_date}",
            data_prefix="../data",
            report_prefix=".",
            home_href="../index.html",
        ),
        encoding="utf-8",
    )

    return {
        "site_index": str(index_path),
        "weekly_report": str(report_page),
        "site_latest": str(data_dir / "latest.json"),
        "site_report_state": str(data_dir / "report_state.json"),
        "site_changes": str(changes_path) if changes is not None else None,
        "history_validation": str(history_validation_path),
        "archive": str(data_dir / "archive.json"),
    }


def _render_page(
    report_state: dict[str, Any],
    changes: dict[str, Any] | None,
    archive_entries: list[dict[str, str]],
    title: str,
    page_label: str,
    data_prefix: str,
    report_prefix: str,
    home_href: str = "#top",
) -> str:
    subsectors = list(report_state.get("subsectors", []))
    research_facts = list(report_state.get("research_facts", []))
    generated_at = _display_datetime(report_state.get("generated_at"))
    data_as_of = escape(str(report_state.get("data_as_of", "unknown")))
    cycle_state = dict(report_state.get("cycle_state", {}))
    pdf_href = "weekly/weekly-cycle-brief.pdf" if data_prefix == "data" else "../weekly/weekly-cycle-brief.pdf"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>{_stylesheet()}</style>
</head>
<body>
  <script id="report-state" type="application/json">{_json_script(report_state)}</script>
  <script id="report-changes" type="application/json">{_json_script(changes or {})}</script>
  <header id="top" class="masthead">
    <div class="masthead__inner">
      <p class="eyebrow">{escape(page_label)}</p>
      <h1>Global Macro, Market and Sector-Cycle Screener</h1>
      <p class="lede">A global view of growth, inflation, major central banks, financial conditions, markets and sector-cycle research priorities - with evidence gaps made explicit.</p>
      <div class="meta-row">
        <span>Generated {generated_at}</span>
        <span>Data as of {data_as_of}</span>
        <span>{len(subsectors)} subsectors</span>
        <a class="meta-link" href="{escape(pdf_href)}">One-page weekly PDF</a>
      </div>
    </div>
  </header>
  <nav class="site-nav" aria-label="Static report views">
    <a href="{escape(home_href)}">Top</a>
    <a href="#now">Now</a>
    <a href="#cycle-map">Cycle Map</a>
    <a href="#subsectors">Subsectors</a>
    <a href="#evidence">Evidence</a>
    <a href="#outlooks">Outlooks</a>
    <a href="#changes">Changes</a>
    <a href="#trust">Trust &amp; Methods</a>
  </nav>
  <main>
    {_health_notice(public_health(report_state))}
    <section id="now" class="decision-section">
      {_render_decision_overview(report_state, changes)}
    </section>

    <section id="cycle-map" class="section">
      <span id="cycle-status" class="anchor-alias" aria-hidden="true"></span>
      <div class="section-heading">
        <p class="eyebrow">Cycle Curve And State Map</p>
        <h2>Where Markets And Subsectors Sit Now</h2>
        <p class="section-intro">A transparent state map, not a forecast of when prices will peak or trough.</p>
      </div>
      {_render_cycle_map(report_state)}
      {_render_cycle_clocks(report_state)}
    </section>

    <section id="subsectors" class="section">
      <div class="section-heading">
        <p class="eyebrow">Oslo-Linked Subsector Signals</p>
        <h2>Research Triggers, Continuation And Risk Alerts</h2>
        <p class="section-intro">Every state includes the evidence boundary and the primary data still missing.</p>
      </div>
      {_render_subsector_cards(report_state)}
      <details class="report-details">
        <summary>Open full research-priority table and signal heatmap</summary>
        <div class="details-body">
          {_render_radar_table(subsectors)}
          <h3>Signal Heatmap</h3>
          {_render_heatmap(subsectors)}
          <h3>Reviewed Research Leads</h3>
          {_render_research_leads(subsectors, research_facts)}
        </div>
      </details>
    </section>

    <section id="evidence" class="section">
      <div class="section-heading">
        <p class="eyebrow">Evidence</p>
        <h2>What Supports Or Contradicts The Read</h2>
      </div>
      {_render_dimension_cards(report_state)}
      <div class="cycle-evidence-grid">
        {_render_cycle_evidence_list("Recovery / Continuation", list(cycle_state.get("continuation_evidence", [])), "No continuation evidence currently dominates.")}
        {_render_cycle_evidence_list("Transition / Exit Risk", list(cycle_state.get("transition_evidence", [])), "No transition evidence currently dominates.")}
        {_render_cycle_evidence_list("Contradictions", list(cycle_state.get("contradictions", [])), "No material cycle contradictions detected.")}
      </div>
      <details class="report-details">
        <summary>Open global and regional historical charts</summary>
        <div class="details-body">{_render_chart_layer(report_state)}</div>
      </details>
      <details class="report-details">
        <summary>Open liquidity, credit and market-internals evidence</summary>
        <div class="details-body">{_render_signal_groups(report_state)}</div>
      </details>
      <details class="report-details">
        <summary>Open full cycle synthesis and Oslo sector read-through</summary>
        <div class="details-body">{_render_cycle_state(report_state)}</div>
      </details>
      <details class="report-details">
        <summary>Open detailed subsector contradictions</summary>
        <div class="details-body">{_render_contradicting_evidence(report_state)}</div>
      </details>
    </section>

    <section id="outlooks" class="section">
      <div class="section-heading">
        <p class="eyebrow">Institutional Outlooks</p>
        <h2>Reviewed Global Views And Scenario Dispersion</h2>
        <p class="section-intro">Official multilateral, BIS, bank and asset-manager publications provide attributed context only. They never enter the numeric score.</p>
      </div>
      {_render_institutional_outlooks(report_state)}
    </section>

    <section id="changes" class="section">
      <div class="section-heading">
        <p class="eyebrow">Changes</p>
        <h2>What Moved</h2>
      </div>
      {_render_changes(changes)}
    </section>

    <section id="trust" class="section section--final">
      <div class="section-heading">
        <p class="eyebrow">Trust And Methods</p>
        <h2>Data Quality, Model Support And Historical Evidence</h2>
      </div>
      {_render_trust_summary(report_state)}
      <details class="report-details">
        <summary>Open source freshness and fallback details</summary>
        <div class="details-body">{_render_source_health(report_state)}</div>
      </details>
      <details class="report-details">
        <summary>Open report-history consistency checks</summary>
        <div class="details-body">{_render_history_validation(report_state)}</div>
      </details>
      <details class="report-details">
        <summary>Open deployment and data-vintage details</summary>
        <div class="details-body">{_render_run_status(report_state, archive_entries)}</div>
      </details>
      <details class="report-details">
        <summary>Open archive</summary>
        <div class="details-body">{_render_archive(archive_entries, report_prefix)}</div>
      </details>
      <details class="report-details">
        <summary>Open full methodology and coverage gaps</summary>
        <div class="details-body">{_render_methodology(report_state, data_prefix)}</div>
      </details>
    </section>
  </main>
</body>
</html>
"""


def _render_decision_overview(
    report_state: dict[str, Any],
    changes: dict[str, Any] | None,
) -> str:
    decision = dict(report_state.get("decision_support", {}))
    global_read = dict(decision.get("global", {}))
    global_cycle = dict(report_state.get("cycle_state", {}).get("global_equity_cycle", {}))
    strategy = str(decision.get("strategy", ""))
    phase = str(global_read.get("phase") or global_cycle.get("phase") or "unknown").replace("_", " ")
    status = str(global_read.get("status") or global_cycle.get("status") or "unknown").replace("_", " ")
    direction = str(global_read.get("direction") or global_cycle.get("direction") or "unknown").replace("_", " ")
    summary = str(global_read.get("summary") or global_cycle.get("summary") or "No cycle summary is available.")
    what_changed = str(global_read.get("what_changed") or "No comparable prior full state was supplied.")
    boundary = str(global_read.get("classification_boundary") or "Require persistence and confirming evidence.")

    return (
        '<div class="decision-hero">'
        '<div class="decision-hero__copy">'
        f'<span class="status-pill">{escape(status)}</span>'
        '<p class="eyebrow">Current Global Equity State</p>'
        f"<h2>{escape(phase)}</h2>"
        f"<p class=\"decision-summary\">{escape(summary)}</p>"
        "</div>"
        '<div class="decision-use-note">'
        "<strong>How this radar is meant to be used</strong>"
        f"<p>{escape(strategy)}</p>"
        "</div>"
        "</div>"
        '<div class="decision-grid">'
        f"{_decision_item('Direction', direction, 'Momentum direction across the five global cycle dimensions.')}"
        f"{_decision_item('What changed', 'Since prior report', what_changed)}"
        f"{_decision_item('What could change the read', 'Classification boundary', boundary)}"
        f"{_decision_item('Data support', str(global_cycle.get('data_support', global_cycle.get('confidence', 'unknown'))).title(), 'Availability, freshness and signal agreement - not a probability that the regime call is correct.')}"
        "</div>"
        f"{_render_trust_summary(report_state, compact=True)}"
    )


def _decision_item(label: str, value: str, detail: str) -> str:
    return (
        '<article class="decision-item">'
        f"<span>{escape(label)}</span>"
        f"<strong>{escape(value)}</strong>"
        f"<p>{escape(detail)}</p>"
        "</article>"
    )


def _render_cycle_map(report_state: dict[str, Any]) -> str:
    decision = dict(report_state.get("decision_support", {}))
    lanes = list(decision.get("phase_lanes", []))
    sectors = list(decision.get("sectors", []))
    subsectors = list(decision.get("subsectors", []))
    global_phase = str(decision.get("global", {}).get("phase", ""))

    curve_segments = "".join(f'<span class="curve-segment curve-segment--{index}"></span>' for index in range(1, 6))
    curve_nodes = []
    lane_cards = []
    for lane in lanes:
        phase = str(lane.get("phase", ""))
        is_current = phase == global_phase
        sector_names = [str(item.get("name", "")) for item in sectors if item.get("phase") == phase]
        subsector_names = [str(item.get("name", "")) for item in subsectors if item.get("phase") == phase]
        marker_label = "Global now" if is_current else str(lane.get("short_label", ""))
        curve_nodes.append(
            f'<div class="curve-node{" curve-node--current" if is_current else ""}" '
            f'style="left:{_num(lane.get("x")):.0f}%;top:{_num(lane.get("y")):.0f}%">'
            '<span class="curve-node__dot"></span>'
            f'<span class="curve-node__label">{escape(str(lane.get("label", "")))}</span>'
            f'<span class="curve-node__hint">{escape(marker_label)}</span>'
            "</div>"
        )
        sector_chips = "".join(f'<span class="map-chip map-chip--sector">{escape(name)}</span>' for name in sector_names)
        subsector_chips = "".join(f'<span class="map-chip">{escape(name)}</span>' for name in subsector_names)
        sector_content = sector_chips or '<span class="muted">None</span>'
        subsector_content = subsector_chips or '<span class="muted">None</span>'
        lane_cards.append(
            f'<article class="phase-lane{" phase-lane--current" if is_current else ""}">'
            f'<span class="phase-lane__action">{escape(str(lane.get("short_label", "")))}</span>'
            f"<h3>{escape(str(lane.get('label', '')))}</h3>"
            f"<p>{escape(str(lane.get('interpretation', '')))}</p>"
            f'<div class="phase-lane__group"><strong>Sectors</strong><div class="chip-row">{sector_content}</div></div>'
            f'<div class="phase-lane__group"><strong>Subsectors</strong><div class="chip-row">{subsector_content}</div></div>'
            "</article>"
        )

    unmatched = [
        str(item.get("name", ""))
        for item in subsectors
        if str(item.get("phase", "")) not in {str(lane.get("phase", "")) for lane in lanes}
    ]
    unmatched_note = (
        f'<p class="warning"><strong>Insufficient evidence:</strong> {escape(", ".join(unmatched))}</p>'
        if unmatched
        else ""
    )
    return (
        '<div class="cycle-map-panel">'
        '<div class="cycle-curve" role="img" aria-label="Cycle curve from deterioration through recovery and continuation to late-cycle and transition">'
        f"{curve_segments}{''.join(curve_nodes)}"
        "</div>"
        f'<p class="curve-boundary">{escape(str(decision.get("curve_boundary", "")))}</p>'
        f'<div class="phase-lane-grid">{"".join(lane_cards)}</div>'
        f"{unmatched_note}"
        "</div>"
    )


def _render_subsector_cards(report_state: dict[str, Any]) -> str:
    subsectors = list(report_state.get("decision_support", {}).get("subsectors", []))
    if not subsectors:
        return '<p class="empty-state">No subsector decision-support records are available.</p>'

    cards = []
    for item in subsectors:
        signals = dict(item.get("signals", {}))
        phase = str(item.get("phase", "unknown")).replace("_", " ")
        reviewed_facts = list(item.get("reviewed_public_facts", []))
        fact_items = "".join(
            "<li>"
            f"<span>{escape(str(fact.get('claim', '')))}</span>"
            f"<small>{_source_link(fact)} · {escape(str(fact.get('source_date', 'unknown date')))}</small>"
            "</li>"
            for fact in reviewed_facts
        )
        fact_block = (
            '<div class="subsector-facts"><strong>Reviewed public context - non-scoring</strong>'
            f"<ul>{fact_items}</ul></div>"
            if fact_items
            else '<div class="subsector-facts"><strong>Reviewed public context</strong><p>No reviewed public fact in this snapshot.</p></div>'
        )
        cards.append(
            '<details class="subsector-card">'
            "<summary>"
            '<div class="subsector-card__identity">'
            f"<span>{escape(str(item.get('group_name', '')))}</span>"
            f"<strong>{escape(str(item.get('name', '')))}</strong>"
            "</div>"
            '<div class="subsector-card__badges">'
            f'<span class="phase-badge">{escape(phase)}</span>'
            f'<span class="direction-badge">{escape(str(item.get("direction", "unknown")).replace("_", " "))}</span>'
            f'<span class="priority-badge">{escape(str(item.get("research_priority_band", "watch")))}</span>'
            "</div>"
            "</summary>"
            '<div class="subsector-card__body">'
            f'<p class="stance"><strong>Investor stance:</strong> {escape(str(item.get("investor_stance", "")))}</p>'
            f"<p>{escape(str(item.get('synthesis', '')))}</p>"
            '<dl class="signal-strip">'
            f"<div><dt>Recovery</dt><dd>{_signed(signals.get('recovery'))}</dd></div>"
            f"<div><dt>Momentum</dt><dd>{_signed(signals.get('momentum'))}</dd></div>"
            f"<div><dt>Macro</dt><dd>{_signed(signals.get('macro'))}</dd></div>"
            f"<div><dt>Cycle-position discount</dt><dd>{_signed(signals.get('cycle_position_discount'))}</dd></div>"
            "</dl>"
            '<div class="subsector-read-grid">'
            f'<div><strong>Confirmation needed</strong><p>{escape(str(item.get("confirmation_needed", "")))}</p></div>'
            f'<div><strong>Primary data gap</strong><p>{escape(str(item.get("primary_data_gap", "")))}</p></div>'
            "</div>"
            f"{fact_block}"
            '<p class="evidence-boundary">'
            f"<strong>Evidence boundary:</strong> {escape(str(item.get('evidence_boundary', '')))}. "
            f"Signal-data quality {escape(str(item.get('signal_data_quality', 'unknown')))}; "
            f"{int(_num(item.get('reviewed_public_fact_count')))} reviewed public fact(s); "
            f"{int(_num(item.get('contradiction_count')))} active contradiction(s)."
            "</p>"
            "</div>"
            "</details>"
        )
    return f'<div class="subsector-list">{"".join(cards)}</div>'


def _render_cycle_clocks(report_state: dict[str, Any]) -> str:
    clocks = list(report_state.get("cycle_state", {}).get("cycle_clocks", []))
    if not clocks:
        return '<p class="empty-state">No cycle-clock synthesis is available.</p>'
    cards = []
    for clock in clocks:
        cards.append(
            '<article class="dimension-card">'
            f'<span class="dimension-card__phase">{escape(str(clock.get("status", "unknown")).replace("_", " "))}</span>'
            f'<h3>{escape(str(clock.get("title", "")))}</h3>'
            f'<p>{escape(str(clock.get("interpretation", "")))}</p>'
            '<dl class="mini-stats">'
            f'<div><dt>Score</dt><dd>{_signed(clock.get("score"))}</dd></div>'
            f'<div><dt>Direction</dt><dd>{escape(str(clock.get("direction", "unknown")))}</dd></div>'
            f'<div><dt>Data support</dt><dd>{escape(str(clock.get("data_support", "unknown")))}</dd></div>'
            '</dl>'
            '</article>'
        )
    return '<h3 class="subsection-title">Separate cycle clocks</h3>' + f'<div class="dimension-grid">{"".join(cards)}</div>'


def _render_dimension_cards(report_state: dict[str, Any]) -> str:
    dimensions = list(report_state.get("cycle_state", {}).get("dimensions", []))
    cards = []
    for item in dimensions:
        coverage = dict(item.get("coverage", {}))
        cards.append(
            '<article class="dimension-card">'
            f'<span class="dimension-card__phase">{escape(str(item.get("phase", "")).replace("_", " "))}</span>'
            f"<h3>{escape(str(item.get('title', '')))}</h3>"
            f"<p>{escape(str(item.get('status', '')).replace('_', ' '))}; {escape(str(item.get('direction', '')).replace('_', ' '))}.</p>"
            '<dl class="mini-stats">'
            f"<div><dt>Score</dt><dd>{_signed(item.get('score'))}</dd></div>"
            f"<div><dt>Data coverage</dt><dd>{escape(str(item.get('confidence', 'unknown')))}</dd></div>"
            f"<div><dt>Inputs</dt><dd>{int(_num(coverage.get('available_count')))} / {int(_num(coverage.get('expected_count')))}</dd></div>"
            "</dl>"
            "</article>"
        )
    return f'<div class="dimension-grid">{"".join(cards)}</div>'


def _render_trust_summary(report_state: dict[str, Any], compact: bool = False) -> str:
    trust = dict(report_state.get("decision_support", {}).get("trust", {}))
    numeric = dict(report_state.get("source_health", {}).get("numeric", {}))
    research_pages = dict(report_state.get("source_health", {}).get("research_pages", {}))
    cards = []
    for key, title in (
        ("data_quality", "Usable source coverage"),
        ("model_support", "Model support"),
        ("historical_validation", "Predictive validation"),
    ):
        item = dict(trust.get(key, {}))
        cards.append(
            '<article class="trust-card">'
            f"<span>{escape(title)}</span>"
            f"<strong>{escape(str(item.get('label', 'unknown')).replace('_', ' '))}</strong>"
            f"<p>{escape(str(item.get('detail', '')))}</p>"
            "</article>"
        )
    impact = (
        '<div class="trust-impact">'
        "<strong>Issue impact is kept separate</strong>"
        f"<span><b>{int(_num(numeric.get('sample_fallback_indicator_count')))}</b> scoring-data fallback</span>"
        f"<span><b>{int(_num(numeric.get('stale_indicator_count')))}</b> stale numeric series</span>"
        f"<span><b>{int(_num(research_pages.get('failed_count')))}</b> non-scoring research-page failure</span>"
        "</div>"
    )
    boundary = (
        '<p class="trust-boundary"><strong>Interpretation boundary:</strong> Source coverage does not imply '
        "high empirical confidence. Model support describes signal agreement; archive coverage describes stored snapshots, not independent outcome evidence.</p>"
    )
    css_class = "trust-summary trust-summary--compact" if compact else "trust-summary"
    return f'<div class="{css_class}"><div class="trust-grid">{"".join(cards)}</div>{impact}{boundary}</div>'


def _render_radar_table(subsectors: list[dict[str, Any]]) -> str:
    rows = []
    for item in subsectors:
        signals = item.get("signals", {})
        rows.append(
            "<tr>"
            f"<td class=\"rank\">{_fmt(item.get('rank'), 0)}</td>"
            f"<td><strong>{escape(str(item.get('name', '')))}</strong><span>{escape(str(item.get('group_name', '')))}</span></td>"
            f"<td>{escape(str(item.get('cycle_phase', 'unknown')).replace('_', ' '))}<span>{escape(str(item.get('cycle_direction', 'unknown')).replace('_', ' '))}</span></td>"
            f"<td>{_score_bar(item.get('research_priority_score', item.get('opportunity_score')))}</td>"
            f"<td>{_signed(signals.get('recovery_potential'))}</td>"
            f"<td>{_signed(signals.get('valuation_proxy'))}</td>"
            f"<td>{_signed(signals.get('momentum'))}</td>"
            f"<td>{_pct(item.get('data_support', signals.get('data_support')))}</td>"
            f"<td>{escape(str(item.get('explanation', '')))}</td>"
            "</tr>"
        )
    return (
        '<div class="table-wrap"><table class="radar-table">'
        "<thead><tr><th>Research rank</th><th>Subsector</th><th>Evidence-gated state</th><th>Research priority</th><th>Recovery</th><th>Cycle-position discount</th><th>Momentum</th><th>Data support</th><th>Read-through</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div>"
    )


def _render_heatmap(subsectors: list[dict[str, Any]]) -> str:
    header = "".join(f"<th>{escape(label)}</th>" for label in SIGNAL_LABELS.values())
    rows = []
    for item in subsectors:
        cells = "".join(_signal_cell(signal, item.get("signals", {}).get(signal)) for signal in SIGNAL_ORDER)
        rows.append(f"<tr><th>{escape(str(item.get('name', '')))}</th>{cells}</tr>")
    return f'<div class="table-wrap"><table class="heatmap"><thead><tr><th>Subsector</th>{header}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def _render_research_leads(subsectors: list[dict[str, Any]], research_facts: list[dict[str, Any]]) -> str:
    facts_by_slug: dict[str, list[dict[str, Any]]] = {}
    for fact in research_facts:
        facts_by_slug.setdefault(str(fact.get("subsector_slug", "")), []).append(fact)

    blocks = []
    for item in subsectors[:5]:
        slug = str(item.get("slug", ""))
        facts = facts_by_slug.get(slug, [])[:3]
        cycle = item.get("market_cycle", {})
        fact_list = "".join(f"<li>{escape(str(fact.get('claim', '')))} {_source_link(fact)}</li>" for fact in facts)
        if not fact_list:
            fact_list = "<li>No reviewed public facts in this snapshot.</li>"
        blocks.append(
            '<article class="lead-item">'
            f"<h4>{escape(str(item.get('name', '')))}</h4>"
            f"<p>{escape(str(item.get('explanation', '')))}</p>"
            '<dl class="mini-stats">'
            f"<div><dt>Relative price</dt><dd>{_fmt(cycle.get('relative_price_index'), 1)}</dd></div>"
            f"<div><dt>Sample cycle-position proxy</dt><dd>{_fmt(cycle.get('valuation_proxy'), 1)}</dd></div>"
            f"<div><dt>Driver pressure</dt><dd>{_signed(cycle.get('driver_pressure'))}</dd></div>"
            "</dl>"
            f"<ul>{fact_list}</ul>"
            "</article>"
        )
    return f'<div class="lead-grid">{"".join(blocks)}</div>'


def _render_chart_layer(report_state: dict[str, Any]) -> str:
    layer = dict(report_state.get("chart_layer", {}))
    views = list(layer.get("views", []))
    if not views:
        return '<p class="empty-state">No historical chart metadata is available in this report snapshot.</p>'

    global_view_id = str(layer.get("global_view_id", "global"))
    global_view = next((view for view in views if view.get("view_id") == global_view_id), views[0])
    regional_views = [view for view in views if view is not global_view]
    sector_views = list(layer.get("sector_views", []))
    coverage_notes = list(layer.get("coverage_notes", []))

    coverage_items = "".join(
        "<li>"
        f"<strong>{escape(str(item.get('dimension', '')))}:</strong> "
        f"{escape(str(item.get('status', '')).replace('_', ' '))}. "
        f"{escape(str(item.get('note', '')))}"
        "</li>"
        for item in coverage_notes
    )
    coverage_block = f"<ul class=\"chart-notes\">{coverage_items}</ul>" if coverage_items else ""

    regional_blocks = "".join(
        "<details class=\"chart-details\">"
        f"<summary>{escape(str(view.get('title', 'Regional chart')))}</summary>"
        f"{_render_chart_view(view)}"
        "</details>"
        for view in regional_views
    )
    sector_blocks = "".join(_render_sector_chart_view(sector) for sector in sector_views)

    return (
        '<div class="chart-layer-intro">'
        f"<p>{escape(str(layer.get('summary', 'Historical charts use current report-state data.')))}</p>"
        f"<p class=\"muted\">{escape(str(layer.get('normalization', 'Chart lines are normalized where needed.')))}</p>"
        "</div>"
        f"{_render_chart_view(global_view, featured=True)}"
        "<h3>Regional Drilldown</h3>"
        f"{regional_blocks or '<p class=\"empty-state\">No regional chart views are available.</p>'}"
        "<h3>Sector And Subsector Drilldown</h3>"
        f"{sector_blocks or '<p class=\"empty-state\">No sector chart views are available.</p>'}"
        "<h3>Chart Coverage Notes</h3>"
        f"{coverage_block}"
    )


def _render_sector_chart_view(sector: dict[str, Any]) -> str:
    subsectors = list(sector.get("subsectors", []))
    cards = []
    for subsector in subsectors:
        cards.append(
            '<article class="subsector-chart-card">'
            f"<h4>{escape(str(subsector.get('subsector_name', '')))}</h4>"
            f"<p class=\"muted\">{escape(str(subsector.get('data_boundary', '')))}</p>"
            f"{_render_chart_view(dict(subsector.get('proxy_view', {})), compact=True)}"
            f"{_render_chart_view(dict(subsector.get('market_view', {})), compact=True)}"
            f"{_render_chart_view(dict(subsector.get('driver_view', {})), compact=True)}"
            "</article>"
        )
    return (
        "<details class=\"chart-details\">"
        f"<summary>{escape(str(sector.get('group_name', 'Sector')))}</summary>"
        f"<p class=\"muted\">{escape(str(sector.get('description', '')))}</p>"
        f"<div class=\"subsector-chart-grid\">{''.join(cards)}</div>"
        "</details>"
    )


def _render_chart_view(view: dict[str, Any], featured: bool = False, compact: bool = False) -> str:
    series = list(view.get("series", []))
    missing = list(view.get("missing_series", []))
    title = escape(str(view.get("title", "Chart view")))
    description = escape(str(view.get("description", "")))
    css_class = "chart-card chart-card--featured" if featured else "chart-card"
    if compact:
        css_class += " chart-card--compact"
    missing_block = ""
    if missing:
        missing_items = "".join(
            f"<li>{escape(str(item.get('label', item.get('series_id', ''))))}: {escape(str(item.get('message', 'missing')))}</li>"
            for item in missing
        )
        missing_block = f"<ul class=\"chart-missing\">{missing_items}</ul>"
    return (
        f"<article class=\"{css_class}\">"
        f"<div class=\"chart-card__heading\"><h4>{title}</h4><p>{description}</p></div>"
        f"{_render_chart_window_note(dict(view.get('chart_window', {})))}"
        f"{_render_line_chart(series, title, dict(view.get('chart_window', {})))}"
        f"{_render_chart_metadata(series, compact=compact)}"
        f"{missing_block}"
        "</article>"
    )


def _render_chart_window_note(chart_window: dict[str, Any]) -> str:
    if not chart_window or not chart_window.get("start") or not chart_window.get("end"):
        return ""
    short = list(chart_window.get("short_history_series", []))
    short_note = ""
    if short:
        labels = ", ".join(str(item.get("label") or item.get("series_id", "")) for item in short[:4])
        remaining = len(short) - 4
        if remaining > 0:
            labels = f"{labels}, and {remaining} more"
        short_note = f" Short-history series flagged: {labels}."
    return (
        '<p class="chart-window-note">'
        f"Chart window: {escape(str(chart_window.get('start')))} to {escape(str(chart_window.get('end')))} "
        f"({escape(_fmt(chart_window.get('year_span'), 1))} years; policy {int(_num(chart_window.get('minimum_years')))}-{int(_num(chart_window.get('maximum_years')))} years)."
        f"{escape(short_note)}"
        "</p>"
    )


def _render_line_chart(series: list[dict[str, Any]], title: str, chart_window: dict[str, Any] | None = None) -> str:
    plottable = [item for item in series if item.get("points")]
    if not plottable:
        return '<p class="empty-state">No chartable points are available for this view.</p>'

    width = 760
    height = 280
    left = 50
    right = 18
    top = 18
    bottom = 42
    plot_width = width - left - right
    plot_height = height - top - bottom
    date_values: list[datetime] = []
    y_values: list[float] = []
    for item in plottable:
        for point in item.get("points", []):
            parsed_date = _parse_date(point.get("date"))
            if parsed_date is None:
                continue
            date_values.append(parsed_date)
            y_values.append(_num(point.get("chart_value")))
    if not date_values or not y_values:
        return '<p class="empty-state">No chartable points are available for this view.</p>'

    window_start = _parse_date((chart_window or {}).get("start"))
    window_end = _parse_date((chart_window or {}).get("end"))
    min_date = window_start or min(date_values)
    max_date = window_end or max(date_values)
    min_y = min(y_values)
    max_y = max(y_values)
    if abs(max_y - min_y) < 1e-9:
        min_y -= 1
        max_y += 1
    padding = (max_y - min_y) * 0.08
    min_y -= padding
    max_y += padding
    date_span = max((max_date - min_date).days, 1)

    colors = ("#207857", "#246389", "#b2822b", "#ac4b3a", "#5b5f97", "#7a6a2f", "#168aad", "#7b2d26", "#4f772d")
    polylines = []
    legend = []
    for idx, item in enumerate(plottable):
        color = colors[idx % len(colors)]
        coords = []
        for point in item.get("points", []):
            parsed_date = _parse_date(point.get("date"))
            if parsed_date is None:
                continue
            x = left + ((parsed_date - min_date).days / date_span) * plot_width
            y = top + (max_y - _num(point.get("chart_value"))) / (max_y - min_y) * plot_height
            coords.append(f"{x:.1f},{y:.1f}")
        if len(coords) >= 2:
            polylines.append(f'<polyline points="{" ".join(coords)}" fill="none" stroke="{color}" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round" />')
        legend.append(
            f'<span><i style="background:{color}"></i>{escape(str(item.get("label", item.get("series_id", ""))))}</span>'
        )

    grid_lines = []
    for step in range(5):
        y = top + (plot_height / 4) * step
        value = max_y - ((max_y - min_y) / 4) * step
        grid_lines.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}" class="chart-grid-line" />'
            f'<text x="{left - 8}" y="{y + 4:.1f}" class="chart-axis-label" text-anchor="end">{value:.1f}</text>'
        )
    axis = (
        f'<line x1="{left}" y1="{height - bottom}" x2="{width - right}" y2="{height - bottom}" class="chart-axis-line" />'
        f'<text x="{left}" y="{height - 14}" class="chart-axis-label" text-anchor="start">{escape(min_date.date().isoformat())}</text>'
        f'<text x="{width - right}" y="{height - 14}" class="chart-axis-label" text-anchor="end">{escape(max_date.date().isoformat())}</text>'
    )

    return (
        '<div class="svg-chart-wrap">'
        f'<svg class="line-chart" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">'
        f"<rect x=\"0\" y=\"0\" width=\"{width}\" height=\"{height}\" rx=\"8\" class=\"chart-bg\" />"
        f"{''.join(grid_lines)}{axis}{''.join(polylines)}"
        "</svg>"
        f'<div class="chart-legend">{"".join(legend)}</div>'
        "</div>"
    )


def _render_chart_metadata(series: list[dict[str, Any]], compact: bool = False) -> str:
    if not series:
        return ""
    rows = []
    display_series = series if not compact else series[:6]
    for item in display_series:
        status = str(item.get("proxy_status", "")).replace("_", " ")
        data_class = str(item.get("data_class", "")).replace("_", " ")
        scoring = "yes" if item.get("scoring_inclusion") else "no"
        legacy = str(item.get("legacy_slug") or "")
        slug = str(item.get("series_id", ""))
        label = slug if not legacy else f"{slug} (legacy: {legacy})"
        rows.append(
            "<tr>"
            f"<td><strong>{escape(str(item.get('label', '')))}</strong><span>{escape(label)}</span></td>"
            f"<td>{escape(str(item.get('source', '')))}</td>"
            f"<td>{escape(str(item.get('latest_observed_at', '')))}</td>"
            f"<td>{escape(str(item.get('frequency', '')))}</td>"
            f"<td>{escape(data_class)}</td>"
            f"<td>{escape(status)}</td>"
            f"<td>{escape(scoring)}</td>"
            "</tr>"
        )
    if compact and len(series) > len(display_series):
        rows.append(f"<tr><td colspan=\"7\">{len(series) - len(display_series)} additional series in JSON metadata.</td></tr>")
    return (
        '<div class="table-wrap chart-meta-wrap"><table class="chart-meta-table">'
        "<thead><tr><th>Series</th><th>Source</th><th>Vintage</th><th>Frequency</th><th>Data class</th><th>Proxy/sample status</th><th>Scored</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div>"
    )


def _render_source_health(report_state: dict[str, Any]) -> str:
    health = dict(report_state.get("source_health", {}))
    numeric = dict(health.get("numeric", {}))
    pages = dict(health.get("research_pages", {}))
    evidence = dict(health.get("research_evidence", {}))
    freshness = list(report_state.get("source_freshness", []))

    fallback_indicators = numeric.get("sample_fallback_indicators", []) or []
    stale_indicators = numeric.get("stale_indicators", []) or []
    failed_sources = pages.get("failed_sources", []) or []
    numeric_mode = str(numeric.get("mode", "unknown")).replace("_", " ")

    status_cards = (
        '<div class="summary-grid summary-grid--compact">'
        f"{_metric('Usable numeric coverage', str(numeric.get('usable_indicator_count', 0)) + '/' + str(numeric.get('configured_indicator_count', 0)), 'Source status: ' + str(numeric.get('status', 'unknown')))}"
        f"{_metric('Numeric sample fallback', str(numeric.get('sample_fallback_indicator_count', 0)), _join_or_none(fallback_indicators))}"
        f"{_metric('Non-scoring research page failures', str(pages.get('failed_count', 0)), _join_or_none([item.get('source_slug', '') for item in failed_sources]))}"
        f"{_metric('Research evidence fallback', 'Yes' if evidence.get('fallback_used') else 'No', str(evidence.get('message', '') or evidence.get('mode', 'unknown')))}"
        "</div>"
    )

    alerts = []
    if fallback_indicators:
        alerts.append(f"<p class=\"warning\"><strong>Numeric sample fallback used:</strong> {_join_or_none(fallback_indicators)}.</p>")
    if stale_indicators:
        alerts.append(f"<p class=\"warning\"><strong>Stale numeric indicators:</strong> {_join_or_none(stale_indicators)}.</p>")
    if failed_sources:
        items = "".join(
            f"<li><strong>{escape(str(item.get('source_slug', '')))}</strong>: {escape(str(item.get('message', '')))}</li>"
            for item in failed_sources
        )
        alerts.append(f"<div class=\"warning\"><strong>Research pages that could not be scanned</strong><ul>{items}</ul></div>")
    if evidence.get("fallback_used"):
        alerts.append(f"<p class=\"warning\"><strong>Research-evidence fallback:</strong> {escape(str(evidence.get('message', 'sample evidence used')))}.</p>")

    rows = []
    for item in freshness:
        display_slug = str(item.get("display_slug") or item.get("indicator_slug", ""))
        legacy_slug = str(item.get("legacy_slug") or "")
        slug_label = display_slug if not legacy_slug else f"{display_slug} (legacy: {legacy_slug})"
        rows.append(
            "<tr>"
            f"<td><strong>{escape(str(item.get('indicator_name', item.get('indicator_slug', ''))))}</strong><span>{escape(slug_label)}</span></td>"
            f"<td>{escape(str(item.get('latest_observed_at') or 'missing'))}<span>Reference period: {escape(str(item.get('observation_period_start') or 'unknown'))} to {escape(str(item.get('observation_period_end') or 'unknown'))}</span></td>"
            f"<td>{_fmt(item.get('age_days'), 0)}</td>"
            f"<td>{escape(str(item.get('source_category', '')).replace('_', ' '))}</td>"
            f"<td>{escape(str(item.get('exclusion_reason', '')).replace('_', ' '))}<span>Release allowance: {item.get('expected_release_days', '?')} days after reference period</span></td>"
            "</tr>"
        )

    table = (
        '<div class="table-wrap"><table class="freshness-table">'
        "<thead><tr><th>Indicator</th><th>Latest observation</th><th>Age days</th><th>Data class</th><th>Freshness</th></tr></thead>"
        f"<tbody>{''.join(rows) or '<tr><td colspan=\"5\">No numeric freshness metadata available.</td></tr>'}</tbody></table></div>"
    )

    return status_cards + "".join(alerts) + table


def _render_run_status(report_state: dict[str, Any], archive_entries: list[dict[str, Any]]) -> str:
    publication = dict(report_state.get("publication_status", {}))
    run = dict(publication.get("run", {}))
    source_health = dict(report_state.get("source_health", {}))
    numeric = dict(source_health.get("numeric", {}))
    evidence = dict(source_health.get("research_evidence", {}))
    cycle_state = dict(report_state.get("cycle_state", {}))
    confidence = dict(cycle_state.get("confidence", {}))
    run_url = str(run.get("run_url", ""))
    run_label = str(run.get("run_id", "")) or "local"
    run_value = f'<a href="{escape(run_url)}">{escape(run_label)}</a>' if run_url.startswith("https://") else escape(run_label)
    commit = str(run.get("commit_sha", ""))
    commit_short = commit[:7] if commit else "local"
    archive_dates = [str(item.get("date", "")) for item in archive_entries if item.get("date")]
    archive_detail = f"{archive_dates[-1]} to {archive_dates[0]}" if len(archive_dates) > 1 else (archive_dates[0] if archive_dates else "current report only")
    data_vintage_detail = f"Generated {_display_datetime(report_state.get('generated_at'))}"
    numeric_detail = f"{numeric.get('live_indicator_count', 0)} live, {numeric.get('sample_fallback_indicator_count', 0)} numeric fallback"

    cards = (
        '<div class="summary-grid summary-grid--compact">'
        f"{_metric('Build status', str(publication.get('status', 'unknown')).replace('_', ' '), str(publication.get('site_target', 'static site')))}"
        f"{_metric('Build mode', str(publication.get('build_mode', 'unknown')), 'Strict fallback guard on' if publication.get('strict_numeric_sample_fallback_guard') else 'Strict fallback guard off')}"
        f"{_metric('Data vintage', str(report_state.get('data_as_of', 'unknown')), data_vintage_detail)}"
        f"{_metric('Numeric mode', str(numeric.get('mode', 'unknown')).replace('_', ' '), numeric_detail)}"
        f"{_metric('Research evidence', 'fallback' if evidence.get('fallback_used') else 'structured', str(evidence.get('message', evidence.get('mode', ''))))}"
        f"{_metric('Archive coverage', str(len(archive_entries)), archive_detail)}"
        "</div>"
    )

    details = (
        '<div class="run-status-grid">'
        '<article class="status-panel">'
        "<h3>Publication Run</h3>"
        '<dl class="mini-stats mini-stats--wide">'
        f"<div><dt>Provider</dt><dd>{escape(str(run.get('provider', 'local')))}</dd></div>"
        f"<div><dt>Workflow run</dt><dd>{run_value}</dd></div>"
        f"<div><dt>Ref</dt><dd>{escape(str(run.get('ref', '')) or 'local')}</dd></div>"
        f"<div><dt>Commit</dt><dd>{escape(commit_short)}</dd></div>"
        "</dl>"
        f"<p class=\"muted\">{escape(str(publication.get('status_summary', 'Static report generated.')))}</p>"
        "</article>"
        '<article class="status-panel">'
        "<h3>Monitoring Snapshot</h3>"
        "<ul>"
        f"<li>Previous report state supplied: {escape('yes' if publication.get('previous_report_state_supplied') else 'no')}.</li>"
        f"<li>Previous archive supplied: {escape('yes' if publication.get('previous_archive_supplied') else 'no')}.</li>"
        f"<li>Model support: {escape(str(confidence.get('label', 'unknown')))} ({_fmt(confidence.get('score'), 3)}); not empirical accuracy.</li>"
        f"<li>Research evidence fallback: {escape('yes' if evidence.get('fallback_used') else 'no')}.</li>"
        "</ul>"
        "</article>"
        "</div>"
    )
    return cards + details


def _render_cycle_state(report_state: dict[str, Any]) -> str:
    cycle_state = dict(report_state.get("cycle_state", {}))
    if not cycle_state:
        return '<p class="empty-state">No cycle-state synthesis is available in this report snapshot.</p>'

    global_cycle = dict(cycle_state.get("global_equity_cycle", {}))
    confidence = dict(cycle_state.get("confidence", {}))
    dimensions = list(cycle_state.get("dimensions", []))
    oslo_groups = list(cycle_state.get("oslo_sector_read_through", []))
    transitions = list(cycle_state.get("transition_evidence", []))
    continuation = list(cycle_state.get("continuation_evidence", []))
    contradictions = list(cycle_state.get("contradictions", []))
    caveats = list(cycle_state.get("missing_data_caveats", []))

    header = (
        '<article class="cycle-headline">'
        '<div>'
        '<p class="eyebrow">Global Equity Cycle</p>'
        f"<h3>{escape(str(global_cycle.get('phase', 'unknown')).replace('_', ' '))}</h3>"
        f"<p>{escape(str(global_cycle.get('summary', 'No summary available.')))}</p>"
        "</div>"
        '<dl class="mini-stats mini-stats--wide">'
        f"<div><dt>Status</dt><dd>{escape(str(global_cycle.get('status', 'unknown')).replace('_', ' '))}</dd></div>"
        f"<div><dt>Direction</dt><dd>{escape(str(global_cycle.get('direction', 'unknown')).replace('_', ' '))}</dd></div>"
        f"<div><dt>Score</dt><dd>{_signed(global_cycle.get('score'))}</dd></div>"
        f"<div><dt>Data coverage</dt><dd>{escape(str(global_cycle.get('confidence', 'unknown')))}</dd></div>"
        "</dl>"
        "</article>"
    )

    dimension_rows = []
    for item in dimensions:
        coverage = dict(item.get("coverage", {}))
        evidence = list(item.get("evidence", []))[:3]
        evidence_text = "; ".join(
            f"{str(point.get('indicator_name', point.get('indicator_slug', '')))} {_signed(point.get('score'))}"
            for point in evidence
        )
        dimension_rows.append(
            "<tr>"
            f"<td><strong>{escape(str(item.get('title', '')))}</strong><span>{escape(str(item.get('description', '')))}</span></td>"
            f"<td>{escape(str(item.get('phase', '')).replace('_', ' '))}</td>"
            f"<td>{escape(str(item.get('status', '')).replace('_', ' '))}</td>"
            f"<td>{escape(str(item.get('direction', '')).replace('_', ' '))}</td>"
            f"<td>{_signed(item.get('score'))}</td>"
            f"<td>{escape(str(item.get('confidence', '')))}<span>{int(_num(coverage.get('available_count')))} of {int(_num(coverage.get('expected_count')))} inputs</span></td>"
            f"<td>{escape(evidence_text or 'No evidence points available.')}</td>"
            "</tr>"
        )
    dimension_table = (
        '<div class="table-wrap"><table class="cycle-table">'
        "<thead><tr><th>Dimension</th><th>Phase</th><th>Status</th><th>Direction</th><th>Score</th><th>Data coverage</th><th>Largest evidence points</th></tr></thead>"
        f"<tbody>{''.join(dimension_rows) or '<tr><td colspan=\"7\">No cycle dimensions available.</td></tr>'}</tbody></table></div>"
    )

    transition_block = _render_cycle_evidence_list("Transition Or Exit Evidence", transitions, "No transition evidence currently dominates the synthesis.")
    continuation_block = _render_cycle_evidence_list("Continuation Or Recovery Evidence", continuation, "No continuation evidence currently dominates the synthesis.")
    contradiction_block = _render_cycle_evidence_list("Cycle Contradictions", contradictions, "No material cycle-level contradictions were detected.")

    oslo_rows = []
    for item in oslo_groups:
        top = ", ".join(str(sub.get("name", "")) for sub in list(item.get("top_subsectors", []))[:3])
        oslo_rows.append(
            "<tr>"
            f"<td><strong>{escape(str(item.get('group_name', '')))}</strong><span>{escape(top or 'No top subsectors listed.')}</span></td>"
            f"<td>{escape(str(item.get('phase', '')).replace('_', ' '))}</td>"
            f"<td>{_fmt(item.get('average_score'), 1)}</td>"
            f"<td>{_signed(item.get('recovery_potential'))}</td>"
            f"<td>{_signed(item.get('momentum'))}</td>"
            f"<td>{escape(str(item.get('confidence', '')))}</td>"
            f"<td>{escape(str(item.get('read_through', '')))}</td>"
            "</tr>"
        )
    oslo_table = (
        "<h3>Oslo-Linked Sector Read-Through</h3>"
        '<div class="table-wrap"><table class="cycle-table">'
        "<thead><tr><th>Group</th><th>Phase</th><th>Avg score</th><th>Recovery</th><th>Momentum</th><th>Confidence</th><th>Read-through</th></tr></thead>"
        f"<tbody>{''.join(oslo_rows) or '<tr><td colspan=\"7\">No Oslo-linked sector read-through available.</td></tr>'}</tbody></table></div>"
    )

    caveat_items = "".join(
        "<li>"
        f"<strong>{escape(str(item.get('dimension', '')))}:</strong> "
        f"{escape(str(item.get('status', '')).replace('_', ' '))}. "
        f"{escape(str(item.get('caveat', '')))}"
        "</li>"
        for item in caveats
    )
    caveat_block = (
        "<h3>Model Support And Missing-Data Caveats</h3>"
        '<div class="warning">'
        f"<p><strong>{escape(str(confidence.get('label', 'unknown')).title())} model support.</strong> {escape(str(confidence.get('summary', '')))}</p>"
        f"<ul>{caveat_items or '<li>No caveats listed.</li>'}</ul>"
        "</div>"
    )

    return (
        header
        + dimension_table
        + '<div class="cycle-evidence-grid">'
        + transition_block
        + continuation_block
        + contradiction_block
        + "</div>"
        + oslo_table
        + caveat_block
        + f"<p class=\"muted\">{escape(str(cycle_state.get('methodology_note', '')))}</p>"
    )


def _render_cycle_evidence_list(title: str, items: list[dict[str, Any]], empty: str) -> str:
    rows = []
    for item in items[:6]:
        rows.append(
            "<li>"
            f"<strong>{escape(str(item.get('title', '')))}</strong>"
            f"<span>{escape(str(item.get('summary', '')))}</span>"
            "</li>"
        )
    if not rows:
        rows.append(f"<li><span>{escape(empty)}</span></li>")
    return (
        '<article class="cycle-evidence-card">'
        f"<h3>{escape(title)}</h3>"
        f"<ul>{''.join(rows)}</ul>"
        "</article>"
    )


def _render_signal_groups(report_state: dict[str, Any]) -> str:
    groups = list(report_state.get("signal_groups", []))
    if not groups:
        return '<p class="empty-state">No signal-group metadata is available in this report snapshot.</p>'

    cards = []
    for group in groups:
        indicators = list(group.get("indicators", []))
        rows = []
        for item in indicators:
            rows.append(
                "<tr>"
                f"<td><strong>{escape(str(item.get('indicator_name', item.get('indicator_slug', ''))))}</strong><span>{escape(str(item.get('display_slug', '')))}</span></td>"
                f"<td>{escape(str(item.get('latest_observed_at', '')))}</td>"
                f"<td>{_fmt(item.get('latest_value'), 3)}</td>"
                f"<td>{_signed(item.get('tailwind_score'))}</td>"
                f"<td>{escape(str(item.get('momentum_horizon', 'unknown')))}</td>"
                f"<td>{escape(str(item.get('source_category', '')).replace('_', ' '))}</td>"
                f"<td>{escape(str(item.get('freshness_status', '')).replace('_', ' '))}</td>"
                "</tr>"
            )
        table = (
            '<div class="table-wrap"><table class="freshness-table">'
            "<thead><tr><th>Indicator</th><th>Latest observation</th><th>Latest value</th><th>Tailwind</th><th>Signal horizon</th><th>Data class</th><th>Freshness</th></tr></thead>"
            f"<tbody>{''.join(rows) or '<tr><td colspan=\"7\">No liquidity or credit indicators available.</td></tr>'}</tbody></table></div>"
        )
        cards.append(
            '<article class="lead-item lead-item--wide">'
            f"<h4>{escape(str(group.get('title', 'Signal group')))}</h4>"
            '<dl class="mini-stats mini-stats--wide">'
            f"<div><dt>Status</dt><dd>{escape(str(group.get('status', 'unknown')).replace('_', ' '))}</dd></div>"
            f"<div><dt>Condition</dt><dd>{escape(str(group.get('summary_label', 'unknown')))}</dd></div>"
            f"<div><dt>Tailwind</dt><dd>{_signed(group.get('tailwind_score'))}</dd></div>"
            f"<div><dt>Macro read</dt><dd>{escape(str(group.get('macro_confirmation', 'unknown')))}</dd></div>"
            "</dl>"
            f"<p class=\"muted\">{escape(str(group.get('methodology_note', '')))}</p>"
            f"{table}"
            "</article>"
        )
    return f'<div class="lead-grid lead-grid--single">{"".join(cards)}</div>'


def _render_contradicting_evidence(report_state: dict[str, Any]) -> str:
    records = list(report_state.get("contradicting_evidence", []))
    if not records:
        return '<p class="empty-state">No material contradictions were detected among the current score components.</p>'

    items = []
    for item in records:
        components = _component_list(dict(item.get("components", {})))
        items.append(
            '<article class="evidence-item">'
            f"<h4>{escape(str(item.get('subsector_name', '')))}</h4>"
            f"<p><strong>{escape(str(item.get('title', '')))}</strong></p>"
            f"<p>{escape(str(item.get('summary', '')))}</p>"
            f"<p class=\"muted\">Components: {components}</p>"
            "</article>"
        )
    return f'<div class="evidence-grid">{"".join(items)}</div>'


def _render_changes(changes: dict[str, Any] | None) -> str:
    if not changes:
        return '<p class="empty-state">No previous report snapshot was supplied, so this build shows the current radar without weekly deltas.</p>'

    summary = changes.get("summary", {})
    change_rows = []
    for item in changes.get("subsector_changes", [])[:12]:
        if item.get("change_type") != "changed":
            label = item.get("change_type", "changed").replace("_", " ")
            change_rows.append(
                f"<tr><td>{escape(str(item.get('slug', '')))}</td><td>{escape(label)}</td><td colspan=\"4\">Rank {_fmt(item.get('current_rank') or item.get('previous_rank'), 0)}</td></tr>"
            )
            continue
        change_rows.append(
            "<tr>"
            f"<td><strong>{escape(str(item.get('name', item.get('slug', ''))))}</strong></td>"
            f"<td>{_rank_delta(item.get('rank_delta'))}</td>"
            f"<td>{_signed(item.get('score_delta'))}</td>"
            f"<td>{escape(str(item.get('score_move', '')))}</td>"
            f"<td>{_delta_list(item.get('signal_delta', {}))}</td>"
            f"<td>{_delta_list(item.get('market_cycle_delta', {}))}</td>"
            "</tr>"
        )

    source_rows = "".join(
        f"<li><strong>{escape(str(item.get('source_slug', '')))}</strong>: {escape(str(item.get('status_delta', item.get('change_type', 'changed'))))}</li>"
        for item in changes.get("source_status_changes", [])[:8]
    )
    source_block = f"<ul>{source_rows}</ul>" if source_rows else '<p class="muted">No source status changes.</p>'
    cycle_rows = "".join(
        "<li>"
        f"<strong>{escape(str(item.get('title') or item.get('scope') or item.get('dimension_id', 'cycle')))}</strong>: "
        f"{escape(str(item.get('previous_phase', '')))} -> {escape(str(item.get('current_phase', item.get('change_type', 'changed'))))}"
        "</li>"
        for item in changes.get("cycle_state_changes", [])[:8]
    )
    cycle_block = f"<ul>{cycle_rows}</ul>" if cycle_rows else '<p class="muted">No cycle-state changes.</p>'
    research = changes.get("research_fact_changes", {})
    research_block = (
        f"<p>{len(research.get('new', []))} new, {len(research.get('changed', []))} changed, "
        f"{len(research.get('removed', []))} removed reviewed public research facts.</p>"
    )

    return (
        '<div class="summary-grid summary-grid--compact">'
        f"{_metric('Subsector changes', str(summary.get('subsector_changes', 0)), 'Rank, score, signal, or cycle')}"
        f"{_metric('Cycle changes', str(summary.get('cycle_state_changes', 0)), 'Phase, direction, confidence, or contradiction')}"
        f"{_metric('Major priority moves', str(summary.get('major_score_moves', 0)), 'Research-priority index move >= 5')}"
        f"{_metric('Source changes', str(summary.get('source_status_changes', 0)), 'Latest source status')}"
        f"{_metric('New facts', str(summary.get('new_research_facts', 0)), 'Reviewed public facts')}"
        "</div>"
        '<div class="table-wrap"><table><thead><tr><th>Subsector</th><th>Research rank</th><th>Priority change</th><th>Move</th><th>Signal deltas</th><th>Market deltas</th></tr></thead>'
        f"<tbody>{''.join(change_rows) or '<tr><td colspan=\"6\">No material subsector changes.</td></tr>'}</tbody></table></div>"
        "<h3>Cycle State</h3>"
        f"{cycle_block}"
        "<h3>Source Status</h3>"
        f"{source_block}"
        "<h3>Research Fact Changes</h3>"
        f"{research_block}"
    )


def _render_history_validation(report_state: dict[str, Any]) -> str:
    validation = dict(report_state.get("report_history_validation", {}))
    if not validation:
        return '<p class="empty-state">No report-history validation is available in this snapshot.</p>'

    phase = dict(validation.get("phase_stability", {}))
    replay = dict(validation.get("rule_replay", {}))
    confidence = dict(validation.get("confidence_calibration", {}))
    transition = dict(validation.get("transition_continuity", {}))
    contradiction = dict(validation.get("contradiction_continuity", {}))
    flags = list(validation.get("review_flags", []))
    snapshots = list(validation.get("snapshots", []))
    calibration_detail = f"History depth {str(validation.get('history_depth', 'unknown')).replace('_', ' ')}"
    snapshot_detail = f"{validation.get('full_state_snapshot_count', 0)} full report states"
    phase_detail = f"{phase.get('phase_change_count', 0)} changes; streak {phase.get('current_phase_streak', 0)}"
    replay_detail = f"{replay.get('checked_snapshot_count', 0)} full snapshots checked"

    cards = (
        '<div class="summary-grid summary-grid--compact">'
        f"{_metric('Consistency status', str(validation.get('calibration_status', 'unknown')).replace('_', ' '), calibration_detail)}"
        f"{_metric('Public snapshots', str(validation.get('snapshot_count', 0)), snapshot_detail)}"
        f"{_metric('Phase stability', str(phase.get('status', 'unknown')).replace('_', ' '), phase_detail)}"
        f"{_metric('Implementation replay', str(replay.get('status', 'unknown')).replace('_', ' '), replay_detail)}"
        "</div>"
    )

    if flags:
        flag_block = '<div class="warning"><h3>Consistency Review Flags</h3><ul>' + "".join(
            f"<li>{escape(str(item))}</li>" for item in flags
        ) + "</ul></div>"
    else:
        flag_block = (
            '<div class="callout"><strong>Implementation replay passed.</strong> '
            f"Stored phase and confidence labels reproduce under the published rules. Empirical validation is "
            f"{escape(str(validation.get('empirical_validation_status', 'insufficient_history')).replace('_', ' '))}; "
            "this does not establish predictive accuracy.</div>"
        )

    continuity_rows = []
    for label, audit in (("Transition evidence", transition), ("Contradiction evidence", contradiction)):
        added = ", ".join(str(item) for item in audit.get("added", [])) or "none"
        removed = ", ".join(str(item) for item in audit.get("removed", [])) or "none"
        similarity = audit.get("jaccard_similarity")
        continuity_rows.append(
            "<tr>"
            f"<td><strong>{escape(label)}</strong></td>"
            f"<td>{escape(str(audit.get('status', 'unknown')).replace('_', ' '))}</td>"
            f"<td>{_fmt(similarity, 3) if similarity is not None else 'n/a'}</td>"
            f"<td>{escape(added)}</td>"
            f"<td>{escape(removed)}</td>"
            "</tr>"
        )
    continuity_table = (
        "<h3>Evidence Continuity</h3>"
        '<div class="table-wrap"><table>'
        "<thead><tr><th>Validation surface</th><th>Status</th><th>Title overlap</th><th>Added</th><th>Removed</th></tr></thead>"
        f"<tbody>{''.join(continuity_rows)}</tbody></table></div>"
    )

    snapshot_rows = []
    for item in reversed(snapshots[-12:]):
        snapshot_rows.append(
            "<tr>"
            f"<td>{escape(str(item.get('generated_at') or item.get('data_as_of') or '')[:10])}</td>"
            f"<td>{escape(str(item.get('cycle_phase', 'unknown')).replace('_', ' '))}</td>"
            f"<td>{escape(str(item.get('cycle_direction', '')) or 'compact archive')}</td>"
            f"<td>{_fmt(item.get('cycle_score'), 3) if item.get('cycle_score') is not None else 'n/a'}</td>"
            f"<td>{escape(str(item.get('cycle_confidence', 'unknown')))}</td>"
            f"<td>{escape('full state' if item.get('full_state') else 'compact archive')}</td>"
            f"<td>{escape(str(item.get('numeric_mode', 'unknown')).replace('_', ' '))}"
            f"<span>{int(_num(item.get('numeric_sample_fallback_count')))} numeric fallback</span></td>"
            "</tr>"
        )
    snapshots_table = (
        "<h3>Accumulated Public Snapshots</h3>"
        '<div class="table-wrap"><table class="cycle-table">'
        "<thead><tr><th>Report</th><th>Phase</th><th>Direction</th><th>Score</th><th>Confidence</th><th>Validation depth</th><th>Numeric mode</th></tr></thead>"
        f"<tbody>{''.join(snapshot_rows) or '<tr><td colspan=\"7\">No snapshots available.</td></tr>'}</tbody></table></div>"
    )

    confidence_note = (
        f"Confidence-label threshold replay is {str(confidence.get('status', 'unknown')).replace('_', ' ')} "
        f"across {confidence.get('checked_snapshot_count', 0)} full snapshots, with "
        f"{confidence.get('mismatch_count', 0)} threshold mismatches."
    )
    return (
        cards
        + f"<p>{escape(str(validation.get('summary', '')))}</p>"
        + flag_block
        + continuity_table
        + snapshots_table
        + f'<p class="muted">{escape(confidence_note)} {escape(str(validation.get("methodology_note", "")))}</p>'
    )


def _render_archive(entries: list[dict[str, str]], report_prefix: str) -> str:
    if not entries:
        return '<p class="empty-state">No archived report pages have been generated yet.</p>'
    rows = "".join(
        "<tr>"
        f"<td><a href=\"{escape(report_prefix)}/{escape(str(entry.get('file', '')))}\">{escape(str(entry.get('date', '')))}</a><span>{escape(str(entry.get('label', '')))}</span></td>"
        f"<td>{escape(str(entry.get('cycle_phase', 'unknown')).replace('_', ' '))}<span>{escape(str(entry.get('cycle_confidence', '')))}</span></td>"
        f"<td>{escape(str(entry.get('numeric_mode', 'unknown')).replace('_', ' '))}<span>{int(_num(entry.get('live_indicator_count')))} live, {int(_num(entry.get('numeric_sample_fallback_count')))} fallback</span></td>"
        f"<td>{escape(str(entry.get('data_as_of', 'unknown')))}</td>"
        f"<td>{escape(str(entry.get('commit_sha', ''))[:7] or 'n/a')}</td>"
        "</tr>"
        for entry in entries
    )
    return (
        '<div class="table-wrap"><table class="archive-table">'
        "<thead><tr><th>Report</th><th>Cycle phase</th><th>Numeric data</th><th>Data vintage</th><th>Commit</th></tr></thead>"
        f"<tbody>{rows}</tbody></table></div>"
    )


def _render_institutional_outlooks(report_state: dict[str, Any]) -> str:
    outlooks = dict(report_state.get("institutional_outlooks", {}))
    timeline = list(outlooks.get("timeline", []))
    if not timeline:
        return '<p class="empty-state">No reviewed institutional outlook records are available.</p>'

    consensus = dict(outlooks.get("consensus", {}))
    consensus_cards = "".join(
        _metric(label, str(consensus.get(key, "not stated")).replace("_", " "), "Mode across each institution's latest reviewed publication.")
        for key, label in (
            ("growth_bias", "Growth view"),
            ("inflation_bias", "Inflation implication"),
            ("policy_bias", "Policy/rates implication"),
            ("market_bias", "Market view"),
        )
    )
    rows = []
    for item in timeline:
        url = str(item.get("source_url", ""))
        title = escape(str(item.get("title", "")))
        source = f'<a href="{escape(url)}">{title}</a>' if url.startswith("https://") else title
        rows.append(
            "<tr>"
            f"<td><strong>{escape(str(item.get('institution', '')))}</strong><span>{escape(str(item.get('institution_type', '')).replace('_', ' '))}</span></td>"
            f"<td>{escape(str(item.get('published_at', '')))}<span>{escape(str(item.get('horizon', '')).replace('_', ' '))}</span></td>"
            f"<td>{source}<span>{escape(str(item.get('source_tier', '')).replace('_', ' '))}</span></td>"
            f"<td>{escape(str(item.get('summary', '')))}</td>"
            f"<td>{escape(str(item.get('risks', '')))}</td>"
            "</tr>"
        )
    return (
        f'<div class="metric-grid">{consensus_cards}</div>'
        f'<p class="trust-boundary"><strong>Reliability boundary:</strong> {escape(str(outlooks.get("reliability_note", "")))}</p>'
        '<div class="table-wrap"><table class="coverage-table">'
        "<thead><tr><th>Institution</th><th>Published / horizon</th><th>Primary source</th><th>Reviewed read</th><th>Risks</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div>"
    )


def _render_methodology(report_state: dict[str, Any], data_prefix: str) -> str:
    methodology = report_state.get("methodology", {})
    signal_items = "".join(f"<li><strong>{escape(label)}:</strong> {escape(_signal_description(signal))}</li>" for signal, label in SIGNAL_LABELS.items())
    coverage_rows = "".join(
        "<tr>"
        f"<td><strong>{escape(str(item.get('dimension', '')))}</strong></td>"
        f"<td>{escape(str(item.get('status', '')).replace('_', ' '))}</td>"
        f"<td>{escape(str(item.get('current_coverage', '')))}</td>"
        f"<td>{escape(str(item.get('main_gap', '')))}</td>"
        "</tr>"
        for item in report_state.get("framework_coverage", [])
    )
    coverage_table = (
        "<h3>Framework Coverage</h3>"
        '<div class="table-wrap"><table class="coverage-table">'
        "<thead><tr><th>Dimension</th><th>Status</th><th>Current coverage</th><th>Main gap</th></tr></thead>"
        f"<tbody>{coverage_rows or '<tr><td colspan=\"4\">No framework coverage metadata available.</td></tr>'}</tbody>"
        "</table></div>"
    )
    return (
        '<div class="methodology-grid">'
        "<div>"
        f"<p><strong>Scoring version:</strong> {escape(str(methodology.get('scoring_version', 'unknown')))}<br>"
        f"<strong>Report schema:</strong> {escape(str(methodology.get('report_state_version', report_state.get('schema_version', 'unknown'))))}<br>"
        f"<strong>Framework reference:</strong> {escape(str(methodology.get('framework_reference', 'not set')))}</p>"
        f"<p>{escape(str(methodology.get('scoring', 'Transparent subsector scoring from public/free indicators and sample fallbacks.')))}</p>"
        f"<p><strong>Framework coverage:</strong> {escape(str(methodology.get('framework_coverage', 'Partial macro-cycle implementation.')))}</p>"
        "<ul>"
        f"{signal_items}"
        "</ul>"
        "</div>"
        "<div>"
        f"<p>{escape(str(methodology.get('implementation_boundary', 'Scores are research triage signals, not forecasts or advice.')))}</p>"
        f"<p>{escape(str(methodology.get('research_policy', 'Only reviewed public research facts are included in public report state.')))}</p>"
        "<p>Unreviewed claims, manual reports, credentials, private notes, raw licensed data, and unpublished research are excluded from this static site.</p>"
        f"<p>Public assets: <a href=\"{escape(data_prefix)}/latest.json\">latest JSON</a>, <a href=\"{escape(data_prefix)}/report_state.json\">report-state JSON</a>, <a href=\"{escape(data_prefix)}/history_validation.json\">history consistency JSON</a>, <a href=\"{escape(data_prefix)}/archive.json\">archive JSON</a>, and the fixed <a href=\"{'weekly' if data_prefix == 'data' else '../weekly'}/weekly-cycle-brief.pdf\">one-page weekly PDF</a>.</p>"
        "</div>"
        "</div>"
        f"{coverage_table}"
    )


def _metric(label: str, value: str, detail: str) -> str:
    return (
        '<article class="metric">'
        f"<span>{escape(label)}</span>"
        f"<strong>{escape(value)}</strong>"
        f"<p>{escape(detail)}</p>"
        "</article>"
    )


def _source_link(fact: dict[str, Any]) -> str:
    source_name = escape(str(fact.get("source_name", "source")))
    source_url = str(fact.get("source_url", ""))
    if source_url.startswith(("https://", "http://")):
        return f'<a href="{escape(source_url)}">{source_name}</a>'
    return f'<span class="source-name">{source_name}</span>'


def _score_bar(value: object) -> str:
    if value is None:
        return '<div class="score-cell">unavailable</div>'
    score = max(0.0, min(100.0, _num(value)))
    return f'<div class="score-cell"><strong>{score:.1f}</strong><span class="bar"><span style="width: {score:.0f}%"></span></span></div>'


def _health_notice(health: dict[str, Any]) -> str:
    payload = _json_script(health)
    status = escape(health["status"])
    return f'''<aside id="source-health-status" role="status" class="section-intro" style="padding:1rem;border:1px solid currentColor">Source health at publication: {status}. Observation dates and usable coverage are separate from report generation. Research validation is not established.</aside>
<script>(() => {{
  const h = {payload};
  const el = document.getElementById('source-health-status');
  const expired = !Number.isFinite(Date.parse(h.expires_at)) || Date.now() > Date.parse(h.expires_at);
  el.dataset.status = expired ? 'blocked' : h.status;
  const c = h.coverage;
  el.textContent = (expired ? 'RETAINED EDITION: its source-health/update deadline has passed. ' : '') + 'Source health at ' + h.generated_at + ': ' + h.status + '. ' + c.usable_indicator_count + '/' + c.configured_indicator_count + ' configured indicators usable. Observation range: ' + (h.source_observation_start || 'unavailable') + ' to ' + (h.source_observation_end || 'unavailable') + '. Source quality and predictive validation are separate.';
}})();</script>'''


def _signal_cell(signal: str, value: object) -> str:
    if value is None:
        return '<td>n/a</td>'
    number = _num(value)
    if signal == "confidence":
        intensity = max(0.08, min(0.45, number * 0.42))
        color = f"rgba(36, 99, 137, {intensity:.2f})"
        label = _pct(number)
    else:
        intensity = max(0.06, min(0.48, abs(number) * 0.95))
        color = f"rgba(32, 120, 87, {intensity:.2f})" if number >= 0 else f"rgba(172, 75, 58, {intensity:.2f})"
        label = _signed(number)
    return f'<td style="background: {color}">{label}</td>'


def _rank_delta(value: object) -> str:
    if value is None:
        return "unavailable"
    number = int(_num(value))
    if number > 0:
        return f"up {number}"
    if number < 0:
        return f"down {abs(number)}"
    return "flat"


def _delta_list(values: dict[str, Any]) -> str:
    if not values:
        return '<span class="muted">none</span>'
    return ", ".join(f"{escape(str(key).replace('_', ' '))} {_signed(value)}" for key, value in values.items())


def _component_list(values: dict[str, Any]) -> str:
    if not values:
        return "none"
    return ", ".join(f"{escape(str(key).replace('_', ' '))} {_signed(value)}" for key, value in values.items())


def _join_or_none(values: list[Any]) -> str:
    cleaned = [str(value) for value in values if str(value)]
    return ", ".join(cleaned) if cleaned else "none"


def _signal_description(signal: str) -> str:
    descriptions = {
        "cycle_pressure": "pressure or stress that can create future recovery setups.",
        "recovery_potential": "evidence that a depressed subsector may be turning.",
        "valuation_proxy": "cycle-position discount or mean-reversion context derived from proxy percentiles; it is not valuation.",
        "momentum": "recent trend strength in the subsector signal set.",
        "macro_tailwind": "macro or geopolitical backdrop that may support the subsector.",
        "narrative_divergence": "gap between current evidence and prevailing sentiment.",
        "data_support": "availability, freshness and source coverage, not model accuracy or a return forecast.",
    }
    return descriptions[signal]


def _archive_entries(
    reports_dir: Path,
    current_file: str,
    report_state: dict[str, Any],
    previous_entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    files = {path.name for path in reports_dir.glob("*.html")}
    files.add(current_file)
    entries_by_file = {
        str(entry.get("file", "")): dict(entry)
        for entry in previous_entries
        if str(entry.get("file", "")).endswith(".html")
    }
    for filename in files:
        date_label = filename.removesuffix(".html")
        entries_by_file.setdefault(filename, {"date": date_label, "file": filename, "label": "Archived report"})
    entries_by_file[current_file] = _archive_entry_for_current_report(report_state, current_file)
    return sorted(entries_by_file.values(), key=lambda item: str(item.get("date", "")), reverse=True)


def _archive_entry_for_current_report(report_state: dict[str, Any], current_file: str) -> dict[str, Any]:
    numeric = dict(report_state.get("source_health", {}).get("numeric", {}))
    global_cycle = dict(report_state.get("cycle_state", {}).get("global_equity_cycle", {}))
    publication = dict(report_state.get("publication_status", {}))
    validation = dict(report_state.get("report_history_validation", {}))
    run = dict(publication.get("run", {}))
    return {
        "date": current_file.removesuffix(".html"),
        "file": current_file,
        "label": "Current report",
        "generated_at": str(report_state.get("generated_at", "")),
        "data_as_of": str(report_state.get("data_as_of", "")),
        "schema_version": str(report_state.get("schema_version", "")),
        "numeric_mode": str(numeric.get("mode", "")),
        "live_indicator_count": int(_num(numeric.get("live_indicator_count"))),
        "numeric_sample_fallback_count": int(_num(numeric.get("sample_fallback_indicator_count"))),
        "cycle_phase": str(global_cycle.get("phase", "")),
        "cycle_confidence": str(global_cycle.get("confidence", "")),
        "overall_confidence": str(report_state.get("cycle_state", {}).get("confidence", {}).get("label", "")),
        "contradiction_count": len(report_state.get("cycle_state", {}).get("contradictions", [])),
        "calibration_status": str(validation.get("calibration_status", "")),
        "history_snapshot_count": int(_num(validation.get("snapshot_count"))),
        "research_fact_count": len(report_state.get("research_facts", [])),
        "run_url": str(run.get("run_url", "")),
        "commit_sha": str(run.get("commit_sha", "")),
    }


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _ensure_public_output(path: Path) -> None:
    root = EXPORT_DIR.parents[0].resolve()
    try:
        root_relative = path.resolve().relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Output directory is outside the project root: {path}") from exc
    if not is_public_export_path(root_relative):
        raise ValueError(f"Output directory is not public-allowlisted: {path}")


def _report_date(report_state: dict[str, Any]) -> str:
    generated_at = str(report_state.get("generated_at", ""))
    try:
        return datetime.fromisoformat(generated_at).date().isoformat()
    except ValueError:
        return str(report_state.get("data_as_of", "report"))


def _display_datetime(value: object) -> str:
    raw = str(value or "")
    try:
        return datetime.fromisoformat(raw).strftime("%Y-%m-%d %H:%M UTC")
    except ValueError:
        return escape(raw or "unknown")


def _json_script(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, allow_nan=False).replace("</", "<\\/")


def _fmt(value: object, digits: int) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "n/a"


def _signed(value: object) -> str:
    try:
        return f"{float(value):+.2f}"
    except (TypeError, ValueError):
        return "n/a"


def _pct(value: object) -> str:
    try:
        return f"{float(value):.0%}"
    except (TypeError, ValueError):
        return "n/a"


def _num(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _parse_date(value: object) -> datetime | None:
    raw = str(value or "")
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def _stylesheet() -> str:
    return """
:root {
  color-scheme: light;
  --ink: #17201c;
  --muted: #5a665f;
  --paper: #f6f7f2;
  --panel: #ffffff;
  --line: #d9ded6;
  --forest: #12342d;
  --green: #207857;
  --red: #ac4b3a;
  --blue: #246389;
  --amber: #b2822b;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: var(--paper);
  color: var(--ink);
}
a { color: var(--blue); text-decoration-thickness: 1px; text-underline-offset: 3px; }
.masthead { background: var(--forest); color: #fff; }
.masthead__inner { max-width: 1240px; margin: 0 auto; padding: 34px 28px 26px; }
.eyebrow { margin: 0 0 8px; color: #9fb7ad; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; }
h1, h2, h3, h4, p { letter-spacing: 0; }
h1 { margin: 0; max-width: 980px; font-size: clamp(30px, 4vw, 52px); line-height: 1.02; }
h2 { margin: 0; font-size: 28px; }
h3 { margin: 28px 0 12px; font-size: 18px; }
h4 { margin: 0 0 8px; font-size: 17px; }
.lede { max-width: 860px; margin: 14px 0 0; color: #dbe7e1; font-size: 17px; line-height: 1.55; }
.meta-row { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 20px; }
.meta-row span, .meta-link { border: 1px solid rgba(255,255,255,.24); padding: 7px 10px; border-radius: 6px; color: #eef5f0; font-size: 13px; }
.meta-link { text-decoration: none; font-weight: 800; }
.site-nav { position: sticky; top: 0; z-index: 5; display: flex; flex-wrap: nowrap; gap: 4px; padding: 8px max(18px, calc((100vw - 1240px) / 2 + 28px)); overflow-x: auto; background: rgba(246,247,242,.97); border-bottom: 1px solid var(--line); backdrop-filter: blur(10px); scrollbar-width: thin; }
.site-nav a { color: var(--ink); padding: 8px 10px; border-radius: 6px; text-decoration: none; font-size: 14px; }
.site-nav a:hover { background: #e8ece4; }
main { max-width: 1240px; margin: 0 auto; padding: 24px 28px 46px; min-width: 0; overflow: clip; }
.decision-section, .section { scroll-margin-top: 66px; }
.decision-section { padding-top: 4px; }
.decision-hero { display: grid; grid-template-columns: minmax(0, 1.45fr) minmax(280px, .55fr); gap: 16px; align-items: stretch; }
.decision-hero__copy, .decision-use-note { border-radius: 10px; padding: 22px; }
.decision-hero__copy { position: relative; overflow: hidden; background: var(--forest); color: #fff; }
.decision-hero__copy::after { content: ""; position: absolute; width: 260px; height: 260px; right: -90px; bottom: -165px; border: 34px solid rgba(255,255,255,.07); border-radius: 50%; }
.decision-hero__copy .eyebrow { margin-top: 22px; }
.decision-hero__copy h2 { max-width: 720px; font-size: clamp(30px, 4vw, 48px); line-height: 1.05; text-transform: capitalize; }
.decision-summary { max-width: 760px; margin: 14px 0 0; color: #e2ede7; font-size: 16px; line-height: 1.55; }
.status-pill { display: inline-flex; padding: 6px 9px; border: 1px solid rgba(255,255,255,.3); border-radius: 999px; color: #fff; font-size: 12px; font-weight: 800; text-transform: uppercase; }
.decision-use-note { background: #e8f0eb; border: 1px solid #c8d9cf; }
.decision-use-note strong { display: block; color: var(--forest); font-size: 18px; }
.decision-use-note p { margin: 10px 0 0; line-height: 1.6; color: #2d4137; }
.decision-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin-top: 12px; }
.decision-item { min-width: 0; background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 14px; }
.decision-item span { display: block; color: var(--muted); font-size: 11px; font-weight: 800; text-transform: uppercase; }
.decision-item strong { display: block; margin-top: 6px; color: var(--forest); font-size: 17px; line-height: 1.2; }
.decision-item p { margin: 7px 0 0; color: #415047; font-size: 12.5px; line-height: 1.45; overflow-wrap: anywhere; }
.section-intro { margin: 8px 0 0; color: var(--muted); line-height: 1.5; }
.trust-summary { margin-top: 12px; }
.trust-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
.trust-card { background: var(--panel); border: 1px solid var(--line); border-top: 3px solid var(--blue); border-radius: 8px; padding: 14px; }
.trust-card span { display: block; color: var(--muted); font-size: 11px; font-weight: 800; text-transform: uppercase; }
.trust-card strong { display: block; margin-top: 5px; color: var(--forest); font-size: 20px; text-transform: capitalize; }
.trust-card p { margin: 6px 0 0; color: #415047; font-size: 12.5px; line-height: 1.45; }
.trust-impact { display: flex; flex-wrap: wrap; gap: 8px 16px; margin-top: 9px; padding: 11px 13px; background: #eef1eb; border-radius: 7px; color: #36463d; font-size: 12.5px; }
.trust-impact strong { margin-right: auto; }
.trust-impact span { white-space: nowrap; }
.trust-boundary { margin: 8px 0 0; color: var(--muted); font-size: 12.5px; line-height: 1.5; }
.cycle-map-panel { background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 18px; }
.cycle-curve { position: relative; height: 245px; border-radius: 8px; overflow: hidden; background: linear-gradient(180deg, #f7faf7 0%, #edf2ec 100%); border: 1px solid #e0e6dd; }
.cycle-curve::before { content: "Recovery and expansion"; position: absolute; left: 35%; top: 9px; color: #859289; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: .06em; }
.curve-segment { position: absolute; height: 4px; background: linear-gradient(90deg, var(--blue), var(--green)); transform-origin: left center; border-radius: 999px; opacity: .7; }
.curve-segment--1 { left: 7%; top: 76%; width: 18%; transform: rotate(-13deg); }
.curve-segment--2 { left: 24%; top: 55%; width: 19%; transform: rotate(-13deg); }
.curve-segment--3 { left: 42%; top: 30%; width: 19%; transform: rotate(-7deg); }
.curve-segment--4 { left: 60%; top: 18%; width: 19%; transform: rotate(10deg); background: linear-gradient(90deg, var(--green), var(--amber)); }
.curve-segment--5 { left: 78%; top: 35%; width: 17%; transform: rotate(15deg); background: linear-gradient(90deg, var(--amber), var(--red)); }
.curve-node { position: absolute; transform: translate(-50%, -50%); width: 120px; text-align: center; z-index: 1; }
.curve-node__dot { display: block; width: 14px; height: 14px; margin: 0 auto 5px; background: #fff; border: 4px solid var(--blue); border-radius: 50%; box-shadow: 0 0 0 3px rgba(36,99,137,.12); }
.curve-node__label, .curve-node__hint { display: block; background: rgba(255,255,255,.88); border-radius: 4px; padding: 2px 4px; }
.curve-node__label { color: var(--forest); font-size: 11px; font-weight: 800; }
.curve-node__hint { margin-top: 2px; color: var(--muted); font-size: 10px; }
.curve-node--current .curve-node__dot { width: 20px; height: 20px; border-color: var(--red); box-shadow: 0 0 0 5px rgba(172,75,58,.16); }
.curve-node--current .curve-node__label { color: var(--red); }
.curve-boundary { margin: 10px 0 0; color: var(--muted); font-size: 12.5px; line-height: 1.5; }
.phase-lane-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin-top: 14px; }
.phase-lane { min-width: 0; padding: 14px; border: 1px solid var(--line); border-radius: 8px; background: #fbfcfa; }
.phase-lane--current { border-color: #c98b7f; box-shadow: inset 4px 0 0 var(--red); }
.phase-lane__action { color: var(--green); font-size: 11px; font-weight: 800; text-transform: uppercase; }
.phase-lane h3 { margin: 5px 0 7px; font-size: 17px; }
.phase-lane p { margin: 0; color: #415047; font-size: 12.5px; line-height: 1.45; }
.phase-lane__group { margin-top: 10px; }
.phase-lane__group > strong { display: block; margin-bottom: 5px; color: var(--muted); font-size: 10px; text-transform: uppercase; }
.chip-row { display: flex; flex-wrap: wrap; gap: 5px; }
.map-chip { display: inline-flex; padding: 4px 6px; border-radius: 4px; background: #e8eee9; color: #2f4439; font-size: 11px; }
.map-chip--sector { background: #dce8e2; font-weight: 800; }
.subsector-list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.subsector-card { min-width: 0; background: var(--panel); border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }
.subsector-card summary { display: flex; justify-content: space-between; gap: 12px; align-items: center; padding: 14px; cursor: pointer; list-style: none; }
.subsector-card summary::-webkit-details-marker { display: none; }
.subsector-card summary::after { content: "+"; flex: 0 0 auto; color: var(--forest); font-size: 22px; font-weight: 600; }
.subsector-card[open] summary::after { content: "-"; }
.subsector-card[open] summary { border-bottom: 1px solid var(--line); }
.subsector-card__identity { min-width: 0; }
.subsector-card__identity span { display: block; color: var(--muted); font-size: 11px; text-transform: uppercase; }
.subsector-card__identity strong { display: block; margin-top: 3px; font-size: 16px; }
.subsector-card__badges { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 4px; }
.phase-badge, .direction-badge, .priority-badge { padding: 4px 6px; border-radius: 4px; font-size: 10px; font-weight: 800; text-transform: capitalize; }
.phase-badge { background: #e5eee8; color: var(--forest); }
.direction-badge { background: #e7eef3; color: #214f6e; }
.priority-badge { background: #fff2d6; color: #795815; }
.subsector-card__body { padding: 14px; }
.subsector-card__body > p { margin: 0 0 10px; color: #35443c; line-height: 1.5; }
.stance { padding: 9px 10px; border-left: 4px solid var(--green); background: #eef4f0; }
.signal-strip { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 7px; margin: 10px 0; }
.signal-strip div { padding: 8px; border-radius: 6px; background: #f0f3ee; }
.signal-strip dt { color: var(--muted); font-size: 10px; }
.signal-strip dd { margin: 4px 0 0; font-weight: 800; }
.subsector-read-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.subsector-read-grid > div { padding: 10px; border: 1px solid #e2e7df; border-radius: 6px; }
.subsector-read-grid strong { color: var(--forest); font-size: 12px; }
.subsector-read-grid p { margin: 5px 0 0; color: #425148; font-size: 12px; line-height: 1.45; }
.subsector-facts { margin-top: 9px; padding: 10px; background: #f5f7f3; border-radius: 6px; }
.subsector-facts > strong { color: var(--forest); font-size: 12px; }
.subsector-facts ul { margin: 7px 0 0; padding-left: 18px; }
.subsector-facts li { margin-top: 6px; color: #3d4d44; font-size: 12px; line-height: 1.45; }
.subsector-facts small { display: block; margin-top: 3px; color: var(--muted); font-size: 10.5px; }
.evidence-boundary { margin-top: 10px !important; color: var(--muted) !important; font-size: 11.5px; }
.dimension-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 9px; }
.dimension-card { min-width: 0; padding: 13px; background: var(--panel); border: 1px solid var(--line); border-top: 3px solid var(--green); border-radius: 8px; }
.dimension-card__phase { color: var(--muted); font-size: 10px; font-weight: 800; text-transform: uppercase; }
.dimension-card h3 { margin: 6px 0; font-size: 16px; }
.dimension-card > p { margin: 0; color: #415047; font-size: 12px; line-height: 1.4; }
.dimension-card .mini-stats { grid-template-columns: 1fr; gap: 5px; margin-top: 10px; }
.dimension-card .mini-stats div { display: flex; justify-content: space-between; gap: 6px; padding: 6px; }
.dimension-card .mini-stats dd { margin: 0; }
.report-details { margin-top: 10px; border: 1px solid var(--line); border-radius: 8px; background: var(--panel); overflow: hidden; }
.report-details > summary { cursor: pointer; padding: 14px 16px; color: var(--forest); font-weight: 800; list-style: none; }
.report-details > summary::-webkit-details-marker { display: none; }
.report-details > summary::after { content: "+"; float: right; font-size: 19px; }
.report-details[open] > summary::after { content: "-"; }
.report-details[open] > summary { background: #eef2ed; border-bottom: 1px solid var(--line); }
.details-body { min-width: 0; padding: 14px; overflow: hidden; }
.details-body > h3:first-child { margin-top: 0; }
.callout { margin: 10px 0; padding: 13px 15px; background: #edf5f0; border: 1px solid #bcd5c6; border-radius: 8px; color: #244235; line-height: 1.5; }
.summary-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-bottom: 26px; }
.summary-grid--compact { margin: 0 0 18px; }
.metric, .lead-item, .evidence-item, .chart-card, .subsector-chart-card, .cycle-headline, .cycle-evidence-card { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; }
.metric { padding: 16px; }
.metric span { display: block; color: var(--muted); font-size: 12px; text-transform: uppercase; font-weight: 700; }
.metric strong { display: block; margin-top: 7px; font-size: 24px; line-height: 1.15; }
.metric p { margin: 7px 0 0; color: var(--muted); font-size: 13px; line-height: 1.4; }
.section { margin-top: 28px; padding-top: 18px; border-top: 1px solid var(--line); }
.section--final { padding-bottom: 30px; }
.section-heading { margin-bottom: 14px; }
.section-heading .eyebrow { color: var(--green); }
.table-wrap { width: 100%; overflow-x: auto; border: 1px solid var(--line); border-radius: 8px; background: var(--panel); }
table { width: 100%; border-collapse: collapse; min-width: 900px; }
th, td { padding: 11px 12px; border-bottom: 1px solid #e8ebe5; text-align: left; vertical-align: top; }
thead th { color: #46524b; background: #eef1eb; font-size: 12px; text-transform: uppercase; }
tbody tr:last-child td, tbody tr:last-child th { border-bottom: 0; }
.radar-table td span { display: block; color: var(--muted); margin-top: 3px; font-size: 13px; }
.rank { font-weight: 800; color: var(--forest); }
.score-cell { min-width: 110px; }
.score-cell strong { display: block; margin-bottom: 6px; }
.bar { display: block; width: 100%; height: 9px; background: #e3e8df; border-radius: 999px; overflow: hidden; }
.bar span { display: block; height: 100%; background: var(--green); border-radius: 999px; }
.heatmap th:first-child { min-width: 190px; }
.heatmap td { min-width: 110px; font-variant-numeric: tabular-nums; }
.lead-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.lead-grid--single { grid-template-columns: 1fr; }
.lead-item { padding: 16px; }
.lead-item--wide { overflow: hidden; }
.lead-item p, .lead-item li { color: #35423b; line-height: 1.45; }
.lead-item ul { margin: 12px 0 0; padding-left: 18px; }
.evidence-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.evidence-item { padding: 15px; border-left: 4px solid var(--amber); }
.evidence-item p { margin: 8px 0 0; color: #35423b; line-height: 1.45; }
.cycle-headline { padding: 18px; margin-bottom: 14px; border-left: 5px solid var(--green); }
.cycle-headline h3 { margin: 0 0 10px; font-size: 28px; text-transform: capitalize; }
.cycle-headline p { margin: 0; color: #35423b; line-height: 1.55; }
.cycle-table td span { display: block; color: var(--muted); margin-top: 3px; font-size: 13px; line-height: 1.35; }
.cycle-evidence-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin-top: 14px; }
.cycle-evidence-card { padding: 15px; }
.cycle-evidence-card h3 { margin-top: 0; }
.cycle-evidence-card ul { margin: 0; padding-left: 18px; }
.cycle-evidence-card li { margin: 9px 0; line-height: 1.45; }
.cycle-evidence-card span { display: block; margin-top: 3px; color: #35423b; }
.chart-layer-intro { background: #eef1eb; border: 1px solid var(--line); border-radius: 8px; padding: 14px 16px; margin-bottom: 14px; }
.chart-layer-intro p { margin: 0; line-height: 1.5; }
.chart-layer-intro p + p { margin-top: 6px; }
.chart-card { padding: 15px; margin-bottom: 12px; }
.chart-card--featured { border-top: 4px solid var(--green); }
.chart-card--compact { padding: 12px; }
.chart-card__heading h4 { margin: 0 0 5px; }
.chart-card__heading p { margin: 0 0 10px; color: #35423b; line-height: 1.45; }
.chart-window-note { margin: 0 0 10px; color: var(--muted); font-size: 13px; line-height: 1.45; }
.svg-chart-wrap { border: 1px solid #e1e6dd; border-radius: 8px; background: #fbfcfa; padding: 8px; }
.line-chart { display: block; width: 100%; height: auto; min-height: 220px; }
.chart-bg { fill: #fbfcfa; }
.chart-grid-line { stroke: #dfe5dc; stroke-width: 1; }
.chart-axis-line { stroke: #9ca79f; stroke-width: 1.2; }
.chart-axis-label { fill: #5a665f; font-size: 11px; }
.chart-legend { display: flex; flex-wrap: wrap; gap: 8px 14px; margin-top: 9px; color: #33413a; font-size: 12px; }
.chart-legend span { display: inline-flex; align-items: center; gap: 6px; }
.chart-legend i { display: inline-block; width: 18px; height: 3px; border-radius: 999px; }
.chart-meta-wrap { margin-top: 10px; }
.chart-meta-table { min-width: 980px; }
.chart-meta-table td span { display: block; color: var(--muted); margin-top: 3px; font-size: 12px; }
.chart-details { margin: 10px 0; border: 1px solid var(--line); border-radius: 8px; background: #fff; }
.chart-details summary { cursor: pointer; padding: 13px 15px; font-weight: 800; color: var(--forest); }
.chart-details > .chart-card, .chart-details > p, .chart-details > .subsector-chart-grid { margin-left: 12px; margin-right: 12px; }
.subsector-chart-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; padding-bottom: 12px; }
.subsector-chart-card { padding: 13px; }
.subsector-chart-card .chart-card { border-color: #e5e9e1; background: #fcfdfb; }
.chart-notes, .chart-missing { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; margin: 0; padding: 14px 18px 14px 32px; }
.chart-notes li, .chart-missing li { margin: 6px 0; line-height: 1.45; }
.source-name { color: var(--muted); font-weight: 700; }
.mini-stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; margin: 14px 0 0; }
.mini-stats--wide { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.mini-stats div { background: #f1f4ef; border-radius: 6px; padding: 9px; }
.mini-stats dt { color: var(--muted); font-size: 12px; }
.mini-stats dd { margin: 4px 0 0; font-weight: 800; }
.run-status-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-top: 14px; }
.status-panel { padding: 15px; }
.status-panel h3 { margin-top: 0; }
.status-panel li { margin: 7px 0; line-height: 1.45; }
.archive-table td span { display: block; color: var(--muted); margin-top: 3px; font-size: 13px; }
.muted { color: var(--muted); }
.empty-state { margin: 0; padding: 16px; background: var(--panel); border: 1px solid var(--line); border-radius: 8px; color: var(--muted); }
.warning { margin: 10px 0; padding: 13px 15px; background: #fff8e8; border: 1px solid #e2c27b; border-radius: 8px; color: #463615; }
.warning ul { margin: 8px 0 0; padding-left: 18px; }
.freshness-table td span { display: block; color: var(--muted); margin-top: 3px; font-size: 13px; }
.methodology-grid { display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(0, .85fr); gap: 18px; }
.methodology-grid > div { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 18px; }
.methodology-grid p, .methodology-grid li { line-height: 1.55; }
.coverage-table td:nth-child(2) { font-weight: 800; text-transform: capitalize; }
@media (max-width: 900px) {
  .summary-grid, .lead-grid, .evidence-grid, .cycle-evidence-grid, .methodology-grid, .subsector-chart-grid, .run-status-grid, .decision-hero, .trust-grid { grid-template-columns: 1fr; }
  .decision-grid, .phase-lane-grid, .dimension-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .subsector-list { grid-template-columns: 1fr; }
  .masthead__inner, main { padding-left: 18px; padding-right: 18px; }
  .site-nav { padding-left: 12px; padding-right: 12px; }
  .table-wrap { max-width: calc(100vw - 64px); overscroll-behavior-inline: contain; }
  .details-body .table-wrap { max-width: calc(100vw - 94px); }
  .trust-impact strong { width: 100%; }
  h1 { font-size: 34px; }
  .line-chart { min-height: 190px; }
}
@media (max-width: 600px) {
  .masthead__inner { padding-top: 26px; }
  h1 { font-size: 31px; }
  h2 { font-size: 24px; }
  .lede { font-size: 15px; }
  .decision-grid, .phase-lane-grid, .dimension-grid, .signal-strip, .subsector-read-grid { grid-template-columns: 1fr; }
  .cycle-curve { display: none; }
  .cycle-map-panel { padding: 12px; }
  .subsector-card summary { align-items: flex-start; }
  .subsector-card__badges { justify-content: flex-start; }
  .trust-impact { display: grid; gap: 6px; }
  .table-wrap { max-width: calc(100vw - 36px); }
  .details-body { padding: 10px; }
  .details-body .table-wrap { max-width: calc(100vw - 78px); }
}
"""
