# ============================================================
# NigeriaRGI  |  Module 3  |  pages/page4_qoe.py
# Page 4: Network Quality & QoE
# Connects commercial outcomes (churn, ARPU) to network root
# causes. Drop call rate vs NCC threshold, MOS distribution,
# congestion heatmap.
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
        <h2 style="margin:0; color:white;">📶 Network Quality & QoE</h2>
        <p style="margin:4px 0 0 0; color:#AEC6E8; font-size:0.9rem;">
            NCC compliance · MOS scores · Drop call rates · Congestion
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI Row ──────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)

    qoe_rate   = metrics.qoe_compliance_rate(df)
    mos        = metrics.avg_mos(df)
    drop_call  = metrics.avg_drop_call_rate(df)
    dl_speed   = metrics.avg_download_speed(df)

    k1.metric("QoE Compliance Rate",
              metrics.format_pct(qoe_rate),
              delta=f"{qoe_rate - 100:.1f}% vs 100% target",
              delta_color="inverse" if qoe_rate < 80 else "normal",
              help="% of LGA-day records meeting NCC thresholds")
    k2.metric("Avg MOS Score",
              f"{mos:.2f}",
              delta=f"{mos - 3.5:+.2f} vs NCC threshold (3.5)",
              delta_color="normal" if mos >= 3.5 else "inverse",
              help="Mean Opinion Score. NCC minimum: 3.5")
    k3.metric("Avg Drop Call Rate",
              f"{drop_call:.2f}%",
              delta=f"{drop_call - 2.0:+.2f}% vs NCC threshold (2%)",
              delta_color="inverse" if drop_call > 2.0 else "normal",
              help="Average drop call rate. NCC maximum: 2%")
    k4.metric("Avg Download Speed",
              f"{dl_speed:.1f} Mbps",
              help="Average download speed across filtered LGAs")

    st.markdown("---")

    # ── Row 1: QoE breach by state + MOS by state ────────────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### QoE Breach Rate by State (%)")
        st.caption("% of days where MOS < 3.5 OR drop call rate > 2%")
        qoe_s = metrics.qoe_by_state(df).sort_values(
            "qoe_breach_pct", ascending=True)
        colors = [RED if v > 80 else AMBER if v > 40 else GREEN
                  for v in qoe_s["qoe_breach_pct"]]
        fig = px.bar(
            qoe_s,
            x="qoe_breach_pct",
            y="state",
            orientation="h",
            color="qoe_breach_pct",
            color_continuous_scale=["#2CA02C", "#F5A623", "#D62728"],
            labels={"qoe_breach_pct": "Breach %", "state": ""},
            text="qoe_breach_pct",
        )
        fig.update_traces(
            texttemplate="%{text:.1f}%", textposition="outside", textfont_size=9)
        fig.add_vline(x=40, line_dash="dash", line_color=AMBER,
                      annotation_text="40% alert")
        fig.add_vline(x=80, line_dash="dash", line_color=RED,
                      annotation_text="80% critical")
        fig.update_layout(
            coloraxis_showscale=False,
            margin=dict(t=20, b=20, l=0, r=0),
            height=360,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Average MOS Score by State")
        st.caption("NCC minimum threshold: 3.5")
        qoe_s2 = metrics.qoe_by_state(df).sort_values("avg_mos")
        fig2 = px.bar(
            qoe_s2,
            x="avg_mos",
            y="state",
            orientation="h",
            color="avg_mos",
            color_continuous_scale=["#D62728", "#F5A623", "#2CA02C"],
            range_color=[2.5, 5.0],
            labels={"avg_mos": "MOS Score", "state": ""},
            text="avg_mos",
        )
        fig2.update_traces(
            texttemplate="%{text:.2f}", textposition="outside", textfont_size=9)
        fig2.add_vline(x=3.5, line_dash="dash", line_color=RED,
                       annotation_text="NCC min (3.5)")
        fig2.update_layout(
            coloraxis_showscale=False,
            margin=dict(t=20, b=20, l=0, r=0),
            height=360,
            xaxis_range=[2.0, 5.5],
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Row 2: Drop call rate by state + Download speed ──────
    col3, col4 = st.columns(2)

    with col3:
        st.markdown("#### Drop Call Rate by State (%)")
        st.caption("NCC maximum threshold: 2.0%")
        qoe_s3 = metrics.qoe_by_state(df).sort_values(
            "avg_drop_call_rate", ascending=False)
        fig3 = px.bar(
            qoe_s3,
            x="state",
            y="avg_drop_call_rate",
            color="avg_drop_call_rate",
            color_continuous_scale=["#2CA02C", "#F5A623", "#D62728"],
            labels={"avg_drop_call_rate": "Drop Call Rate (%)", "state": "State"},
            text="avg_drop_call_rate",
        )
        fig3.update_traces(
            texttemplate="%{text:.2f}%", textposition="outside", textfont_size=9)
        fig3.add_hline(y=2.0, line_dash="dash", line_color=RED,
                       annotation_text="NCC threshold 2%")
        fig3.update_layout(
            coloraxis_showscale=False,
            margin=dict(t=20, b=60, l=0, r=0),
            height=360,
            xaxis_tickangle=-35,
        )
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.markdown("#### Avg Download Speed by State (Mbps)")
        st.caption("Urban benchmark: 13–28 Mbps · Rural benchmark: 4–12 Mbps")
        qoe_s4 = metrics.qoe_by_state(df).sort_values(
            "avg_download_speed", ascending=True)
        fig4 = px.bar(
            qoe_s4,
            x="avg_download_speed",
            y="state",
            orientation="h",
            color="avg_download_speed",
            color_continuous_scale="Blues",
            labels={"avg_download_speed": "Download Speed (Mbps)", "state": ""},
            text="avg_download_speed",
        )
        fig4.update_traces(
            texttemplate="%{text:.1f}", textposition="outside", textfont_size=9)
        fig4.add_vline(x=13, line_dash="dash", line_color=AMBER,
                       annotation_text="Urban floor 13 Mbps")
        fig4.update_layout(
            coloraxis_showscale=False,
            margin=dict(t=20, b=20, l=0, r=0),
            height=360,
        )
        st.plotly_chart(fig4, use_container_width=True)

    # ── Row 3: MOS trend + MOS distribution ──────────────────
    st.markdown("---")
    col5, col6 = st.columns(2)

    with col5:
        st.markdown("#### MOS Score Trend Over Time")
        qoe_trend = metrics.qoe_trend(df)
        selected = df["state"].unique().tolist()
        if len(selected) <= 4:
            trend_state = (
                df.groupby(["date", "state"])["avg_mos_score"]
                .mean()
                .reset_index()
            )
            fig5 = px.line(
                trend_state,
                x="date",
                y="avg_mos_score",
                color="state",
                labels={"avg_mos_score": "MOS Score", "date": ""},
            )
        else:
            fig5 = px.line(
                qoe_trend,
                x="date",
                y="avg_mos_score",
                labels={"avg_mos_score": "MOS Score", "date": ""},
                color_discrete_sequence=[BLUE],
            )
        fig5.add_hline(y=3.5, line_dash="dash", line_color=RED,
                       annotation_text="NCC min (3.5)")
        fig5.update_traces(line_width=2)
        fig5.update_layout(
            margin=dict(t=20, b=40, l=0, r=0),
            height=320,
            yaxis_range=[2.0, 5.0],
        )
        st.plotly_chart(fig5, use_container_width=True)

    with col6:
        st.markdown("#### MOS Score Distribution Across LGAs")
        fig6 = px.histogram(
            df,
            x="avg_mos_score",
            nbins=30,
            color_discrete_sequence=[BLUE],
            labels={"avg_mos_score": "MOS Score"},
        )
        fig6.add_vline(x=3.5, line_dash="dash", line_color=RED,
                       annotation_text="NCC threshold")
        fig6.update_layout(
            margin=dict(t=20, b=40, l=0, r=0),
            height=320,
            yaxis_title="Count",
        )
        st.plotly_chart(fig6, use_container_width=True)

    # ── Row 4: QoE vs ARPU scatter ───────────────────────────
    st.markdown("---")
    st.markdown("#### MOS Score vs Monthly ARPU — Network Quality → Revenue Link")
    st.caption(
        "Each point is one LGA on one day. "
        "The positive correlation shows that better network quality "
        "drives higher ARPU — the commercial case for network investment."
    )

    sample = df.sample(min(2000, len(df)), random_state=42)
    fig7 = px.scatter(
        sample,
        x="avg_mos_score",
        y="arpu_monthly_est",
        color="state",
        opacity=0.5,
        hover_name="lga",
        labels={
            "avg_mos_score":    "MOS Score",
            "arpu_monthly_est": "Monthly ARPU (₦)",
        },
        trendline="ols",
        trendline_scope="overall",
        trendline_color_override=RED,
    )
    fig7.add_vline(x=3.5, line_dash="dash", line_color=RED,
                   annotation_text="NCC threshold")
    fig7.update_layout(
        margin=dict(t=20, b=40, l=0, r=0),
        height=400,
    )
    st.plotly_chart(fig7, use_container_width=True)

    # ── Footer ───────────────────────────────────────────────
    st.markdown("---")
    st.caption(
        "NCC QoE thresholds: MOS ≥ 3.5 · Drop Call Rate ≤ 2% · "
        "Download Speed urban ≥ 13 Mbps · Source: NCC QoS Report 2024"
    )