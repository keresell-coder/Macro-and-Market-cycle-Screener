from __future__ import annotations

from typing import Any

from .cycle_state import classify_global_phase


HISTORY_VALIDATION_VERSION = "report-history-validation-v1-sprint15"
MAX_HISTORY_SNAPSHOTS = 60
CONFIDENCE_THRESHOLDS = (
    (0.75, "high"),
    (0.55, "medium"),
    (0.3, "low"),
    (0.0, "very low"),
)


def build_report_history_validation(
    current_state: dict[str, Any],
    previous_state: dict[str, Any] | None = None,
    previous_archive_entries: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    snapshots: dict[str, dict[str, Any]] = {}

    if previous_state:
        preserved = previous_state.get("report_history_validation", {}).get("snapshots", [])
        for item in preserved:
            if isinstance(item, dict):
                _store_snapshot(snapshots, dict(item))

    for entry in previous_archive_entries or []:
        if isinstance(entry, dict):
            _store_snapshot(snapshots, _snapshot_from_archive(entry))

    if previous_state:
        _store_snapshot(snapshots, _snapshot_from_state(previous_state))
    _store_snapshot(snapshots, _snapshot_from_state(current_state))

    ordered = sorted(snapshots.values(), key=_snapshot_sort_key)[-MAX_HISTORY_SNAPSHOTS:]
    phase_stability = _phase_stability(ordered)
    transition_continuity = _evidence_continuity(ordered, "transition_titles")
    contradiction_continuity = _evidence_continuity(ordered, "contradiction_titles")
    confidence_calibration = _confidence_calibration(ordered)
    rule_replay = _rule_replay(ordered)

    full_count = sum(bool(item.get("full_state")) for item in ordered)
    if len(ordered) >= 4 and full_count >= 2:
        history_depth = "established"
    elif len(ordered) >= 2:
        history_depth = "developing"
    else:
        history_depth = "insufficient"

    review_flags: list[str] = []
    if phase_stability["status"] == "unstable":
        review_flags.append("Phase labels changed frequently relative to the available report history.")
    if rule_replay["mismatch_count"]:
        review_flags.append("At least one stored full snapshot does not replay to its published phase label.")
    if confidence_calibration["mismatch_count"]:
        review_flags.append("At least one stored confidence label is inconsistent with the published score thresholds.")
    for label, audit in (
        ("Transition evidence", transition_continuity),
        ("Contradiction evidence", contradiction_continuity),
    ):
        if audit.get("review_flag"):
            review_flags.append(f"{label} changed materially while the headline phase remained unchanged.")

    if review_flags:
        calibration_status = "needs_review"
    elif history_depth != "established":
        calibration_status = "limited_history"
    else:
        calibration_status = "coherent"

    return {
        "version": HISTORY_VALIDATION_VERSION,
        "calibration_status": calibration_status,
        "history_depth": history_depth,
        "snapshot_count": len(ordered),
        "full_state_snapshot_count": full_count,
        "compact_snapshot_count": len(ordered) - full_count,
        "coverage_start": _snapshot_date(ordered[0]) if ordered else "",
        "coverage_end": _snapshot_date(ordered[-1]) if ordered else "",
        "phase_stability": phase_stability,
        "transition_continuity": transition_continuity,
        "contradiction_continuity": contradiction_continuity,
        "confidence_calibration": confidence_calibration,
        "rule_replay": rule_replay,
        "review_flags": review_flags,
        "summary": _summary(
            calibration_status,
            history_depth,
            len(ordered),
            full_count,
            phase_stability,
            rule_replay,
            confidence_calibration,
        ),
        "methodology_note": (
            "Validation reuses only accumulated public report snapshots and archive summaries. "
            "It does not add indicators, change numeric scoring, or admit research claims. "
            "Compact archive rows validate headline phase persistence; full report states also validate "
            "transition evidence, contradictions, rule replay, and confidence-label thresholds."
        ),
        "snapshots": ordered,
    }


def _snapshot_from_state(state: dict[str, Any]) -> dict[str, Any]:
    cycle_state = dict(state.get("cycle_state", {}))
    global_cycle = dict(cycle_state.get("global_equity_cycle", {}))
    overall_confidence = dict(cycle_state.get("confidence", {}))
    numeric = dict(state.get("source_health", {}).get("numeric", {}))
    dimensions = {
        str(item.get("dimension_id", "")): item
        for item in cycle_state.get("dimensions", [])
        if isinstance(item, dict) and item.get("dimension_id")
    }
    generated_at = str(state.get("generated_at", ""))
    data_as_of = str(state.get("data_as_of", ""))
    return {
        "snapshot_id": f"report:{generated_at or data_as_of}",
        "generated_at": generated_at,
        "data_as_of": data_as_of,
        "schema_version": str(state.get("schema_version", "")),
        "cycle_phase": str(global_cycle.get("phase", "")),
        "cycle_status": str(global_cycle.get("status", "")),
        "cycle_direction": str(global_cycle.get("direction", "")),
        "cycle_score": _optional_float(global_cycle.get("score")),
        "cycle_confidence": str(global_cycle.get("confidence", "")),
        "cycle_confidence_score": _optional_float(global_cycle.get("confidence_score")),
        "overall_confidence": str(overall_confidence.get("label", "")),
        "overall_confidence_score": _optional_float(overall_confidence.get("score")),
        "dimension_phases": {key: str(value.get("phase", "")) for key, value in dimensions.items()},
        "dimension_scores": {key: _optional_float(value.get("score")) for key, value in dimensions.items()},
        "dimension_direction_scores": {
            key: _optional_float(value.get("direction_score")) for key, value in dimensions.items()
        },
        "transition_titles": _titles(cycle_state.get("transition_evidence", [])),
        "contradiction_titles": _titles(cycle_state.get("contradictions", [])),
        "contradiction_count": len(cycle_state.get("contradictions", [])),
        "numeric_mode": str(numeric.get("mode", "")),
        "numeric_sample_fallback_count": int(numeric.get("sample_fallback_indicator_count") or 0),
        "full_state": True,
    }


def _snapshot_from_archive(entry: dict[str, Any]) -> dict[str, Any]:
    generated_at = str(entry.get("generated_at", ""))
    date_value = str(entry.get("date") or entry.get("data_as_of") or "")
    commit_sha = str(entry.get("commit_sha", ""))
    return {
        "snapshot_id": f"archive:{generated_at or date_value}:{commit_sha}",
        "generated_at": generated_at,
        "data_as_of": str(entry.get("data_as_of", "")),
        "schema_version": str(entry.get("schema_version", "")),
        "cycle_phase": str(entry.get("cycle_phase", "")),
        "cycle_status": "",
        "cycle_direction": "",
        "cycle_score": None,
        "cycle_confidence": str(entry.get("cycle_confidence", "")),
        "cycle_confidence_score": None,
        "overall_confidence": str(entry.get("overall_confidence", "")),
        "overall_confidence_score": None,
        "dimension_phases": {},
        "dimension_scores": {},
        "dimension_direction_scores": {},
        "transition_titles": [],
        "contradiction_titles": [],
        "contradiction_count": entry.get("contradiction_count"),
        "numeric_mode": str(entry.get("numeric_mode", "")),
        "numeric_sample_fallback_count": int(entry.get("numeric_sample_fallback_count") or 0),
        "full_state": False,
    }


def _store_snapshot(snapshots: dict[str, dict[str, Any]], candidate: dict[str, Any]) -> None:
    if not candidate.get("snapshot_id"):
        return
    generated_at = str(candidate.get("generated_at", ""))
    same_generated_key = next(
        (
            key
            for key, item in snapshots.items()
            if generated_at and str(item.get("generated_at", "")) == generated_at
        ),
        None,
    )
    key = same_generated_key or str(candidate["snapshot_id"])
    existing = snapshots.get(key)
    if existing and existing.get("full_state") and not candidate.get("full_state"):
        return
    if existing and candidate.get("full_state"):
        merged = {**existing, **candidate}
        merged["snapshot_id"] = str(candidate["snapshot_id"])
        snapshots.pop(key, None)
        snapshots[str(candidate["snapshot_id"])] = merged
        return
    snapshots[key] = candidate


def _phase_stability(snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    phases = [str(item.get("cycle_phase", "")) for item in snapshots if item.get("cycle_phase")]
    changes = []
    for previous, current in zip(snapshots, snapshots[1:]):
        previous_phase = str(previous.get("cycle_phase", ""))
        current_phase = str(current.get("cycle_phase", ""))
        if previous_phase and current_phase and previous_phase != current_phase:
            changes.append(
                {
                    "from": previous_phase,
                    "to": current_phase,
                    "at": _snapshot_date(current),
                }
            )
    opportunities = max(0, len(phases) - 1)
    churn_rate = len(changes) / opportunities if opportunities else 0.0
    if len(phases) < 2:
        status = "insufficient_history"
    elif churn_rate > 0.5:
        status = "unstable"
    elif changes:
        status = "evolving"
    else:
        status = "stable"
    current_phase = phases[-1] if phases else ""
    current_streak = 0
    for phase in reversed(phases):
        if phase != current_phase:
            break
        current_streak += 1
    return {
        "status": status,
        "current_phase": current_phase,
        "unique_phase_count": len(set(phases)),
        "phase_change_count": len(changes),
        "churn_rate": round(churn_rate, 3),
        "current_phase_streak": current_streak,
        "changes": changes,
    }


def _evidence_continuity(snapshots: list[dict[str, Any]], field: str) -> dict[str, Any]:
    full = [item for item in snapshots if item.get("full_state")]
    if len(full) < 2:
        return {
            "status": "insufficient_history",
            "shared_count": 0,
            "added": [],
            "removed": [],
            "jaccard_similarity": None,
            "review_flag": False,
        }
    previous, current = full[-2], full[-1]
    previous_titles = set(previous.get(field, []))
    current_titles = set(current.get(field, []))
    union = previous_titles | current_titles
    similarity = len(previous_titles & current_titles) / len(union) if union else 1.0
    if previous_titles == current_titles:
        status = "stable"
    elif similarity >= 0.5:
        status = "evolving"
    else:
        status = "changed"
    same_phase = previous.get("cycle_phase") == current.get("cycle_phase")
    return {
        "status": status,
        "previous_snapshot": _snapshot_date(previous),
        "current_snapshot": _snapshot_date(current),
        "shared_count": len(previous_titles & current_titles),
        "added": sorted(current_titles - previous_titles),
        "removed": sorted(previous_titles - current_titles),
        "jaccard_similarity": round(similarity, 3),
        "review_flag": bool(same_phase and union and similarity < 0.25),
    }


def _confidence_calibration(snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    checks = []
    mismatch_count = 0
    for item in snapshots:
        if not item.get("full_state"):
            continue
        snapshot_checks = []
        for label_field, score_field, scope in (
            ("cycle_confidence", "cycle_confidence_score", "global_equity_cycle"),
            ("overall_confidence", "overall_confidence_score", "overall_synthesis"),
        ):
            score = item.get(score_field)
            label = str(item.get(label_field, ""))
            if score is None or not label:
                continue
            expected = _confidence_label(float(score))
            aligned = label == expected
            mismatch_count += int(not aligned)
            snapshot_checks.append(
                {
                    "scope": scope,
                    "label": label,
                    "score": round(float(score), 3),
                    "expected_label": expected,
                    "aligned": aligned,
                }
            )
        if snapshot_checks:
            checks.append({"snapshot": _snapshot_date(item), "checks": snapshot_checks})
    return {
        "status": "aligned" if checks and mismatch_count == 0 else ("needs_review" if mismatch_count else "insufficient_history"),
        "checked_snapshot_count": len(checks),
        "mismatch_count": mismatch_count,
        "thresholds": {"high": 0.75, "medium": 0.55, "low": 0.3, "very_low": 0.0},
        "checks": checks,
    }


def _rule_replay(snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    checks = []
    mismatch_count = 0
    required = {"growth", "inflation_rates", "liquidity_credit", "market_pricing"}
    for item in snapshots:
        scores = dict(item.get("dimension_scores", {}))
        direction_scores = dict(item.get("dimension_direction_scores", {}))
        if (
            not item.get("full_state")
            or not required.issubset(scores)
            or any(scores.get(key) is None for key in required)
            or item.get("cycle_score") is None
        ):
            continue
        available_directions = [
            float(value)
            for value in direction_scores.values()
            if value is not None
        ]
        expected = classify_global_phase(
            growth=float(scores["growth"]),
            rates=float(scores["inflation_rates"]),
            liquidity=float(scores["liquidity_credit"]),
            market=float(scores["market_pricing"]),
            internals=float(scores.get("valuation_internals") or 0.0),
            weighted_score=float(item["cycle_score"]),
            direction_score=sum(available_directions) / len(available_directions) if available_directions else 0.0,
            has_contradictions=bool(item.get("contradiction_count")),
        )
        published = str(item.get("cycle_phase", ""))
        aligned = expected == published
        mismatch_count += int(not aligned)
        checks.append(
            {
                "snapshot": _snapshot_date(item),
                "published_phase": published,
                "replayed_phase": expected,
                "aligned": aligned,
            }
        )
    return {
        "status": "aligned" if checks and mismatch_count == 0 else ("needs_review" if mismatch_count else "insufficient_history"),
        "checked_snapshot_count": len(checks),
        "mismatch_count": mismatch_count,
        "checks": checks,
    }


def _summary(
    calibration_status: str,
    history_depth: str,
    snapshot_count: int,
    full_count: int,
    phase_stability: dict[str, Any],
    rule_replay: dict[str, Any],
    confidence: dict[str, Any],
) -> str:
    return (
        f"Calibration status is {calibration_status.replace('_', ' ')} across {snapshot_count} public snapshots "
        f"({full_count} full report states; history depth {history_depth}). "
        f"Headline phase stability is {str(phase_stability.get('status', '')).replace('_', ' ')}; "
        f"phase-rule replay is {str(rule_replay.get('status', '')).replace('_', ' ')} and confidence labels are "
        f"{str(confidence.get('status', '')).replace('_', ' ')}."
    )


def _titles(records: Any) -> list[str]:
    if not isinstance(records, list):
        return []
    return sorted(
        {
            str(item.get("title", ""))
            for item in records
            if isinstance(item, dict) and item.get("title")
        }
    )


def _confidence_label(score: float) -> str:
    for threshold, label in CONFIDENCE_THRESHOLDS:
        if score >= threshold:
            return label
    return "very low"


def _snapshot_sort_key(item: dict[str, Any]) -> tuple[str, str]:
    return (str(item.get("generated_at") or item.get("data_as_of") or ""), str(item.get("snapshot_id", "")))


def _snapshot_date(item: dict[str, Any]) -> str:
    return str(item.get("generated_at") or item.get("data_as_of") or "")[:10]


def _optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return round(float(value), 3)
