"""Observation health shared by scoring, reporting and publication.

Fetching a series successfully does not establish either its freshness or its
fitness for scoring. Observation dates are never replaced by the attempt date.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd

from .indicators import indicator_by_slug, public_indicator_slug


def freshness_status(age_days: int, expected_release_days: int = 75) -> str:
    if age_days < 0:
        return "future_dated"
    threshold = max(int(expected_release_days), 1)
    if age_days > max(round(threshold * 1.6), threshold + 15):
        return "very_stale"
    return "stale" if age_days > threshold else "current"


def observation_health(observations: pd.DataFrame, *, as_of=None,
                       sample: bool = False, supported_slugs=None) -> list[dict[str, Any]]:
    now = pd.Timestamp(as_of if as_of is not None else datetime.now(timezone.utc))
    now = now.tz_localize("UTC") if now.tzinfo is None else now.tz_convert("UTC")
    definitions = indicator_by_slug()
    frame = observations.copy()
    for column in ("indicator_slug", "observed_at", "value", "source"):
        if column not in frame:
            frame[column] = pd.Series(dtype="object")
    frame["date"] = pd.to_datetime(frame["observed_at"], errors="coerce", utc=True)
    frame["numeric_value"] = pd.to_numeric(frame["value"], errors="coerce").replace([float("inf"), -float("inf")], float("nan"))
    records = []
    for slug in sorted(set(definitions) | set(frame["indicator_slug"].dropna().astype(str))):
        definition = definitions.get(slug)
        group = frame[frame["indicator_slug"] == slug]
        valid = group.dropna(subset=["date", "numeric_value"]).sort_values("date")
        latest = valid.iloc[-1] if not valid.empty else None
        observed = latest["date"] if latest is not None else None
        source = str(latest["source"]) if latest is not None else ""
        sources = sorted(set(group["source"].dropna().astype(str)))
        fallback = "sample_fallback" in sources
        category = "missing" if latest is None else "numeric_sample_fallback" if fallback else "deterministic_sample" if sample or source == "sample" else "live_numeric" if source else "unverified"
        reference_period = definition.reference_period if definition else "date"
        if definition and definition.source in {"world_bank_commodity", "dbnomics_oecd_cli", "dbnomics_bis_policy", "ssb_cpi", "academic_gpr"}:
            reference_period = "month"
        if definition and definition.source == "world_bank_indicator":
            reference_period = "year"
        if slug == "us_equity_market_cap_gdp_proxy":
            reference_period = "quarter"
        if slug == "oil_curve_pressure":
            reference_period = "month"
        period = observed.tz_localize(None).to_period({"month": "M", "year": "Y", "quarter": "Q"}[reference_period]) if observed is not None and reference_period != "date" else None
        period_start = period.start_time.date() if period is not None else observed.date() if observed is not None else None
        period_end = period.end_time.date() if period is not None else observed.date() if observed is not None else None
        age = (now.date() - observed.date()).days if observed is not None else None
        freshness_age = (now.date() - period_end).days if period_end is not None else None
        cadence = definition.expected_release_days if definition else 75
        future = bool(observed is not None and (observed > now or period_end > now.date()))
        freshness = "missing" if latest is None else "future_dated" if future else freshness_status(freshness_age, cadence)
        enough_history = supported_slugs is None or slug in supported_slugs
        eligible = freshness == "current" and enough_history and category == "live_numeric"
        reason = "included" if eligible else "insufficient_history" if freshness == "current" and not enough_history else freshness if freshness != "current" else category
        records.append({
            "indicator_slug": slug, "display_slug": public_indicator_slug(slug),
            "legacy_slug": slug if public_indicator_slug(slug) != slug else "",
            "indicator_name": definition.name if definition else slug,
            "indicator_description": definition.description if definition else "",
            "latest_observed_at": observed.date().isoformat() if observed is not None else None,
            "reference_period": reference_period,
            "observation_period_start": period_start.isoformat() if period_start else None,
            "observation_period_end": period_end.isoformat() if period_end else None,
            "freshness_reference_date": period_end.isoformat() if period_end else None,
            "age_since_reference_period_end_days": freshness_age,
            "age_days": age, "observation_count": len(valid),
            "invalid_observation_count": len(group) - len(valid),
            "source": source, "sources_seen": sources, "source_category": category,
            "has_sample_fallback": fallback, "freshness_status": freshness,
            "future_dated_observation": future,
            "raw_latest_observed_at": observed.isoformat() if future else "",
            "expected_release_days": cadence, "critical": bool(definition and definition.critical),
            "scoring_eligible": eligible, "exclusion_reason": reason,
            "history_supported": enough_history,
        })
    return records


def numeric_health(records: list[dict[str, Any]]) -> dict[str, Any]:
    def slugs(predicate):
        return [r["indicator_slug"] for r in records if predicate(r)]
    live = slugs(lambda r: r["source_category"] == "live_numeric")
    usable = slugs(lambda r: r.get("scoring_eligible", False))
    missing = slugs(lambda r: r["freshness_status"] == "missing")
    stale = slugs(lambda r: r["freshness_status"] in {"stale", "very_stale"})
    future = slugs(lambda r: r["freshness_status"] == "future_dated")
    fallback = slugs(lambda r: r["has_sample_fallback"])
    sample = slugs(lambda r: r["source_category"] == "deterministic_sample")
    critical = slugs(lambda r: r.get("critical") and not r.get("scoring_eligible"))
    status = "blocked" if not usable or critical or future or fallback else "current" if len(usable) == len(records) else "degraded"
    return {
        "status": status, "mode": "deterministic_sample" if sample and len(sample) == len(records) else "live_with_numeric_sample_fallback" if fallback else "live_numeric" if live else "unknown",
        "indicator_count": len(records), "configured_indicator_count": len(records),
        "live_indicator_count": len(live), "usable_indicator_count": len(usable),
        "usable_coverage_ratio": len(usable) / len(records) if records else 0.0,
        "usable_indicators": usable,
        "missing_indicator_count": len(missing), "missing_indicators": missing,
        "stale_indicator_count": len(stale), "stale_indicators": stale,
        "future_indicator_count": len(future), "future_indicators": future,
        "sample_fallback_indicator_count": len(fallback), "sample_fallback_indicators": fallback,
        "sample_build_indicator_count": len(sample), "unusable_critical_indicators": critical,
    }


def public_health(report_state: dict[str, Any]) -> dict[str, Any]:
    numeric = report_state["source_health"]["numeric"]
    records = report_state["source_freshness"]
    dates = [r["latest_observed_at"] for r in records if r.get("scoring_eligible") and r.get("latest_observed_at")]
    generated = pd.Timestamp(report_state["generated_at"])
    generated = generated.tz_localize("UTC") if generated.tzinfo is None else generated.tz_convert("UTC")
    deadlines = [generated + timedelta(days=7)]
    deadlines.extend(pd.Timestamp(r["freshness_reference_date"], tz="UTC") + timedelta(days=r["expected_release_days"] + 1) for r in records if r.get("scoring_eligible") and r.get("freshness_reference_date"))
    return {
        "schema_version": "source-health-v1", "status": numeric["status"],
        "generated_at": report_state["generated_at"],
        "status_as_of": report_state["generated_at"],
        "expires_at": min(deadlines).isoformat(),
        "source_observation_start": min(dates) if dates else None,
        "source_observation_end": max(dates) if dates else None,
        "coverage": numeric,
        "issues": [{"source": r["indicator_slug"], "reason": r["exclusion_reason"]} for r in records if not r.get("scoring_eligible")],
        "sources": records,
        "research_validation": "not_established",
        "next_expected_update_days": 7,
        "observation_date_basis": "Native observation/reference dates; retrieval and report generation are separate. Release-cadence age uses the explicitly identified reference-period end without relabeling the native observation. Yahoo uses completed prior exchange dates.",
    }


def assert_publication_health(state: dict[str, Any]) -> None:
    records = state.get("source_freshness", [])
    numeric = state.get("source_health", {}).get("numeric", {})
    if not records or not numeric or numeric.get("status") == "blocked":
        raise RuntimeError("Source health blocks publication: missing, stale critical, future-dated or fallback inputs. Preserve the previous valid edition.")
    expected = numeric_health(records)
    if any(numeric.get(key) != value for key, value in expected.items()):
        raise RuntimeError("Source-health counts/status do not match per-source evidence.")
    generated = pd.Timestamp(state["generated_at"])
    for row in records:
        if not row.get("scoring_eligible"):
            continue
        observed = pd.Timestamp(row["freshness_reference_date"])
        age = (generated.date() - observed.date()).days
        if freshness_status(age, row["expected_release_days"]) != "current" or row.get("source_category") != "live_numeric" or not row.get("history_supported"):
            raise RuntimeError("Scoring eligibility does not match publication-time source observations.")
