from __future__ import annotations

from pathlib import Path
import sys
import math

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cycle_screener.config import get_settings
from cycle_screener.export_static import export_static
from cycle_screener.refresh import refresh
from cycle_screener.storage import RadarStore
from cycle_screener.taxonomy import subsector_by_slug


st.set_page_config(page_title="Oslo Macro and Market-cycle Radar", layout="wide")


def load_tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    settings = get_settings()
    store = RadarStore(settings.database_path)
    scores = store.table("subsector_scores")
    observations = store.table("observations")
    statuses = store.table("source_status")
    research_profiles = store.table("subsector_research_profiles")
    research_facts = store.table("research_facts")
    market_cycle = store.table("subsector_market_cycle")
    store.close()
    if scores.empty:
        refresh(sample=True)
        return load_tables()
    return scores, observations, statuses, research_profiles, research_facts, market_cycle


def score_color(value: float) -> str:
    if value >= 70:
        return "#16735f"
    if value >= 55:
        return "#c28722"
    return "#8b2f26"


def highlight_signal_table(frame: pd.DataFrame) -> pd.io.formats.style.Styler:
    numeric_columns = ["Score", "Recovery", "Valuation/proxy", "Momentum", "Macro", "Narrative gap"]
    quantiles = {
        column: {
            "high": frame[column].quantile(0.8),
            "low": frame[column].quantile(0.2),
        }
        for column in numeric_columns
    }

    def style_cell(value: object, column: str) -> str:
        if column not in numeric_columns:
            return ""
        numeric = float(value)
        high = quantiles[column]["high"]
        low = quantiles[column]["low"]
        if column == "Score":
            if numeric >= high:
                return "background-color: #dcefe7; color: #0e4f42; font-weight: 700;"
            if numeric <= low:
                return "background-color: #f7e4df; color: #79281f;"
            return ""
        if numeric >= high and numeric > 0:
            return "background-color: #dcefe7; color: #0e4f42; font-weight: 700;"
        if numeric <= low and numeric < 0:
            return "background-color: #f7e4df; color: #79281f; font-weight: 700;"
        if abs(numeric) >= 0.5:
            return "background-color: #fff0cf; color: #6c4a00; font-weight: 700;"
        return ""

    def style_column(column: pd.Series) -> list[str]:
        return [style_cell(value, column.name) for value in column]

    return (
        frame.style.apply(style_column, subset=numeric_columns)
        .format(
            {
                "Score": "{:.1f}",
                "Recovery": "{:+.3f}",
                "Valuation/proxy": "{:+.3f}",
                "Momentum": "{:+.3f}",
                "Macro": "{:+.3f}",
                "Narrative gap": "{:+.3f}",
                "Confidence": "{:.0%}",
            }
        )
    )


def symmetric_axis_range(normalized: pd.DataFrame) -> list[float]:
    low = float(normalized.min(numeric_only=True).min())
    high = float(normalized.max(numeric_only=True).max())
    distance = max(abs(high - 100), abs(100 - low), 10)
    padded = distance * 1.15
    lower = math.floor((100 - padded) / 10) * 10
    upper = math.ceil((100 + padded) / 10) * 10
    return [lower, upper]


def write_research_block(title: str, text: object) -> None:
    st.markdown(f"**{title}**")
    lines = [line.strip() for line in str(text or "").splitlines() if line.strip()]
    if not lines:
        st.write("No reviewed research note recorded yet.")
        return
    for line in lines:
        st.write(line)


def review_badge(status: object) -> str:
    label = str(status or "unreviewed").replace("_", " ").title()
    return f"`{label}`"


def latest_market_cycle_summary(frame: pd.DataFrame) -> dict[str, float]:
    if frame.empty:
        return {}
    ordered = frame.copy()
    ordered["observed_at"] = pd.to_datetime(ordered["observed_at"], errors="coerce")
    ordered = ordered.dropna(subset=["observed_at"]).sort_values("observed_at")
    latest = ordered.iloc[-1]
    prior = ordered.iloc[-13] if len(ordered) >= 13 else ordered.iloc[0]
    return {
        "relative_price": float(latest["relative_price_index"]),
        "relative_price_change": float(latest["relative_price_index"] - prior["relative_price_index"]),
        "valuation_proxy": float(latest["valuation_proxy"]),
        "valuation_change": float(latest["valuation_proxy"] - prior["valuation_proxy"]),
        "driver_pressure": float(latest["driver_pressure"]),
    }


def cycle_read(selected: pd.Series, summary: dict[str, float]) -> str:
    if not summary:
        return "Cycle read: market price and valuation history is not available yet."

    recovery = float(selected["recovery_potential"])
    macro = float(selected["macro_tailwind"])
    valuation = float(selected["valuation_proxy"])
    relative_change = summary["relative_price_change"]
    valuation_level = summary["valuation_proxy"]
    driver_pressure = summary["driver_pressure"]

    if recovery > 0.25 and macro >= 0 and relative_change > 0 and valuation_level <= 105:
        stance = "Cycle read: improving setup"
        reason = "recovery, macro, relative price, and valuation proxy are pointing in the same direction."
    elif recovery > 0.2 and valuation > 0 and relative_change <= 0:
        stance = "Cycle read: early watch"
        reason = "the scoring setup is improving, but relative sector price has not confirmed it yet."
    elif macro < -0.2 or driver_pressure < -0.35:
        stance = "Cycle read: headwind watch"
        reason = "macro or driver pressure remains hostile enough to demand stronger confirmation."
    else:
        stance = "Cycle read: mixed evidence"
        reason = "the current data does not yet show a clean phase change."
    return f"{stance} - {reason}"


def source_evidence_table(facts: pd.DataFrame) -> pd.DataFrame:
    if facts.empty:
        return pd.DataFrame()
    display_facts = facts.copy()
    display_facts["Source"] = display_facts.apply(
        lambda row: f"{row['source_name']} ({row['source_quality']})",
        axis=1,
    )
    display_facts["Review"] = display_facts["review_status"].str.replace("_", " ").str.title()
    display_facts["Confidence"] = display_facts["confidence"].astype(float).map(lambda value: f"{value:.0%}")
    return display_facts[
        [
            "theme",
            "claim",
            "Source",
            "source_url",
            "source_date",
            "captured_at",
            "Confidence",
            "Review",
            "evidence_scope",
        ]
    ].rename(
        columns={
            "theme": "Theme",
            "claim": "Claim",
            "source_url": "URL/File",
            "source_date": "Source date",
            "captured_at": "Captured",
            "evidence_scope": "Scope",
        }
    )


scores, observations, statuses, research_profiles, research_facts, market_cycle = load_tables()
taxonomy = subsector_by_slug()
settings = get_settings()
status_store = RadarStore(settings.database_path)
backend = status_store.backend
status_store.close()

st.title("Oslo-Linked Macro and Market-cycle Opportunity Radar")
st.caption("Research leads for subsector recovery potential. Not investment advice.")

top_cols = st.columns([1, 1, 1, 1])
top_cols[0].metric("Subsectors", f"{len(scores)}")
top_cols[1].metric("Top score", f"{scores['opportunity_score'].max():.1f}")
top_cols[2].metric("Median confidence", f"{scores['confidence'].median():.0%}")
top_cols[3].metric("Data backend", backend)

actions = st.columns([1, 1, 5])
if actions[0].button("Refresh sample data", width="stretch"):
    refresh(sample=True)
    st.rerun()
if actions[1].button("Export static HTML", width="stretch"):
    output = export_static()
    st.success(f"Exported {output}")

group_filter = st.multiselect(
    "Groups",
    options=sorted(scores["group_name"].unique()),
    default=sorted(scores["group_name"].unique()),
)
filtered = scores[scores["group_name"].isin(group_filter)].copy()

left, right = st.columns([1.25, 1])
with left:
    st.subheader("Signal Heatmap")
    heatmap = filtered.set_index("name")[
        ["recovery_potential", "valuation_proxy", "momentum", "macro_tailwind", "narrative_divergence"]
    ]
    heatmap = heatmap.rename(
        columns={
            "recovery_potential": "Recovery",
            "valuation_proxy": "Valuation/proxy",
            "momentum": "Momentum",
            "macro_tailwind": "Macro",
            "narrative_divergence": "Narrative gap",
        }
    )
    figure = px.imshow(
        heatmap,
        color_continuous_scale="RdYlGn",
        zmin=-1,
        zmax=1,
        aspect="auto",
        labels={"x": "Signal", "y": "Subsector", "color": "Score"},
    )
    figure.update_layout(margin=dict(l=0, r=0, t=8, b=0), height=max(360, len(heatmap) * 28))
    st.plotly_chart(figure, width="stretch")

with right:
    st.subheader("Top Research Leads")
    for _, row in filtered.head(5).iterrows():
        color = score_color(float(row["opportunity_score"]))
        st.markdown(
            f"""
            <div style="border-left: 5px solid {color}; padding: 8px 12px; margin-bottom: 10px; background: #f8faf7;">
              <strong>{row['name']}</strong><br>
              Score {row['opportunity_score']:.1f} | confidence {row['confidence']:.0%}<br>
              <span style="color:#56615a;">{row['explanation']}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.subheader("Opportunity Radar")
st.caption(
    "Highlighted values stand out among the currently filtered subsectors: green is high-positive, red is low-negative, and amber is a large absolute signal."
)
display = filtered[
    [
        "name",
        "group_name",
        "opportunity_score",
        "recovery_potential",
        "valuation_proxy",
        "momentum",
        "macro_tailwind",
        "narrative_divergence",
        "confidence",
        "data_confidence",
    ]
].rename(
    columns={
        "name": "Subsector",
        "group_name": "Group",
        "opportunity_score": "Score",
        "recovery_potential": "Recovery",
        "valuation_proxy": "Valuation/proxy",
        "momentum": "Momentum",
        "macro_tailwind": "Macro",
        "narrative_divergence": "Narrative gap",
        "confidence": "Confidence",
        "data_confidence": "Data quality",
    }
)
st.dataframe(
    highlight_signal_table(display),
    width="stretch",
    hide_index=True,
)

st.subheader("Subsector Drilldown")
selected_name = st.selectbox("Subsector", filtered["name"].tolist())
selected = filtered[filtered["name"] == selected_name].iloc[0]
subsector = taxonomy[selected["slug"]]

detail_cols = st.columns([1, 1, 1, 1])
detail_cols[0].metric("Opportunity score", f"{selected['opportunity_score']:.1f}")
detail_cols[1].metric("Recovery", f"{selected['recovery_potential']:+.2f}")
detail_cols[2].metric("Macro", f"{selected['macro_tailwind']:+.2f}")
detail_cols[3].metric("Confidence", f"{selected['confidence']:.0%}")

st.write(selected["explanation"])
st.write("Drivers: " + ", ".join(subsector.drivers))
st.write("Macro sensitivities: " + ", ".join(subsector.macro_sensitivities))

profile = research_profiles[research_profiles["subsector_slug"] == selected["slug"]]
facts = research_facts[research_facts["subsector_slug"] == selected["slug"]].copy()
selected_market = market_cycle[market_cycle["subsector_slug"] == selected["slug"]].copy()
market_summary = latest_market_cycle_summary(selected_market)

st.subheader("Research Evidence")
st.caption("Source-backed research context is shown separately from numeric scoring. Unreviewed claims do not affect the opportunity score.")

if profile.empty:
    st.info("No research profile has been recorded for this subsector yet.")
else:
    profile_row = profile.iloc[0]
    st.markdown(
        f"""
        <div style="border:1px solid #d8e1dc; border-left:6px solid {score_color(float(selected['opportunity_score']))}; background:#f7faf8; padding:14px 16px; margin:8px 0 16px;">
          <div style="font-size:13px; color:#536058; text-transform:uppercase; letter-spacing:0;">Highlighted research conclusion</div>
          <div style="font-size:19px; font-weight:700; color:#1c2b24; margin-top:4px;">{cycle_read(selected, market_summary)}</div>
          <div style="margin-top:8px; color:#2f3b35;">{profile_row['cycle_conclusion']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write(f"Scope: {profile_row['scope']}")
    st.write(f"Phase hypothesis: {profile_row['current_phase_hypothesis']}")
    st.write(f"Review status: {review_badge(profile_row['review_status'])} | Updated: {profile_row['updated_at']}")

    summary_cols = st.columns([1, 1, 1])
    if market_summary:
        summary_cols[0].metric("Relative price", f"{market_summary['relative_price']:.1f}", f"{market_summary['relative_price_change']:+.1f} 12m")
        summary_cols[1].metric("Valuation proxy", f"{market_summary['valuation_proxy']:.1f}", f"{market_summary['valuation_change']:+.1f} 12m")
        summary_cols[2].metric("Driver pressure", f"{market_summary['driver_pressure']:+.2f}")

    section_cols = st.columns([1, 1])
    with section_cols[0]:
        write_research_block("Why now?", profile_row["why_now"])
        write_research_block("Valuation context", profile_row["valuation_context"])
        write_research_block("Catalysts", profile_row["catalysts"])
    with section_cols[1]:
        write_research_block("Market-cycle watch", profile_row["market_cycle_watch"])
        write_research_block("Key debates", profile_row["key_debates"])
        write_research_block("Risks", profile_row["risks"])

    st.markdown("**Source evidence**")
    evidence_display = source_evidence_table(facts)
    if evidence_display.empty:
        st.info("No source-backed facts recorded yet.")
    else:
        st.dataframe(evidence_display, width="stretch", hide_index=True)

st.subheader("Sector Price, Valuation, And Driver Picture")
if selected_market.empty:
    st.info("No sector price or valuation proxy history available for this subsector.")
else:
    selected_market["observed_at"] = pd.to_datetime(selected_market["observed_at"], errors="coerce")
    selected_market = selected_market.dropna(subset=["observed_at"]).sort_values("observed_at")
    market_chart = go.Figure()
    for column, label in [
        ("price_index", "Subsector price proxy"),
        ("benchmark_index", "Oslo benchmark proxy"),
        ("relative_price_index", "Relative price"),
        ("valuation_proxy", "Valuation proxy"),
    ]:
        market_chart.add_trace(
            go.Scatter(
                x=selected_market["observed_at"],
                y=selected_market[column],
                mode="lines",
                name=label,
                hovertemplate="%{x|%Y-%m-%d}<br>%{y:.1f}<extra>%{fullData.name}</extra>",
            )
        )
    market_chart.add_hline(y=100, line_width=1, line_dash="dash", line_color="#8a928c")
    market_chart.update_layout(
        height=380,
        margin=dict(l=0, r=0, t=8, b=0),
        yaxis=dict(title="Indexed / proxy level"),
        xaxis=dict(title=None),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    st.plotly_chart(market_chart, width="stretch")

st.subheader("Macro And Market-cycle Driver Factors")
chart_data = observations[observations["indicator_slug"].isin(subsector.proxy_indicators)].copy()
if not chart_data.empty:
    chart_data["observed_at"] = pd.to_datetime(chart_data["observed_at"], errors="coerce")
    pivot = chart_data.pivot_table(index="observed_at", columns="indicator_slug", values="value", aggfunc="mean").sort_index()
    normalized = (pivot / pivot.iloc[0] * 100).dropna(how="all")
    chart = go.Figure()
    for column in normalized.columns:
        chart.add_trace(
            go.Scatter(
                x=normalized.index,
                y=normalized[column],
                mode="lines",
                name=column,
                hovertemplate="%{x|%Y-%m-%d}<br>%{y:.1f}<extra>%{fullData.name}</extra>",
            )
        )
    chart.add_hline(y=100, line_width=1, line_dash="dash", line_color="#8a928c")
    chart.update_layout(
        height=360,
        margin=dict(l=0, r=0, t=8, b=0),
        yaxis=dict(title="Indexed to 100", range=symmetric_axis_range(normalized)),
        xaxis=dict(title=None),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    st.plotly_chart(chart, width="stretch")
else:
    st.info("No indicator history available for this subsector.")

st.subheader("Source Status")
if statuses.empty:
    st.info("No source status has been recorded yet.")
else:
    st.dataframe(statuses.tail(20), width="stretch", hide_index=True)

st.caption("Public exports exclude manual reports and private notes by design.")
