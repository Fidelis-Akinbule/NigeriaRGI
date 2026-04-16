# ============================================================
# NigeriaRGI  |  Module 3  |  pages/page1_command_centre.py
# Page 1: Regional Command Centre
# One screen shows region health in 30 seconds:
# KPI cards, revenue/QoE/churn summary, early warning panel.
# ============================================================

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from utils import metrics

# ── Colour constants ─────────────────────────────────────────
BLUE    = "#0057A8"
RED     = "#D62728"
GREEN   = "#2CA02C"
AMBER   = "#F5A623"


def render(df: pd.DataFrame):

    # ── Header ───────────────────────────────────────────────
    st.markdown("""
    <div class="page-header">
        <h2 style="margin:0; color:white;">🏠 Regional Command Centre</h2>
        <p style="margin:4px 0 0 0; color:#AEC6E8; font-size:0.9rem;">
            Region-wide health snapshot · Leadership view
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI Row ──────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)

    total_rev   = metrics.total_revenue_millions(df)
    arpu        = metrics.avg_monthly_arpu(df)
    active_subs = metrics.total_active_subs(df)
    qoe_rate    = metrics.qoe_compliance_rate(df)
    site_profit = metrics.avg_site_profit(df)

    k1.metric("Total Revenue",
              metrics.format_ngn_billions(total_rev),
              help="Sum of all LGA daily revenue across filtered period")
    k2.metric("Avg Monthly ARPU",
              f"₦{arpu:,.0f}",
              help="Average monthly ARPU across all LGAs")
    k3.metric("Active Subscribers",
              f"{active_subs:,}",
              help="Total active subscribers on latest date in filtered period")
    k4.metric("QoE Compliance",
              metrics.format_pct(qoe_rate),
              delta=f"{qoe_rate - 100:.1f}% vs 100% target",
              delta_color="inverse" if qoe_rate < 80 else "normal",
              help="% of LGA-day records meeting NCC MOS and drop call thresholds")
    k5.metric("Avg Daily Site Profit",
              f"₦{site_profit:,.0f}",
              help="Average daily profit per site across filtered LGAs")

    st.markdown("---")

    # ── Row 1: Revenue by state + Revenue trend ───────────────
    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.markdown("#### 💰 Revenue by State (₦ Millions)")
        rev_state = metrics.revenue_by_state(df)
        fig = px.bar(
            rev_state,
            x="state",
            y="total_revenue_ngn_m",
            color="total_revenue_ngn_m",
            color_continuous_scale="Blues",
            labels={"total_revenue_ngn_m": "₦ Millions", "state": "State"},
            text="total_revenue_ngn_m",
        )
        fig.update_traces(texttemplate="₦%{text:,.0f}M", textposition="outside",
                          textfont_size=9)
        fig.update_layout(
            coloraxis_showscale=False,
            margin=dict(t=20, b=40, l=0, r=0),
            height=320,
            xaxis_tickangle=-35,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### 📈 Daily Revenue Trend")
        trend = metrics.revenue_trend(df)
        fig2 = px.line(
            trend,
            x="date",
            y="daily_revenue_ngn",
            labels={"daily_revenue_ngn": "₦ Daily Revenue", "date": ""},
            color_discrete_sequence=[BLUE],
        )
        fig2.update_traces(line_width=2)
        fig2.update_layout(
            margin=dict(t=20, b=40, l=0, r=0),
            height=320,
            yaxis_tickformat="₦,.0f",
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Row 2: QoE compliance + Revenue mix + Penetration ────
    col3, col4, col5 = st.columns(3)

    with col3:
        st.markdown("#### 📶 QoE Compliance by State")
        qoe_state = metrics.qoe_by_state(df)
        fig3 = px.bar(
            qoe_state.sort_values("qoe_breach_pct", ascending=True),
            x="qoe_breach_pct",
            y="state",
            orientation="h",
            color="qoe_breach_pct",
            color_continuous_scale=["#2CA02C", "#F5A623", "#D62728"],
            labels={"qoe_breach_pct": "Breach %", "state": ""},
        )
        fig3.add_vline(x=40, line_dash="dash", line_color=RED,
                       annotation_text="40% alert")
        fig3.update_layout(
            coloraxis_showscale=False,
            margin=dict(t=20, b=20, l=0, r=0),
            height=300,
        )
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.markdown("#### 🥧 Revenue Mix")
        mix = metrics.revenue_mix(df)
        fig4 = go.Figure(go.Pie(
            labels=["Data", "Voice", "VAS"],
            values=[mix["data"], mix["voice"], mix["vas"]],
            hole=0.55,
            marker_colors=[BLUE, "#5BA3D9", "#AED6F1"],
            textinfo="label+percent",
            textfont_size=12,
        ))
        fig4.update_layout(
            margin=dict(t=20, b=20, l=0, r=0),
            height=300,
            showlegend=False,
        )
        st.plotly_chart(fig4, use_container_width=True)

    with col5:
        st.markdown("#### 👥 Avg Penetration by State")
        pen = (
            df.groupby("state")["penetration_rate"]
            .mean()
            .reset_index()
            .sort_values("penetration_rate", ascending=True)
        )
        pen["penetration_pct"] = (pen["penetration_rate"] * 100).round(1)
        fig5 = px.bar(
            pen,
            x="penetration_pct",
            y="state",
            orientation="h",
            color="penetration_pct",
            color_continuous_scale="Blues",
            labels={"penetration_pct": "Penetration %", "state": ""},
        )
        fig5.add_vline(x=45, line_dash="dash", line_color=AMBER,
                       annotation_text="45% whitespace")
        fig5.update_layout(
            coloraxis_showscale=False,
            margin=dict(t=20, b=20, l=0, r=0),
            height=300,
        )
        st.plotly_chart(fig5, use_container_width=True)

    # ── Row 3: Early Warning Panel ───────────────────────────
    st.markdown("---")
    st.markdown("#### ⚠️ Early Warning Panel")

    w1, w2, w3 = st.columns(3)

    with w1:
        st.markdown("**🔴 High QoE Breach States (>80%)**")
        high_breach = metrics.qoe_by_state(df)
        high_breach = high_breach[high_breach["qoe_breach_pct"] > 80][
            ["state", "qoe_breach_pct", "avg_mos", "avg_drop_call_rate"]
        ].rename(columns={
            "qoe_breach_pct": "Breach %",
            "avg_mos": "MOS",
            "avg_drop_call_rate": "Drop Call %"
        })
        if high_breach.empty:
            st.success("No states above 80% breach threshold.")
        else:
            st.dataframe(high_breach, use_container_width=True, hide_index=True)

    with w2:
        st.markdown("**🟡 Whitespace Opportunity LGAs**")
        ws = metrics.whitespace_lgas(df)[
            ["state", "lga", "lga_population", "penetration_rate"]
        ].copy()
        ws["penetration_rate"] = (ws["penetration_rate"] * 100).round(1)
        ws = ws.rename(columns={
            "lga_population": "Population",
            "penetration_rate": "Penetration %"
        })
        if ws.empty:
            st.info("No whitespace LGAs in current filter.")
        else:
            st.dataframe(ws, use_container_width=True, hide_index=True)

    with w3:
        st.markdown("**🟠 Churn Risk LGAs**")
        churn = metrics.churn_risk_lgas(df)
        if churn.empty:
            st.success("No active churn risk signals in current filter.")
        else:
            display = churn[[
                "state", "lga", "subs_7d_change_pct", "arpu_7d_change_pct"
            ]].rename(columns={
                "subs_7d_change_pct": "Subs 7d %",
                "arpu_7d_change_pct": "ARPU 7d %"
            })
            st.dataframe(display, use_container_width=True, hide_index=True)

    # ── Footer note ──────────────────────────────────────────
    st.markdown("---")
    n_states = df["state"].nunique()
    n_lgas   = df["lga"].nunique()
    n_days   = df["date"].nunique()
    st.caption(
        f"Showing {n_states} states · {n_lgas} LGAs · {n_days} days  "
        f"| NCC thresholds: MOS ≥ 3.5, Drop Call ≤ 2%  "
        f"| Whitespace: population > 300,000 & penetration < 45%"
    )