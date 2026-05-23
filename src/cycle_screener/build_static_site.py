from __future__ import annotations

import argparse
import json
from pathlib import Path

from .change_tracking import compare_report_states
from .config import EXPORT_DIR
from .publication import is_public_export_path
from .refresh import refresh
from .report_state import build_report_state
from .static_site import build_site_files


def build_static_site(
    sample: bool = False,
    previous: Path | None = None,
    output_dir: Path | None = None,
    site_dir: Path | None = None,
    fail_on_numeric_sample_fallback: bool = False,
) -> dict[str, str | None]:
    if sample:
        refresh(sample=True)

    target_dir = output_dir or EXPORT_DIR / "public" / "data"
    root_relative = target_dir if not target_dir.is_absolute() else target_dir.resolve().relative_to(EXPORT_DIR.parents[0].resolve())
    if not is_public_export_path(root_relative):
        raise ValueError(f"Output directory is not public-allowlisted: {target_dir}")

    target_dir.mkdir(parents=True, exist_ok=True)
    current_state = build_report_state()
    if fail_on_numeric_sample_fallback:
        assert_no_numeric_sample_fallback(current_state)
    previous_state = json.loads(previous.read_text(encoding="utf-8")) if previous and previous.exists() else None

    report_state_path = target_dir / "report_state.json"
    latest_path = target_dir / "latest.json"
    report_state_path.write_text(json.dumps(current_state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    latest_path.write_text(json.dumps(current_state, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    changes_path: Path | None = None
    changes = None
    if previous_state:
        changes = compare_report_states(previous_state, current_state)
        changes_path = target_dir / "changes.json"
        changes_path.write_text(json.dumps(changes, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        (target_dir / "changes.json").unlink(missing_ok=True)

    site_result = build_site_files(current_state, changes, site_dir=site_dir)

    return {
        "report_state": str(report_state_path),
        "latest": str(latest_path),
        "changes": str(changes_path) if changes_path else None,
        **site_result,
    }


def assert_no_numeric_sample_fallback(report_state: dict) -> None:
    numeric_health = report_state.get("source_health", {}).get("numeric", {})
    fallback_count = int(numeric_health.get("sample_fallback_indicator_count") or 0)
    if fallback_count <= 0:
        return
    fallback_indicators = ", ".join(numeric_health.get("sample_fallback_indicators") or [])
    raise RuntimeError(
        "Live numeric build used sample_fallback for "
        f"{fallback_count} indicator(s): {fallback_indicators}. "
        "Review source failures or run an explicit deterministic sample build."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the public-safe static report site and JSON artifacts.")
    parser.add_argument("--sample", action="store_true", help="Refresh deterministic sample data before writing artifacts.")
    parser.add_argument("--previous", type=Path, help="Previous report_state.json to compare against.")
    parser.add_argument("--output-dir", type=Path, default=EXPORT_DIR / "public" / "data", help="Backward-compatible public JSON output directory.")
    parser.add_argument("--site-dir", type=Path, default=EXPORT_DIR / "site", help="Public-safe static HTML site directory.")
    parser.add_argument(
        "--fail-on-numeric-sample-fallback",
        action="store_true",
        help="Fail the build if live numeric data fell back to deterministic sample rows.",
    )
    args = parser.parse_args()

    result = build_static_site(
        sample=args.sample,
        previous=args.previous,
        output_dir=args.output_dir,
        site_dir=args.site_dir,
        fail_on_numeric_sample_fallback=args.fail_on_numeric_sample_fallback,
    )
    print(f"Report state written to {result['report_state']}")
    print(f"Latest state written to {result['latest']}")
    if result["changes"]:
        print(f"Change report written to {result['changes']}")
    else:
        print("No previous report provided; change report not written.")
    print(f"Static site written to {result['site_index']}")
    print(f"Weekly report page written to {result['weekly_report']}")


if __name__ == "__main__":
    main()
