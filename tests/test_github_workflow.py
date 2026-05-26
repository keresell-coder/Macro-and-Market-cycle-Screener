from pathlib import Path


WORKFLOW = Path(".github/workflows/weekly-report.yml")


def test_weekly_report_workflow_deploys_only_static_site() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "actions/upload-artifact@v4" in workflow
    assert "actions/deploy-pages@v5" in workflow
    assert "GIT_TERMINAL_PROMPT=0 git fetch --depth=1 origin" in workflow
    assert 'tar --dereference --hard-dereference --directory exports/site -cvf "$RUNNER_TEMP/github-pages.tar" .' in workflow
    assert "name: github-pages" in workflow
    assert "python -m pytest -q" in workflow
    assert "python -m cycle_screener.build_static_site" in workflow


def test_weekly_report_workflow_defaults_to_live_data_with_sample_option() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "default: live" in workflow
    assert "github.event.inputs.data_mode" in workflow
    assert "|| 'live'" in workflow
    assert "- sample" in workflow
    assert "DATA_MODE:" in workflow
    assert "python -m cycle_screener.refresh" in workflow
    assert "--fail-on-numeric-sample-fallback" in workflow
    assert "FRED_API_KEY: ${{ secrets.FRED_API_KEY }}" in workflow
    assert "EIA_API_KEY: ${{ secrets.EIA_API_KEY }}" in workflow
    assert "CYCLE_RADAR_PREVIOUS_STATE_URL" in workflow
    assert "previous_archive.json" in workflow
    assert "--previous-archive" in workflow
