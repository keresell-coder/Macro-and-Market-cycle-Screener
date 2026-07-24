from copy import deepcopy

from cycle_screener.history_validation import build_report_history_validation
from cycle_screener.refresh import refresh
from cycle_screener.report_state import build_report_state


def test_history_validation_replays_rules_and_preserves_scoring_state() -> None:
    refresh(sample=True)
    current = build_report_state()
    current["generated_at"] = "2026-07-24T12:00:00+00:00"
    previous = deepcopy(current)
    previous["generated_at"] = "2026-07-17T12:00:00+00:00"
    original = deepcopy(current)
    archive = [
        {
            "generated_at": "2026-07-03T12:00:00+00:00",
            "date": "2026-07-03",
            "data_as_of": "2026-07-03",
            "cycle_phase": current["cycle_state"]["global_equity_cycle"]["phase"],
            "cycle_confidence": current["cycle_state"]["global_equity_cycle"]["confidence"],
            "numeric_mode": "sample_numeric",
            "numeric_sample_fallback_count": 0,
        },
        {
            "generated_at": "2026-07-10T12:00:00+00:00",
            "date": "2026-07-10",
            "data_as_of": "2026-07-10",
            "cycle_phase": current["cycle_state"]["global_equity_cycle"]["phase"],
            "cycle_confidence": current["cycle_state"]["global_equity_cycle"]["confidence"],
            "numeric_mode": "sample_numeric",
            "numeric_sample_fallback_count": 0,
        },
    ]

    validation = build_report_history_validation(current, previous, archive)

    assert current == original
    assert validation["version"] == "report-history-consistency-v2-sprint16"
    assert validation["calibration_status"] == "implementation_replay_passed"
    assert validation["history_depth"] == "preliminary"
    assert validation["empirical_validation_status"] == "insufficient_history"
    assert validation["independent_validation"] is False
    assert validation["snapshot_count"] == 4
    assert validation["full_state_snapshot_count"] == 2
    assert validation["phase_stability"]["status"] == "stable"
    assert validation["rule_replay"]["status"] == "aligned"
    assert validation["rule_replay"]["mismatch_count"] == 0
    assert validation["confidence_calibration"]["status"] == "aligned"
    assert validation["transition_continuity"]["status"] == "stable"
    assert validation["contradiction_continuity"]["status"] == "stable"


def test_history_validation_flags_phase_rule_mismatch() -> None:
    refresh(sample=True)
    current = build_report_state()
    current["generated_at"] = "2026-07-24T12:00:00+00:00"
    current["cycle_state"]["global_equity_cycle"]["phase"] = "recovery confirmation"

    validation = build_report_history_validation(current)

    assert validation["calibration_status"] == "needs_review"
    assert validation["rule_replay"]["status"] == "needs_review"
    assert validation["rule_replay"]["mismatch_count"] == 1
    assert validation["review_flags"]


def test_history_validation_carries_forward_bounded_public_snapshots() -> None:
    refresh(sample=True)
    previous = build_report_state()
    previous["generated_at"] = "2026-07-23T12:00:00+00:00"
    previous["report_history_validation"] = {
        "snapshots": [
            {
                "snapshot_id": "report:2026-07-01T12:00:00+00:00",
                "generated_at": "2026-07-01T12:00:00+00:00",
                "data_as_of": "2026-07-01",
                "cycle_phase": (
                    "late-cycle/crowded risk"
                    if previous["cycle_state"]["global_equity_cycle"]["phase"] != "late-cycle/crowded risk"
                    else "transition watch"
                ),
                "cycle_confidence": "medium",
                "numeric_mode": "live_numeric",
                "numeric_sample_fallback_count": 0,
                "full_state": False,
            }
        ]
    }
    current = deepcopy(previous)
    current.pop("report_history_validation")
    current["generated_at"] = "2026-07-24T12:00:00+00:00"

    validation = build_report_history_validation(current, previous)

    dates = [item["generated_at"][:10] for item in validation["snapshots"]]
    assert dates == ["2026-07-01", "2026-07-23", "2026-07-24"]
    assert validation["phase_stability"]["phase_change_count"] == 1
