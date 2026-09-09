from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
from typing import Any


LATEST_PDF_NAME = "weekly-cycle-brief.pdf"


def build_weekly_pdf(
    report_state: dict[str, Any],
    site_dir: Path,
    local_dir: Path | None = None,
) -> dict[str, str]:
    """Create a public-safe one-page weekly brief and stable latest copies."""

    report_date = _report_date(report_state)
    public_dir = site_dir / "weekly"
    local_output_dir = local_dir or Path("output/pdf")
    public_dir.mkdir(parents=True, exist_ok=True)
    local_output_dir.mkdir(parents=True, exist_ok=True)

    dated_name = f"{report_date}-cycle-brief.pdf"
    public_dated = public_dir / dated_name
    public_latest = public_dir / LATEST_PDF_NAME
    local_dated = local_output_dir / dated_name
    local_latest = local_output_dir / LATEST_PDF_NAME

    _render_pdf(report_state, public_dated)
    shutil.copyfile(public_dated, public_latest)
    shutil.copyfile(public_dated, local_dated)
    shutil.copyfile(public_dated, local_latest)

    return {
        "weekly_pdf": str(public_dated),
        "weekly_pdf_latest": str(public_latest),
        "weekly_pdf_local": str(local_latest),
    }


def _render_pdf(report_state: dict[str, Any], output: Path) -> None:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        KeepTogether,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    decision = dict(report_state.get("decision_support", {}))
    global_read = dict(decision.get("global", {}))
    trust = dict(decision.get("trust", {}))
    cycle_state = dict(report_state.get("cycle_state", {}))
    dimensions = list(cycle_state.get("dimensions", []))
    contradictions = list(cycle_state.get("contradictions", []))
    subsectors = {str(item.get("slug", "")): item for item in decision.get("subsectors", [])}
    groups = dict(decision.get("research_groups", {}))
    numeric = dict(report_state.get("source_health", {}).get("numeric", {}))

    forest = colors.HexColor("#12342D")
    green = colors.HexColor("#207857")
    red = colors.HexColor("#A54737")
    amber = colors.HexColor("#B2822B")
    blue = colors.HexColor("#246389")
    paper = colors.HexColor("#F6F7F2")
    line = colors.HexColor("#D9DED6")
    muted = colors.HexColor("#526159")

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "BriefTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=17,
        leading=19,
        textColor=forest,
        spaceAfter=3,
        alignment=TA_LEFT,
    )
    kicker_style = ParagraphStyle(
        "Kicker",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9,
        textColor=green,
        uppercase=True,
        spaceAfter=2,
    )
    phase_style = ParagraphStyle(
        "Phase",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12.5,
        leading=15,
        textColor=forest,
        spaceAfter=3,
    )
    body_style = ParagraphStyle(
        "BriefBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=7.7,
        leading=10,
        textColor=colors.HexColor("#26332D"),
        spaceAfter=2,
    )
    small_style = ParagraphStyle(
        "BriefSmall",
        parent=body_style,
        fontSize=6.7,
        leading=8.2,
        textColor=muted,
    )
    cell_style = ParagraphStyle(
        "BriefCell",
        parent=body_style,
        fontSize=7.1,
        leading=8.6,
        spaceAfter=0,
    )
    cell_small = ParagraphStyle(
        "BriefCellSmall",
        parent=small_style,
        fontSize=6.3,
        leading=7.5,
        spaceAfter=0,
    )
    header_cell = ParagraphStyle(
        "BriefHeaderCell",
        parent=cell_style,
        fontName="Helvetica-Bold",
        textColor=colors.white,
    )
    section_style = ParagraphStyle(
        "BriefSection",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=10,
        textColor=forest,
        spaceBefore=4,
        spaceAfter=3,
    )

    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=10 * mm,
        bottomMargin=9 * mm,
        title="Weekly Macro and Market-Cycle Brief",
        author="Global Macro, Market and Sector-Cycle Screener",
        subject="Public-safe weekly cycle-state summary",
    )

    story: list[Any] = [
        Paragraph("WEEKLY MACRO AND MARKET-CYCLE BRIEF", kicker_style),
        Paragraph("Global Macro, Market and Sector-Cycle Screener", title_style),
        Paragraph(
            _clean(
                f"Data as of {report_state.get('data_as_of', 'unknown')} | "
                f"{numeric.get('usable_indicator_count', 0)}/{numeric.get('configured_indicator_count', 0)} usable indicators | "
                f"{numeric.get('sample_fallback_indicator_count', 0)} numeric fallback"
            ),
            small_style,
        ),
        Spacer(1, 3),
        Paragraph(_clean(str(global_read.get("phase", "unknown")).replace("_", " ").title()), phase_style),
        Paragraph(_clean(str(global_read.get("summary", ""))), body_style),
        Paragraph(
            "<b>Investor read:</b> "
            + _clean(
                "Use weak or depressed areas as research candidates only after stabilization and momentum confirmation. "
                "Let supported winners run while monitoring invalidation. Treat late-cycle risk as a do-not-chase and "
                "exposure-review alert, not an automatic sell signal."
            ),
            body_style,
        ),
    ]

    trust_cells = []
    for key, label in (
        ("data_quality", "Usable source coverage"),
        ("model_support", "Model support"),
        ("historical_validation", "Predictive validation"),
    ):
        item = dict(trust.get(key, {}))
        trust_cells.append(
            Paragraph(
                f"<b>{label}: {_clean(str(item.get('label', 'unknown')).title())}</b><br/>"
                f"{_clean(str(item.get('detail', '')))}",
                cell_small,
            )
        )
    trust_table = Table([trust_cells], colWidths=[60 * mm, 60 * mm, 60 * mm])
    trust_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), paper),
                ("BOX", (0, 0), (-1, -1), 0.5, line),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, line),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.extend([Spacer(1, 3), trust_table])

    dimension_rows = [
        [
            Paragraph("Global dimensions", header_cell),
            Paragraph("Phase / direction", header_cell),
            Paragraph("Score", header_cell),
        ]
    ]
    for item in dimensions:
        dimension_rows.append(
            [
                Paragraph(_clean(str(item.get("title", ""))), cell_style),
                Paragraph(
                    _clean(
                        f"{str(item.get('phase', '')).replace('_', ' ')} | "
                        f"{str(item.get('direction', '')).replace('_', ' ')}"
                    ),
                    cell_style,
                ),
                Paragraph("n/a" if item.get("score") is None else f"{float(item['score']):+.2f}", cell_style),
            ]
        )
    dimension_table = Table(dimension_rows, colWidths=[67 * mm, 91 * mm, 22 * mm], repeatRows=1)
    dimension_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), forest),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.35, line),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ]
        )
    )
    story.extend([Paragraph("Cycle dimensions", section_style), dimension_table])

    action_rows = [
        [
            Paragraph("Research lane", header_cell),
            Paragraph("Subsectors", header_cell),
            Paragraph("How to use the signal", header_cell),
        ]
    ]
    lane_specs = (
        ("investigate", "Investigate", "Contrarian/recovery candidates; require fundamental and momentum confirmation.", green),
        ("continuation", "Continuation", "Let supported strength run while monitoring invalidation and crowding.", blue),
        ("risk_alert", "Risk alert", "Do not chase; review exposure, contradictions, and rollover evidence.", red),
        ("transition", "Transition", "Signals conflict; wait for clearer confirmation or deterioration.", amber),
    )
    row_colors = []
    for row_index, (key, label, guidance, color) in enumerate(lane_specs, start=1):
        names = [_clean(str(subsectors.get(slug, {}).get("name", slug))) for slug in groups.get(key, [])]
        action_rows.append(
            [
                Paragraph(f"<b>{label}</b>", cell_style),
                Paragraph(", ".join(names) if names else "None in this snapshot.", cell_small),
                Paragraph(_clean(guidance), cell_small),
            ]
        )
        row_colors.append((row_index, color))
    action_table = Table(action_rows, colWidths=[28 * mm, 85 * mm, 67 * mm], repeatRows=1)
    action_style = [
        ("BACKGROUND", (0, 0), (-1, 0), forest),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, line),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    for row_index, color in row_colors:
        action_style.append(("LINEBEFORE", (0, row_index), (0, row_index), 3, color))
    action_table.setStyle(TableStyle(action_style))
    story.extend([Paragraph("Subsector cycle lanes", section_style), action_table])

    contradiction_items = "; ".join(
        _clean(str(item.get("title", ""))) for item in contradictions[:3]
    ) or "No material cycle-level contradictions listed."
    monitoring = KeepTogether(
        [
            Paragraph("What changed and what could invalidate the read", section_style),
            Paragraph(
                f"<b>Change:</b> {_clean(str(global_read.get('what_changed', '')))}<br/>"
                f"<b>Boundary:</b> {_clean(str(global_read.get('classification_boundary', '')))}<br/>"
                f"<b>Contradictions:</b> {contradiction_items}",
                body_style,
            ),
        ]
    )
    story.append(monitoring)

    story.extend(
        [
            Spacer(1, 2),
            Paragraph(
                _clean(
                    "Scope boundary: subsector states are macro-proxy research classifications. True Oslo subsector "
                    "price, valuation, earnings-revision, positioning, and several primary-driver histories remain "
                    "missing or sample-backed. This brief is not investment advice or a market-timing model."
                ),
                small_style,
            ),
            Paragraph(
                '<link href="https://keresell-coder.github.io/Macro-and-Market-cycle-Screener/">'
                "Open the full dashboard</link>",
                ParagraphStyle(
                    "FooterLink",
                    parent=small_style,
                    alignment=TA_LEFT,
                    textColor=blue,
                    spaceBefore=2,
                ),
            ),
        ]
    )

    def footer(canvas, document) -> None:
        canvas.saveState()
        canvas.setStrokeColor(line)
        canvas.line(12 * mm, 7 * mm, A4[0] - 12 * mm, 7 * mm)
        canvas.setFont("Helvetica", 6.3)
        canvas.setFillColor(muted)
        canvas.drawString(12 * mm, 4.2 * mm, "Public-safe weekly summary | Fixed latest PDF: /weekly/weekly-cycle-brief.pdf")
        canvas.drawRightString(A4[0] - 12 * mm, 4.2 * mm, f"Page {document.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def _report_date(report_state: dict[str, Any]) -> str:
    generated_at = str(report_state.get("generated_at", ""))
    try:
        return datetime.fromisoformat(generated_at).date().isoformat()
    except ValueError:
        return str(report_state.get("data_as_of", "report"))


def _clean(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\u2011", "-")
    )
