"""Publish source failure status without inventing a new research edition."""
from __future__ import annotations

from html import escape
import json
from pathlib import Path
import re
import shutil
from typing import Any

from .source_health import public_health
from .static_site import _ensure_public_output


def build_blocked_site(current_state: dict[str, Any], previous_state: dict[str, Any] | None,
                       archive_entries: list[dict[str, Any]], site_dir: Path,
                       reason: str) -> dict[str, str | None]:
    _ensure_public_output(site_dir)
    # A test or earlier local build may have left sample/current-edition assets.
    # Only verified previous archive HTML belongs in a blocked publication.
    archive_names = {str(entry.get("file", "")) for entry in archive_entries if re.fullmatch(r"\d{4}-\d{2}-\d{2}\.html", str(entry.get("file", "")))}
    for path in (site_dir / "reports").glob("*.html"):
        if path.name not in archive_names:
            path.unlink()
    for directory in ("weekly", "assets", "charts"):
        shutil.rmtree(site_dir / directory, ignore_errors=True)
    data_dir = site_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (site_dir / ".nojekyll").write_text("", encoding="utf-8")
    attempt_at = current_state["generated_at"]
    health = public_health(current_state)
    health.update({
        "status": "blocked", "publication_mode": "blocked_status_page",
        "generated_at": (previous_state or {}).get("generated_at"),
        "latest_attempt_at": attempt_at, "status_as_of": attempt_at,
        "attempt_status": "failed", "expires_at": attempt_at,
        "observation_context": "latest_failed_attempt",
        "attempt_coverage": health["coverage"], "attempt_sources": health["sources"],
        "retained_edition": {"generated_at": (previous_state or {}).get("generated_at"),
                             "data_as_of": (previous_state or {}).get("data_as_of")},
    })
    health["issues"].insert(0, {"source": "publication", "reason": reason})

    def write_json(path, payload):
        path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")

    write_json(site_dir / "health.json", health)
    for name in ("report_state.json", "latest.json"):
        path = data_dir / name
        if previous_state:
            write_json(path, previous_state)  # preserve the complete original state and dates
        else:
            path.unlink(missing_ok=True)
    (data_dir / "changes.json").unlink(missing_ok=True)
    (data_dir / "history_validation.json").unlink(missing_ok=True)

    available_archives = [entry for entry in archive_entries
                          if re.fullmatch(r"\d{4}-\d{2}-\d{2}\.html", str(entry.get("file", "")))
                          and (site_dir / "reports" / entry["file"]).is_file()]
    write_json(data_dir / "archive.json", available_archives)
    archive_links = "".join(f'<li><a href="reports/{escape(entry["file"])}">Archived edition {escape(entry["file"][:-5])}</a> — original dates and limitations apply</li>' for entry in available_archives)
    if not archive_links:
        archive_links = "<li>No verified archived HTML was available to retain.</li>"
    rows = "".join(f'<tr><td>{escape(r["indicator_name"])}</td><td>{escape(str(r["latest_observed_at"] or "missing"))}</td><td>{escape(r["exclusion_reason"])}</td></tr>' for r in health["sources"] if not r["scoring_eligible"])
    counts = health["coverage"]
    previous_date = escape(str(health["generated_at"] or "No verified prior edition timestamp"))
    html = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Macro screener — current report blocked</title>
<style>body{{font:17px/1.5 system-ui,sans-serif;max-width:960px;padding:24px;margin:auto;color:#172b24;background:#f6f5ef}}aside{{padding:20px;border:2px solid #92472c}}table{{border-collapse:collapse;width:100%;font-size:14px}}td,th{{border-bottom:1px solid #bbb;padding:8px;text-align:left}}a{{color:#205d49}}</style></head>
<body><h1>Current report blocked</h1><aside id="source-health-status" role="status" data-status="blocked"><strong>No new macro or sector verdict was published.</strong><p>The latest attempt at {escape(attempt_at)} failed the source-health gate. The retained research edition was generated at {previous_date}.</p></aside>
<p>{counts['usable_indicator_count']}/{counts['configured_indicator_count']} configured indicators were usable in this attempt; {counts['missing_indicator_count']} missing, {counts['stale_indicator_count']} stale, {counts['future_indicator_count']} future-dated. Successful fetching does not validate freshness or predictive ability.</p>
<p>{escape(reason)}</p><p><a href="health.json">Dated source health and coverage JSON</a></p>
<h2>Preserved archives</h2><ul>{archive_links}</ul><h2>Excluded source evidence in this attempt</h2><table><thead><tr><th>Source series</th><th>Latest native observation</th><th>Exclusion</th></tr></thead><tbody>{rows}</tbody></table>
<p>Observation dates remain provider reference dates. They are not replaced by this attempt's timestamp. Predictive validation is not established.</p></body></html>'''
    index = site_dir / "index.html"
    index.write_text(html, encoding="utf-8")
    return {"publication_status": "blocked", "site_index": str(index),
            "report_state": str(data_dir / "report_state.json") if previous_state else None,
            "latest": str(data_dir / "latest.json") if previous_state else None,
            "changes": None, "weekly_report": None, "weekly_pdf_latest": None,
            "health": str(site_dir / "health.json")}
