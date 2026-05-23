from __future__ import annotations

from html import escape

from .config import EXPORT_DIR, get_settings
from .storage import RadarStore


def export_static() -> str:
    settings = get_settings()
    store = RadarStore(settings.database_path)
    scores = store.table("subsector_scores")
    statuses = store.table("source_status")
    store.close()

    if scores.empty:
        from .refresh import refresh

        refresh(sample=True)
        store = RadarStore(settings.database_path)
        scores = store.table("subsector_scores")
        statuses = store.table("source_status")
        store.close()

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    output = EXPORT_DIR / "opportunity_radar.html"
    rows = "\n".join(_score_row(row) for _, row in scores.iterrows())
    status_rows = "\n".join(
        f"<li><strong>{escape(str(row['source_slug']))}</strong>: {escape(str(row['status']))} - {escape(str(row['message']))}</li>"
        for _, row in statuses.tail(12).iterrows()
    )
    refreshed = escape(str(scores["refreshed_at"].iloc[0])) if not scores.empty and "refreshed_at" in scores else "unknown"
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Oslo Macro and Market-cycle Opportunity Radar</title>
  <style>
    body {{ margin: 0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f6f7f4; color: #18201b; }}
    header {{ padding: 28px 32px 18px; background: #12332d; color: #fff; }}
    main {{ padding: 24px 32px 40px; max-width: 1180px; margin: 0 auto; }}
    h1 {{ margin: 0 0 8px; font-size: 30px; letter-spacing: 0; }}
    p {{ line-height: 1.5; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; border: 1px solid #d9ded7; }}
    th, td {{ padding: 10px 12px; border-bottom: 1px solid #e6e9e3; text-align: left; vertical-align: top; }}
    th {{ font-size: 12px; text-transform: uppercase; color: #4c5a52; background: #eef1ec; }}
    .score {{ font-weight: 700; }}
    .bar {{ height: 9px; background: #e1e6de; border-radius: 999px; min-width: 90px; }}
    .fill {{ height: 9px; background: #16735f; border-radius: 999px; }}
    .muted {{ color: #536058; }}
    section {{ margin-top: 24px; }}
  </style>
</head>
<body>
  <header>
    <h1>Oslo Macro and Market-cycle Opportunity Radar</h1>
    <p>Explainable subsector research leads. Not investment advice. Refreshed: {refreshed}</p>
  </header>
  <main>
    <section>
      <table>
        <thead>
          <tr><th>Rank</th><th>Subsector</th><th>Group</th><th>Score</th><th>Recovery</th><th>Momentum</th><th>Confidence</th><th>Evidence</th></tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </section>
    <section>
      <h2>Recent Source Status</h2>
      <ul>{status_rows}</ul>
      <p class="muted">Public export excludes private notes and manual reports.</p>
    </section>
  </main>
</body>
</html>
"""
    output.write_text(html, encoding="utf-8")
    return str(output)


def _score_row(row) -> str:
    score = float(row["opportunity_score"])
    rank = int(row.name) + 1
    return (
        "<tr>"
        f"<td>{rank}</td>"
        f"<td><strong>{escape(str(row['name']))}</strong></td>"
        f"<td>{escape(str(row['group_name']))}</td>"
        f"<td class='score'>{score:.1f}<div class='bar'><div class='fill' style='width:{score:.0f}%'></div></div></td>"
        f"<td>{float(row['recovery_potential']):+.2f}</td>"
        f"<td>{float(row['momentum']):+.2f}</td>"
        f"<td>{float(row['confidence']):.0%}</td>"
        f"<td>{escape(str(row['explanation']))}</td>"
        "</tr>"
    )


def main() -> None:
    output = export_static()
    print(f"Static export written to {output}")


if __name__ == "__main__":
    main()
