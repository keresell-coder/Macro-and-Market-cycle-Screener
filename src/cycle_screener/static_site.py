from __future__ import annotations

from datetime import datetime
from html import escape
import json
from pathlib import Path
from statistics import median
from typing import Any

from .config import EXPORT_DIR
from .publication import is_public_export_path


SIGNAL_LABELS = {
    "cycle_pressure": "Cycle pressure",
    "recovery_potential": "Recovery",
    "valuation_proxy": "Valuation proxy",
    "momentum": "Momentum",
    "macro_tailwind": "Macro",
    "narrative_divergence": "Narrative gap",
    "confidence": "Confidence",
}

SIGNAL_ORDER = tuple(SIGNAL_LABELS)


def build_site_files(
    report_state: dict[str, Any],
    changes: dict[str, Any] | None,
    site_dir: Path | None = None,
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

    _write_json(data_dir / "report_state.json", report_state)
    _write_json(data_dir / "latest.json", report_state)
    changes_path = data_dir / "changes.json"
    if changes is None:
        changes_path.unlink(missing_ok=True)
    else:
        _write_json(changes_path, changes)

    archive_entries = _archive_entries(reports_dir, report_page.name)
    _write_json(data_dir / "archive.json", archive_entries)

    index_path = output_dir / "index.html"
    index_path.write_text(
        _render_page(
            report_state=report_state,
            changes=changes,
            archive_entries=archive_entries,
            title="Oslo Macro and Market-cycle Opportunity Radar",
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
    top = subsectors[0] if subsectors else {}
    source_status = list(report_state.get("source_status", []))
    source_health = dict(report_state.get("source_health", {}))
    research_facts = list(report_state.get("research_facts", []))
    numeric_health = dict(source_health.get("numeric", {}))
    page_health = dict(source_health.get("research_pages", {}))
    evidence_health = dict(source_health.get("research_evidence", {}))
    issue_count = (
        int(_num(numeric_health.get("sample_fallback_indicator_count")))
        + int(_num(numeric_health.get("stale_indicator_count")))
        + int(_num(page_health.get("failed_count")))
        + (1 if evidence_health.get("fallback_used") else 0)
    )
    confidence_values = [_num(item.get("signals", {}).get("confidence")) for item in subsectors if "confidence" in item.get("signals", {})]
    median_confidence = median(confidence_values) if confidence_values else 0
    generated_at = _display_datetime(report_state.get("generated_at"))
    data_as_of = escape(str(report_state.get("data_as_of", "unknown")))
    cycle_state = dict(report_state.get("cycle_state", {}))
    global_cycle = dict(cycle_state.get("global_equity_cycle", {}))

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
      <h1>Oslo Macro and Market-cycle Opportunity Radar</h1>
      <p class="lede">Private-first static research radar for Oslo-linked subsector cycle changes. It surfaces where further analyst work may be timely; it is not stock selection or investment advice.</p>
      <div class="meta-row">
        <span>Generated {generated_at}</span>
        <span>Data as of {data_as_of}</span>
        <span>{len(subsectors)} subsectors</span>
      </div>
    </div>
  </header>
  <nav class="site-nav" aria-label="Static report views">
    <a href="{escape(home_href)}">Top</a>
    <a href="#historical-charts">Historical Charts</a>
    <a href="#liquidity-credit">Liquidity/Credit</a>
    <a href="#cycle-status">Cycle Status</a>
    <a href="#source-health">Source Health</a>
    <a href="#contradicting-evidence">Contradicting Evidence</a>
    <a href="#latest-radar">Latest Radar</a>
    <a href="#changes">Changes Since Last Report</a>
    <a href="#archive">Archive</a>
    <a href="#methodology">Methodology</a>
  </nav>
  <main>
    <section class="summary-grid" aria-label="Report summary">
      {_metric("Global equity cycle", str(global_cycle.get("phase", "n/a")).replace("_", " "), f"Confidence {global_cycle.get('confidence', 'n/a')}")}
      {_metric("Median confidence", _pct(median_confidence), "Reviewed public facts only")}
      {_metric("Source issues", str(issue_count), "Fallbacks, stale series, or source failures")}
      {_metric("Numeric fallback", str(numeric_health.get("sample_fallback_indicator_count", 0)), f"{numeric_health.get('live_indicator_count', 0)} live indicators")}
    </section>

    <section id="historical-charts" class="section section--charts">
      <div class="section-heading">
        <p class="eyebrow">Historical Charts</p>
        <h2>Global View And Drilldown</h2>
      </div>
      {_render_chart_layer(report_state)}
    </section>

    <section id="liquidity-credit" class="section">
      <div class="section-heading">
        <p class="eyebrow">Liquidity And Credit</p>
        <h2>Financial Conditions Signal Group</h2>
      </div>
      {_render_signal_groups(report_state)}
    </section>

    <section id="cycle-status" class="section">
      <div class="section-heading">
        <p class="eyebrow">Cycle Status And Transition Synthesis</p>
        <h2>Current Cycle Read</h2>
      </div>
      {_render_cycle_state(report_state)}
    </section>

    <section id="source-health" class="section">
      <div class="section-heading">
        <p class="eyebrow">Source Health</p>
        <h2>Freshness And Fallbacks</h2>
      </div>
      {_render_source_health(report_state)}
    </section>

    <section id="contradicting-evidence" class="section">
      <div class="section-heading">
        <p class="eyebrow">Contradicting Evidence</p>
        <h2>Signals That Do Not Yet Agree</h2>
      </div>
      {_render_contradicting_evidence(report_state)}
    </section>

    <section id="latest-radar" class="section">
      <div class="section-heading">
        <p class="eyebrow">Latest Radar</p>
        <h2>Ranked Opportunity Signals</h2>
      </div>
      {_render_radar_table(subsectors)}
      <h3>Signal Heatmap</h3>
      {_render_heatmap(subsectors)}
      <h3>Research Leads</h3>
      {_render_research_leads(subsectors, research_facts)}
    </section>

    <section id="changes" class="section">
      <div class="section-heading">
        <p class="eyebrow">Changes Since Last Report</p>
        <h2>What Moved</h2>
      </div>
      {_render_changes(changes)}
    </section>

    <section id="archive" class="section">
      <div class="section-heading">
        <p class="eyebrow">Archive</p>
        <h2>Published Static Reports</h2>
      </div>
      {_render_archive(archive_entries, report_prefix)}
    </section>

    <section id="methodology" class="section section--final">
      <div class="section-heading">
        <p class="eyebrow">Methodology</p>
        <h2>How To Read This Radar</h2>
      </div>
      {_render_methodology(report_state, data_prefix)}
    </section>
  </main>
</body>
</html>
"""


def _render_radar_table(subsectors: list[dict[str, Any]]) -> str:
    rows = []
    for item in subsectors:
        signals = item.get("signals", {})
        rows.append(
            "<tr>"
            f"<td class=\"rank\">{int(_num(item.get('rank')))}</td>"
            f"<td><strong>{escape(str(item.get('name', '')))}</strong><span>{escape(str(item.get('group_name', '')))}</span></td>"
            f"<td>{_score_bar(item.get('opportunity_score'))}</td>"
            f"<td>{_signed(signals.get('recovery_potential'))}</td>"
            f"<td>{_signed(signals.get('valuation_proxy'))}</td>"
            f"<td>{_signed(signals.get('momentum'))}</td>"
            f"<td>{_pct(signals.get('confidence'))}</td>"
            f"<td>{escape(str(item.get('explanation', '')))}</td>"
            "</tr>"
        )
    return (
        '<div class="table-wrap"><table class="radar-table">'
        "<thead><tr><th>Rank</th><th>Subsector</th><th>Score</th><th>Recovery</th><th>Valuation proxy</th><th>Momentum</th><th>Confidence</th><th>Read-through</th></tr></thead>"
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
            f"<div><dt>Valuation proxy</dt><dd>{_fmt(cycle.get('valuation_proxy'), 1)}</dd></div>"
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
    chart_layer = dict(report_state.get("chart_layer", {}))

    fallback_indicators = numeric.get("sample_fallback_indicators", []) or []
    stale_indicators = numeric.get("stale_indicators", []) or []
    failed_sources = pages.get("failed_sources", []) or []
    numeric_mode = str(numeric.get("mode", "unknown")).replace("_", " ")

    status_cards = (
        '<div class="summary-grid summary-grid--compact">'
        f"{_metric('Live numeric data', str(numeric.get('live_indicator_count', 0)), f'Mode: {numeric_mode}')}"
        f"{_metric('Numeric sample fallback', str(numeric.get('sample_fallback_indicator_count', 0)), _join_or_none(fallback_indicators))}"
        f"{_metric('Research page failures', str(pages.get('failed_count', 0)), _join_or_none([item.get('source_slug', '') for item in failed_sources]))}"
        f"{_metric('Research evidence fallback', 'Yes' if evidence.get('fallback_used') else 'No', str(evidence.get('message', '') or evidence.get('mode', 'unknown')))}"
        f"{_metric('Historical chart layer', str(chart_layer.get('series_count', 0)), str(chart_layer.get('version', 'not available')))}"
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
            f"<td>{escape(str(item.get('latest_observed_at', '')))}</td>"
            f"<td>{int(_num(item.get('age_days')))}</td>"
            f"<td>{escape(str(item.get('source_category', '')).replace('_', ' '))}</td>"
            f"<td>{escape(str(item.get('freshness_status', '')).replace('_', ' '))}</td>"
            "</tr>"
        )

    table = (
        '<div class="table-wrap"><table class="freshness-table">'
        "<thead><tr><th>Indicator</th><th>Latest observation</th><th>Age days</th><th>Data class</th><th>Freshness</th></tr></thead>"
        f"<tbody>{''.join(rows) or '<tr><td colspan=\"5\">No numeric freshness metadata available.</td></tr>'}</tbody></table></div>"
    )

    return status_cards + "".join(alerts) + table


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
        f"<div><dt>Confidence</dt><dd>{escape(str(global_cycle.get('confidence', 'unknown')))}</dd></div>"
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
        "<thead><tr><th>Dimension</th><th>Phase</th><th>Status</th><th>Direction</th><th>Score</th><th>Confidence</th><th>Largest evidence points</th></tr></thead>"
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
        "<h3>Confidence And Missing-Data Caveats</h3>"
        '<div class="warning">'
        f"<p><strong>{escape(str(confidence.get('label', 'unknown')).title())} confidence.</strong> {escape(str(confidence.get('summary', '')))}</p>"
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
                f"<td>{escape(str(item.get('source_category', '')).replace('_', ' '))}</td>"
                f"<td>{escape(str(item.get('freshness_status', '')).replace('_', ' '))}</td>"
                "</tr>"
            )
        table = (
            '<div class="table-wrap"><table class="freshness-table">'
            "<thead><tr><th>Indicator</th><th>Latest observation</th><th>Latest value</th><th>Tailwind</th><th>Data class</th><th>Freshness</th></tr></thead>"
            f"<tbody>{''.join(rows) or '<tr><td colspan=\"6\">No liquidity or credit indicators available.</td></tr>'}</tbody></table></div>"
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
        f"{_metric('Major score moves', str(summary.get('major_score_moves', 0)), 'Absolute move >= 5 points')}"
        f"{_metric('Source changes', str(summary.get('source_status_changes', 0)), 'Latest source status')}"
        f"{_metric('New facts', str(summary.get('new_research_facts', 0)), 'Reviewed public facts')}"
        "</div>"
        '<div class="table-wrap"><table><thead><tr><th>Subsector</th><th>Rank</th><th>Score</th><th>Move</th><th>Signal deltas</th><th>Market deltas</th></tr></thead>'
        f"<tbody>{''.join(change_rows) or '<tr><td colspan=\"6\">No material subsector changes.</td></tr>'}</tbody></table></div>"
        "<h3>Cycle State</h3>"
        f"{cycle_block}"
        "<h3>Source Status</h3>"
        f"{source_block}"
        "<h3>Research Fact Changes</h3>"
        f"{research_block}"
    )


def _render_archive(entries: list[dict[str, str]], report_prefix: str) -> str:
    if not entries:
        return '<p class="empty-state">No archived report pages have been generated yet.</p>'
    items = "".join(
        f"<li><a href=\"{escape(report_prefix)}/{escape(entry['file'])}\">{escape(entry['date'])}</a><span>{escape(entry['label'])}</span></li>"
        for entry in entries
    )
    return f'<ul class="archive-list">{items}</ul>'


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
        f"<p>JSON assets: <a href=\"{escape(data_prefix)}/latest.json\">latest</a>, <a href=\"{escape(data_prefix)}/report_state.json\">report state</a>, <a href=\"{escape(data_prefix)}/archive.json\">archive</a>.</p>"
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
    score = max(0.0, min(100.0, _num(value)))
    return f'<div class="score-cell"><strong>{score:.1f}</strong><span class="bar"><span style="width: {score:.0f}%"></span></span></div>'


def _signal_cell(signal: str, value: object) -> str:
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
        "valuation_proxy": "public-data screening context and sample-backed valuation context, not true subsector valuation multiples.",
        "momentum": "recent trend strength in the subsector signal set.",
        "macro_tailwind": "macro or geopolitical backdrop that may support the subsector.",
        "narrative_divergence": "gap between current evidence and prevailing sentiment.",
        "confidence": "data availability and source quality, not a return forecast.",
    }
    return descriptions[signal]


def _archive_entries(reports_dir: Path, current_file: str) -> list[dict[str, str]]:
    files = {path.name for path in reports_dir.glob("*.html")}
    files.add(current_file)
    entries = []
    for filename in sorted(files, reverse=True):
        date_label = filename.removesuffix(".html")
        entries.append({"date": date_label, "file": filename, "label": "Current report" if filename == current_file else "Archived report"})
    return entries


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
    return json.dumps(payload, sort_keys=True).replace("</", "<\\/")


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
.meta-row span { border: 1px solid rgba(255,255,255,.24); padding: 7px 10px; border-radius: 6px; color: #eef5f0; font-size: 13px; }
.site-nav { position: sticky; top: 0; z-index: 2; display: flex; flex-wrap: wrap; gap: 8px; padding: 10px 28px; background: rgba(246,247,242,.96); border-bottom: 1px solid var(--line); backdrop-filter: blur(10px); }
.site-nav a { color: var(--ink); padding: 8px 10px; border-radius: 6px; text-decoration: none; font-size: 14px; }
.site-nav a:hover { background: #e8ece4; }
main { max-width: 1240px; margin: 0 auto; padding: 24px 28px 46px; }
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
.archive-list { margin: 0; padding: 0; list-style: none; border: 1px solid var(--line); border-radius: 8px; background: var(--panel); }
.archive-list li { display: flex; justify-content: space-between; gap: 16px; padding: 13px 15px; border-bottom: 1px solid #e8ebe5; }
.archive-list li:last-child { border-bottom: 0; }
.archive-list span, .muted { color: var(--muted); }
.empty-state { margin: 0; padding: 16px; background: var(--panel); border: 1px solid var(--line); border-radius: 8px; color: var(--muted); }
.warning { margin: 10px 0; padding: 13px 15px; background: #fff8e8; border: 1px solid #e2c27b; border-radius: 8px; color: #463615; }
.warning ul { margin: 8px 0 0; padding-left: 18px; }
.freshness-table td span { display: block; color: var(--muted); margin-top: 3px; font-size: 13px; }
.methodology-grid { display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(0, .85fr); gap: 18px; }
.methodology-grid > div { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 18px; }
.methodology-grid p, .methodology-grid li { line-height: 1.55; }
.coverage-table td:nth-child(2) { font-weight: 800; text-transform: capitalize; }
@media (max-width: 900px) {
  .summary-grid, .lead-grid, .evidence-grid, .cycle-evidence-grid, .methodology-grid, .subsector-chart-grid { grid-template-columns: 1fr; }
  .masthead__inner, main { padding-left: 18px; padding-right: 18px; }
  .site-nav { padding-left: 18px; padding-right: 18px; }
  h1 { font-size: 34px; }
  .line-chart { min-height: 190px; }
}
"""
