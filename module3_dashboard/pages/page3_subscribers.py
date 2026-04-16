# ============================================================
# NigeriaRGI  |  Module 3  |  pages/page3_subscribers.py
# Page 3: Subscriber Health & Churn Risk
# Subscriber base, penetration gaps, churn risk early warning.
# ============================================================

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from utils import metrics

BLUE  = "#0057A8"
RED   = "#D62728"
AMBER = "#F5A623"
GREEN = "#2CA02C"


def render(df: pd.DataFrame):

    # ── Header ───────────────────────────────────────────────
    st.markdown("""
    <div class="page-header">
        <h2 style="margin:0; color:white;">👥 Subscriber Health & Churn Risk</h2>
        <p style="margin:4px 0 0 0; color:#AEC6E8; font-size:0.9rem;">
            Subscriber base · Penetration gaps · Churn risk early warning
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI Row ──────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)

    active_subs  = metrics.total_active_subs(df)
    churned_subs = metrics.total_churned_subs(df)
    penetration  = metrics.avg_penetration_rate(df)
    churn_lgas   = metrics.churn_risk_lgas(df)
    n_churn_risk = len(churn_lgas)

    k1.metric("Active Subscribers",
              f"{active_subs:,}",
              help="Total active subscribers on latest date in filtered period")
    k2.metric("Churned (Period)",
              f"{churned_subs:,}",
              help="Total churned subscribers across the filtered period")
    k3.metric("Avg Penetration Rate",
              metrics.format_pct(penetration),
              delta=f"{penetration - 45:.1f}% vs 45% whitespace threshold",
              delta_color="normal" if penetration >= 45 else "inverse",
              help="Average penetration rate across filtered LGAs")
    k4.metric("Churn Risk LGAs",
              str(n_churn_risk),
              delta="Active risk signals" if n_churn_risk > 0 else "No active signals",
              delta_color="inverse" if n_churn_risk > 0 else "normal",
              help="LGAs showing simultaneous subscriber and ARPU decline over 7 days")

    st.markdown("---")

    # ── Row 1: Active subs by state + Subscriber trend ───────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Active Subscribers by State")
        subs_state = (
            df[df["date"] == df["date"].max()]
            .groupby("state")["active_subs"]
            .sum()
            .reset_index()
            .sort_values("active_subs", ascending=True)
        )
        fig = px.bar(
            subs_state,
            x="active_subs",
            y="state",
            orientation="h",
            color="active_subs",
            color_continuous_scale="Blues",
            labels={"active_subs": "Active Subscribers", "state": ""},
            text="active_subs",
        )
        fig.update_traces(
            texttemplate="%{text:,.0f}", textposition="outside", textfont_size=9)
        fig.update_layout(
            coloraxis_showscale=False,
            margin=dict(t=20, b=20, l=0, r=0),
            height=360,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Daily Subscriber Trend")
        trend = metrics.subscriber_trend(df)
        selected = df["state"].unique().tolist()
        if len(selected) <= 4:
            trend_state = (
                df.groupby(["date", "state"])["active_subs"]
                .sum()
                .reset_index()
            )
            fig2 = px.line(
                trend_state,
                x="date",
                y="active_subs",
                color="state",
                labels={"active_subs": "Active Subscribers", "date": ""},
            )
        else:
            fig2 = px.line(
                trend,
                x="date",
                y="active_subs",
                labels={"active_subs": "Active Subscribers", "date": ""},
                color_discrete_sequence=[BLUE],
            )
        fig2.update_traces(line_width=2)
        fig2.update_layout(
            margin=dict(t=20, b=40, l=0, r=0),
            height=360,
            yaxis_tickformat=",",
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Row 2: Penetration by LGA + New vs Churned ───────────
    col3, col4 = st.columns(2)

    with col3:
        st.markdown("#### Penetration Rate by State (%)")
        pen = (
            df.groupby("state")["penetration_rate"]
            .mean()
            .reset_index()
            .sort_values("penetration_rate", ascending=True)
        )
        pen["penetration_pct"] = (pen["penetration_rate"] * 100).round(1)
        colors = [RED if v < 45 else BLUE for v in pen["penetration_pct"]]
        fig3 = px.bar(
            pen,
            x="penetration_pct",
            y="state",
            orientation="h",
            color="penetration_pct",
            color_continuous_scale="Blues",
            labels={"penetration_pct": "Penetration %", "state": ""},
            text="penetration_pct",
        )
        fig3.update_traces(
            texttemplate="%{text:.1f}%", textposition="outside", textfont_size=9)
        fig3.add_vline(x=45, line_dash="dash", line_color=AMBER,
                       annotation_text="45% whitespace threshold")
        fig3.update_layout(
            coloraxis_showscale=False,
            margin=dict(t=20, b=20, l=0, r=0),
            height=360,
        )
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.markdown("#### New Activations vs Churned by State")
        net = (
            df.groupby("state")
            .agg(new_subs=("new_subs", "sum"),
                 churned_subs=("churned_subs", "sum"))
            .reset_index()
            .sort_values("new_subs", ascending=True)
        )
        fig4 = go.Figure()
        fig4.add_trace(go.Bar(
            name="New Activations",
            x=net["new_subs"],
            y=net["state"],
            orientation="h",
            marker_color=GREEN,
        ))
        fig4.add_trace(go.Bar(
            name="Churned",
            x=net["churned_subs"],
            y=net["state"],
            orientation="h",
            marker_color=RED,
            opacity=0.75,
        ))
        fig4.update_layout(
            barmode="overlay",
            margin=dict(t=20, b=20, l=0, r=0),
            height=360,
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            xaxis_title="Subscribers",
        )
        st.plotly_chart(fig4, use_container_width=True)

    # ── Row 3: Churn risk table ───────────────────────────────
    st.markdown("---")
    st.markdown("#### ⚠️ Churn Risk Flag Table")
    st.caption(
        "LGAs showing simultaneous subscriber decline AND ARPU erosion "
        "over the past 7 days. Retention action required within 48 hours."
    )

    churn = metrics.churn_risk_lgas(df)
    if churn.empty:
        st.success(
            "✅ No active churn risk signals in the current filter. "
            "All LGAs show stable or improving subscriber and ARPU trends."
        )
    else:
        display = churn[[
            "state", "lga", "active_subs",
            "subs_7d_change_pct", "arpu_7d_change_pct", "avg_mos_score"
        ]].rename(columns={
            "state":              "State",
            "lga":                "LGA",
            "active_subs":        "Active Subs",
            "subs_7d_change_pct": "Subs 7d Δ%",
            "arpu_7d_change_pct": "ARPU 7d Δ%",
            "avg_mos_score":      "MOS Score",
        })
        st.dataframe(
            display.style.background_gradient(
                subset=["Subs 7d Δ%", "ARPU 7d Δ%"], cmap="RdYlGn"
            ),
            use_container_width=True,
            hide_index=True,
        )

    # ── Row 4: Penetration scatter ───────────────────────────
    st.markdown("---")
    st.markdown("#### Population vs Penetration Rate (LGA Level)")
    st.caption(
        "Bubble size = active subscribers. "
        "LGAs bottom-left are large, underserved markets."
    )

    latest = df[df["date"] == df["date"].max()].drop_duplicates(
        subset=["state", "lga"])
    latest = latest.copy()
    latest["penetration_pct"] = (latest["penetration_rate"] * 100).round(1)

    fig5 = px.scatter(
        latest,
        x="lga_population",
        y="penetration_pct",
        size="active_subs",
        color="state",
        hover_name="lga",
        hover_data={
            "lga_population": ":,",
            "penetration_pct": ":.1f",
            "active_subs": ":,",
        },
        labels={
            "lga_population":  "LGA Population",
            "penetration_pct": "Penetration Rate (%)",
        },
        size_max=40,
        opacity=0.75,
    )
    fig5.add_hline(y=45, line_dash="dash", line_color=AMBER,
                   annotation_text="45% whitespace threshold")
    fig5.update_layout(
        margin=dict(t=20, b=40, l=0, r=0),
        height=400,
    )
    st.plotly_chart(fig5, use_container_width=True)

    # ── Footer ───────────────────────────────────────────────
    st.markdown("---")
    st.caption(
        "Churn risk flag: subs_7d_change < -1% AND arpu_7d_change < -1%  "
        "| Whitespace threshold: population > 300,000 & penetration < 45%"
    )