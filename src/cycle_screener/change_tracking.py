from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


SIGNAL_MOVE_THRESHOLD = 0.15
MODERATE_SCORE_MOVE = 2.0
MAJOR_SCORE_MOVE = 5.0
MAJOR_RANK_MOVE = 3
MARKET_MOVE_THRESHOLD = 5.0


def compare_report_states(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    subsector_changes = _subsector_changes(previous.get("subsectors", []), current.get("subsectors", []))
    source_changes = _source_status_changes(previous.get("source_status", []), current.get("source_status", []))
    research_changes = _research_fact_changes(previous.get("research_facts", []), current.get("research_facts", []))
    cycle_changes = _cycle_state_changes(previous.get("cycle_state", {}), current.get("cycle_state", {}))

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "previous_generated_at": previous.get("generated_at"),
        "current_generated_at": current.get("generated_at"),
        "summary": {
            "subsector_changes": len(subsector_changes),
            "major_score_moves": sum(change.get("score_move") == "major" for change in subsector_changes),
            "major_rank_moves": sum(abs(change.get("rank_delta", 0)) >= MAJOR_RANK_MOVE for change in subsector_changes),
            "source_status_changes": len(source_changes),
            "new_research_facts": len(research_changes["new"]),
            "removed_research_facts": len(research_changes["removed"]),
            "changed_research_facts": len(research_changes["changed"]),
            "cycle_state_changes": len(cycle_changes),
        },
        "cycle_state_changes": cycle_changes,
        "subsector_changes": subsector_changes,
        "source_status_changes": source_changes,
        "research_fact_changes": research_changes,
    }


def _subsector_changes(previous_items: list[dict[str, Any]], current_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    previous_by_slug = {item["slug"]: item for item in previous_items}
    current_by_slug = {item["slug"]: item for item in current_items}
    changes: list[dict[str, Any]] = []

    for slug in sorted(set(previous_by_slug) | set(current_by_slug)):
        previous = previous_by_slug.get(slug)
        current = current_by_slug.get(slug)
        if previous is None:
            changes.append({"slug": slug, "change_type": "new_subsector", "current_rank": current.get("rank") if current else None})
            continue
        if current is None:
            changes.append({"slug": slug, "change_type": "removed_subsector", "previous_rank": previous.get("rank")})
            continue

        rank_delta = int(previous["rank"]) - int(current["rank"])
        score_delta = _delta(previous.get("opportunity_score"), current.get("opportunity_score"))
        signal_delta = _signal_delta(previous.get("signals", {}), current.get("signals", {}))
        market_delta = _market_delta(previous.get("market_cycle", {}), current.get("market_cycle", {}))

        if rank_delta or abs(score_delta) >= MODERATE_SCORE_MOVE or signal_delta or market_delta:
            changes.append(
                {
                    "slug": slug,
                    "name": current.get("name", previous.get("name", slug)),
                    "change_type": "changed",
                    "previous_rank": previous["rank"],
                    "current_rank": current["rank"],
                    "rank_delta": rank_delta,
                    "previous_score": previous.get("opportunity_score"),
                    "current_score": current.get("opportunity_score"),
                    "score_delta": score_delta,
                    "score_move": _score_move(score_delta),
                    "signal_delta": signal_delta,
                    "market_cycle_delta": market_delta,
                }
            )

    return sorted(changes, key=lambda item: (abs(item.get("score_delta", 0)), abs(item.get("rank_delta", 0))), reverse=True)


def _signal_delta(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, float]:
    result = {}
    for signal in sorted(set(previous) | set(current)):
        delta = _delta(previous.get(signal, 0), current.get(signal, 0))
        if abs(delta) >= SIGNAL_MOVE_THRESHOLD:
            result[signal] = delta
    return result


def _market_delta(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, float]:
    result = {}
    for field in ("relative_price_index", "valuation_proxy", "driver_pressure"):
        delta = _delta(previous.get(field, 0), current.get(field, 0))
        threshold = SIGNAL_MOVE_THRESHOLD if field == "driver_pressure" else MARKET_MOVE_THRESHOLD
        if abs(delta) >= threshold:
            result[field] = delta
    return result


def _source_status_changes(previous_items: list[dict[str, Any]], current_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    previous_by_slug = {item["source_slug"]: item for item in previous_items}
    current_by_slug = {item["source_slug"]: item for item in current_items}
    changes = []
    for slug in sorted(set(previous_by_slug) | set(current_by_slug)):
        previous = previous_by_slug.get(slug)
        current = current_by_slug.get(slug)
        if previous is None:
            changes.append({"source_slug": slug, "change_type": "new_source", "current_status": current.get("status") if current else None})
            continue
        if current is None:
            changes.append({"source_slug": slug, "change_type": "removed_source", "previous_status": previous.get("status")})
            continue
        if previous.get("status") != current.get("status"):
            changes.append(
                {
                    "source_slug": slug,
                    "change_type": "status_changed",
                    "previous_status": previous.get("status"),
                    "current_status": current.get("status"),
                    "status_delta": f"{previous.get('status')} -> {current.get('status')}",
                }
            )
    return changes


def _research_fact_changes(previous_items: list[dict[str, Any]], current_items: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    previous_by_id = {item["fact_id"]: item for item in previous_items}
    current_by_id = {item["fact_id"]: item for item in current_items}
    new = [current_by_id[fact_id] for fact_id in sorted(set(current_by_id) - set(previous_by_id))]
    removed = [previous_by_id[fact_id] for fact_id in sorted(set(previous_by_id) - set(current_by_id))]
    changed = []
    for fact_id in sorted(set(previous_by_id) & set(current_by_id)):
        previous = previous_by_id[fact_id]
        current = current_by_id[fact_id]
        fields = ["claim", "source_date", "confidence", "source_quality"]
        changed_fields = {field: {"previous": previous.get(field), "current": current.get(field)} for field in fields if previous.get(field) != current.get(field)}
        if changed_fields:
            changed.append({"fact_id": fact_id, "subsector_slug": current.get("subsector_slug"), "changed_fields": changed_fields})
    return {"new": new, "removed": removed, "changed": changed}


def _cycle_state_changes(previous: dict[str, Any], current: dict[str, Any]) -> list[dict[str, Any]]:
    if not previous and not current:
        return []
    if not previous:
        return [{"scope": "cycle_state", "change_type": "new_cycle_state", "current_phase": current.get("global_equity_cycle", {}).get("phase")}]
    if not current:
        return [{"scope": "cycle_state", "change_type": "removed_cycle_state", "previous_phase": previous.get("global_equity_cycle", {}).get("phase")}]

    changes: list[dict[str, Any]] = []
    previous_global = previous.get("global_equity_cycle", {})
    current_global = current.get("global_equity_cycle", {})
    global_fields = ("phase", "status", "direction", "confidence")
    changed_fields = {
        field: {"previous": previous_global.get(field), "current": current_global.get(field)}
        for field in global_fields
        if previous_global.get(field) != current_global.get(field)
    }
    score_delta = _delta(previous_global.get("score", 0), current_global.get("score", 0))
    if changed_fields or abs(score_delta) >= SIGNAL_MOVE_THRESHOLD:
        changes.append(
            {
                "scope": "global_equity_cycle",
                "change_type": "changed",
                "changed_fields": changed_fields,
                "score_delta": score_delta,
                "previous_phase": previous_global.get("phase"),
                "current_phase": current_global.get("phase"),
            }
        )

    previous_dimensions = {item.get("dimension_id"): item for item in previous.get("dimensions", [])}
    current_dimensions = {item.get("dimension_id"): item for item in current.get("dimensions", [])}
    for dimension_id in sorted(set(previous_dimensions) | set(current_dimensions)):
        previous_dimension = previous_dimensions.get(dimension_id)
        current_dimension = current_dimensions.get(dimension_id)
        if previous_dimension is None:
            changes.append({"scope": "dimension", "dimension_id": dimension_id, "change_type": "new_dimension", "current_phase": current_dimension.get("phase") if current_dimension else None})
            continue
        if current_dimension is None:
            changes.append({"scope": "dimension", "dimension_id": dimension_id, "change_type": "removed_dimension", "previous_phase": previous_dimension.get("phase")})
            continue
        changed_fields = {
            field: {"previous": previous_dimension.get(field), "current": current_dimension.get(field)}
            for field in global_fields
            if previous_dimension.get(field) != current_dimension.get(field)
        }
        score_delta = _delta(previous_dimension.get("score", 0), current_dimension.get("score", 0))
        confidence_delta = _delta(previous_dimension.get("confidence_score", 0), current_dimension.get("confidence_score", 0))
        if changed_fields or abs(score_delta) >= SIGNAL_MOVE_THRESHOLD or abs(confidence_delta) >= SIGNAL_MOVE_THRESHOLD:
            changes.append(
                {
                    "scope": "dimension",
                    "dimension_id": dimension_id,
                    "title": current_dimension.get("title", previous_dimension.get("title", dimension_id)),
                    "change_type": "changed",
                    "changed_fields": changed_fields,
                    "score_delta": score_delta,
                    "confidence_delta": confidence_delta,
                    "previous_phase": previous_dimension.get("phase"),
                    "current_phase": current_dimension.get("phase"),
                }
            )

    previous_contradictions = {item.get("title") for item in previous.get("contradictions", [])}
    current_contradictions = {item.get("title") for item in current.get("contradictions", [])}
    for title in sorted(current_contradictions - previous_contradictions):
        changes.append({"scope": "cycle_contradiction", "change_type": "new_contradiction", "title": title})
    for title in sorted(previous_contradictions - current_contradictions):
        changes.append({"scope": "cycle_contradiction", "change_type": "resolved_contradiction", "title": title})

    return changes


def _score_move(score_delta: float) -> str:
    if abs(score_delta) >= MAJOR_SCORE_MOVE:
        return "major"
    if abs(score_delta) >= MODERATE_SCORE_MOVE:
        return "moderate"
    return "minor"


def _delta(previous: Any, current: Any) -> float:
    return round(float(current) - float(previous), 3)
