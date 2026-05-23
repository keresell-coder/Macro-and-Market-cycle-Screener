from pathlib import Path


WORKFLOW = Path(".github/workflows/weekly-report.yml")


def test_weekly_report_workflow_deploys_only_static_site() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "actions/configure-pages@v5" in workflow
    assert "actions/upload-pages-artifact@v4" in workflow
    assert "actions/deploy-pages@v4" in workflow
    assert "path: exports/site" in workflow
    assert "python -m pytest -q" in workflow
    assert "python -m cycle_screener.build_static_site" in workflow


def test_weekly_report_workflow_defaults_to_live_data_with_sample_option() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "default: live" in workflow
    assert "|| 'live'" in workflow
    assert "- sample" in workflow
    assert "DATA_MODE:" in workflow
    assert "--fail-on-numeric-sample-fallback" in workflow
    assert "FRED_API_KEY: ${{ secrets.FRED_API_KEY }}" in workflow
    assert "EIA_API_KEY: ${{ secrets.EIA_API_KEY }}" in workflow
    assert "CYCLE_RADAR_PREVIOUS_STATE_URL" in workflow
