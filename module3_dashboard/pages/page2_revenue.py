# ============================================================
# NigeriaRGI  |  Module 3  |  pages/page2_revenue.py
# Page 2: Revenue & ARPU Deep Dive
# State/LGA revenue drill-down, ARPU trends, revenue mix.
# ============================================================

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from utils import metrics

BLUE  = "#0057A8"
RED   = "#D62728"
AMBER = "#F5A623"


def render(df: pd.DataFrame):

    # ── Header ───────────────────────────────────────────────
    st.markdown("""
    <div class="page-header">
        <h2 style="margin:0; color:white;">💰 Revenue & ARPU Deep Dive</h2>
        <p style="margin:4px 0 0 0; color:#AEC6E8; font-size:0.9rem;">
            State and LGA revenue breakdown · ARPU trends · Revenue mix
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI Row ──────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)

    total_rev  = metrics.total_revenue_millions(df)
    arpu       = metrics.avg_monthly_arpu(df)
    mix        = metrics.revenue_mix(df)

    k1.metric("Total Revenue",
              metrics.format_ngn_billions(total_rev),
              help="Total revenue across filtered states and period")
    k2.metric("Avg Monthly ARPU",
              f"₦{arpu:,.0f}",
              help="Average monthly ARPU across all LGAs in filter")
    k3.metric("Data Revenue Share",
              f"{mix['data']}%",
              help="Data as % of total revenue")
    k4.metric("VAS Revenue Share",
              f"{mix['vas']}%",
              delta="Target: >15%",
              delta_color="inverse" if mix["vas"] < 15 else "normal",
              help="VAS as % of total revenue. Below 15% = monetisation gap.")

    st.markdown("---")

    # ── Row 1: Stacked revenue by state + ARPU by state ──────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Revenue Split by State (₦ Millions)")
        rev = metrics.revenue_by_state(df)
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Data", x=rev["state"], y=rev["data_revenue_ngn_m"],
            marker_color=BLUE))
        fig.add_trace(go.Bar(
            name="Voice", x=rev["state"], y=rev["voice_revenue_ngn_m"],
            marker_color="#5BA3D9"))
        fig.add_trace(go.Bar(
            name="VAS", x=rev["state"], y=rev["vas_revenue_ngn_m"],
            marker_color="#AED6F1"))
        fig.update_layout(
            barmode="stack",
            margin=dict(t=20, b=60, l=0, r=0),
            height=360,
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            xaxis_tickangle=-35,
            yaxis_title="₦ Millions",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Average Monthly ARPU by State (₦)")
        rev2 = metrics.revenue_by_state(df)
        fig2 = px.bar(
            rev2.sort_values("avg_arpu"),
            x="avg_arpu",
            y="state",
            orientation="h",
            color="avg_arpu",
            color_continuous_scale="Blues",
            labels={"avg_arpu": "Avg Monthly ARPU (₦)", "state": ""},
            text="avg_arpu",
        )
        fig2.update_traces(texttemplate="₦%{text:,.0f}", textposition="outside",
                           textfont_size=9)
        fig2.add_vline(x=3200, line_dash="dash", line_color=RED,
                       annotation_text="Rural floor ₦3,200")
        fig2.add_vline(x=5500, line_dash="dash", line_color=BLUE,
                       annotation_text="Urban ceiling ₦5,500")
        fig2.update_layout(
            coloraxis_showscale=False,
            margin=dict(t=20, b=20, l=0, r=0),
            height=360,
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Row 2: Daily revenue trend + Revenue mix donut ───────
    col3, col4 = st.columns([1.5, 1])

    with col3:
        st.markdown("#### Daily Revenue Trend (₦)")
        trend = metrics.revenue_trend(df)

        # Optional: split by state if ≤ 4 states selected
        selected = df["state"].unique().tolist()
        if len(selected) <= 4:
            trend_state = (
                df.groupby(["date", "state"])["total_revenue_ngn"]
                .sum()
                .reset_index()
            )
            fig3 = px.line(
                trend_state,
                x="date",
                y="total_revenue_ngn",
                color="state",
                labels={"total_revenue_ngn": "₦ Daily Revenue", "date": ""},
            )
        else:
            fig3 = px.line(
                trend,
                x="date",
                y="daily_revenue_ngn",
                labels={"daily_revenue_ngn": "₦ Daily Revenue", "date": ""},
                color_discrete_sequence=[BLUE],
            )

        fig3.update_traces(line_width=2)
        fig3.update_layout(
            margin=dict(t=20, b=40, l=0, r=0),
            height=340,
            yaxis_tickformat="₦,.0f",
        )
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.markdown("#### Revenue Mix")
        mix2 = metrics.revenue_mix(df)
        fig4 = go.Figure(go.Pie(
            labels=["Data", "Voice", "VAS"],
            values=[mix2["data"], mix2["voice"], mix2["vas"]],
            hole=0.6,
            marker_colors=[BLUE, "#5BA3D9", "#AED6F1"],
            textinfo="label+percent",
            textfont_size=13,
        ))
        fig4.add_annotation(
            text=f"VAS<br>{mix2['vas']}%",
            x=0.5, y=0.5,
            font_size=14,
            showarrow=False
        )
        fig4.update_layout(
            margin=dict(t=20, b=20, l=0, r=0),
            height=340,
            showlegend=False,
        )
        st.plotly_chart(fig4, use_container_width=True)

    # ── Row 3: Top LGA table ─────────────────────────────────
    st.markdown("---")
    st.markdown("#### 🏆 Top 15 LGAs by Revenue")

    lga_rev = metrics.revenue_by_lga(df).head(15).copy()
    lga_rev["avg_arpu"]        = lga_rev["avg_arpu"].apply(lambda x: f"₦{x:,.0f}")
    lga_rev["avg_penetration"] = (lga_rev["avg_penetration"] * 100).round(1)
    lga_rev = lga_rev.rename(columns={
        "state":               "State",
        "lga":                 "LGA",
        "total_revenue_ngn_m": "Revenue (₦M)",
        "avg_arpu":            "Avg ARPU",
        "avg_penetration":     "Penetration %",
    })
    st.dataframe(lga_rev, use_container_width=True, hide_index=True)

    # ── Row 4: ARPU distribution ─────────────────────────────
    st.markdown("---")
    col5, col6 = st.columns(2)

    with col5:
        st.markdown("#### ARPU Distribution Across LGAs")
        latest = df[df["date"] == df["date"].max()]
        fig5 = px.histogram(
            latest,
            x="arpu_monthly_est",
            nbins=30,
            color_discrete_sequence=[BLUE],
            labels={"arpu_monthly_est": "Monthly ARPU (₦)"},
        )
        fig5.add_vline(x=3200, line_dash="dash", line_color=RED,
                       annotation_text="Rural floor")
        fig5.add_vline(x=5500, line_dash="dash", line_color=BLUE,
                       annotation_text="Urban ceiling")
        fig5.update_layout(
            margin=dict(t=20, b=40, l=0, r=0),
            height=300,
            yaxis_title="Number of LGAs",
        )
        st.plotly_chart(fig5, use_container_width=True)

    with col6:
        st.markdown("#### VAS Revenue Share by State (%)")
        rev3 = metrics.revenue_by_state(df).copy()
        rev3["vas_share_pct"] = (
            rev3["vas_revenue_ngn_m"] / rev3["total_revenue_ngn_m"] * 100
        ).round(1)
        fig6 = px.bar(
            rev3.sort_values("vas_share_pct"),
            x="vas_share_pct",
            y="state",
            orientation="h",
            color="vas_share_pct",
            color_continuous_scale=["#D62728", "#F5A623", "#2CA02C"],
            labels={"vas_share_pct": "VAS Share (%)", "state": ""},
            text="vas_share_pct",
        )
        fig6.update_traces(texttemplate="%{text:.1f}%", textposition="outside",
                           textfont_size=9)
        fig6.add_vline(x=15, line_dash="dash", line_color=BLUE,
                       annotation_text="15% target")
        fig6.update_layout(
            coloraxis_showscale=False,
            margin=dict(t=20, b=20, l=0, r=0),
            height=300,
        )
        st.plotly_chart(fig6, use_container_width=True)

    # ── Footer ───────────────────────────────────────────────
    st.markdown("---")
    st.caption(
        "ARPU benchmarks: Urban ₦3,600–₦5,500 · Rural ₦2,200–₦3,200 "
        "(NCC 2025, post-tariff hike)  |  VAS target: >15% of total revenue"
    )