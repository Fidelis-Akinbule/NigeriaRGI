# ============================================================
# NigeriaRGI  |  Module 3  |  pages/page5_gtm.py
# Page 5: Growth Opportunity & GTM
# Whitespace map, site profitability ranking, POI vs
# penetration scatter, composite GTM opportunity score.
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
        <h2 style="margin:0; color:white;">🚀 Growth Opportunity & GTM</h2>
        <p style="margin:4px 0 0 0; color:#AEC6E8; font-size:0.9rem;">
            Whitespace identification · Site profitability · GTM scoring
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI Row ──────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)

    gtm_df       = metrics.gtm_opportunity_score(df)
    ws_df        = metrics.whitespace_lgas(df)
    site_df      = metrics.site_profitability_by_lga(df)
    n_whitespace = len(ws_df)
    top_gtm_lga  = gtm_df.iloc[0]["lga"] if not gtm_df.empty else "N/A"
    top_gtm_state = gtm_df.iloc[0]["state"] if not gtm_df.empty else "N/A"
    avg_profit   = metrics.avg_site_profit(df)

    k1.metric("Whitespace LGAs",
              str(n_whitespace),
              help="LGAs with population > 300,000 and penetration < 45%")
    k2.metric("Top GTM Target",
              top_gtm_lga,
              delta=top_gtm_state,
              delta_color="off",
              help="LGA with highest composite GTM opportunity score")
    k3.metric("Avg Daily Site Profit",
              f"₦{avg_profit:,.0f}",
              help="Average daily profit per site across filtered LGAs")
    k4.metric("Total LGAs Ranked",
              str(len(gtm_df)),
              help="Total LGAs in the GTM opportunity ranking")

    st.markdown("---")

    # ── Row 1: GTM score ranking + Whitespace table ───────────
    col1, col2 = st.columns([1.4, 1])

    with col1:
        st.markdown("#### 🏆 Top 15 LGAs — Composite GTM Opportunity Score")
        st.caption(
            "Score = whitespace (30%) + income index (25%) + "
            "POI density (20%) + penetration gap (15%) + site profit (10%)"
        )
        top15 = gtm_df.head(15).copy()
        top15["penetration_pct"] = (top15["penetration_rate"] * 100).round(1)
        top15["priority"] = top15["whitespace_flag"].map(
            {1: "🔴 Priority", 0: "🔵 Opportunity"})

        fig = px.bar(
            top15.sort_values("gtm_score"),
            x="gtm_score",
            y="lga",
            orientation="h",
            color="whitespace_flag",
            color_continuous_scale=[[0, BLUE], [1, RED]],
            hover_data={
                "state": True,
                "penetration_pct": True,
                "income_index": True,
                "poi_total": True,
                "whitespace_flag": False,
            },
            labels={"gtm_score": "GTM Score", "lga": ""},
            text="gtm_score",
        )
        fig.update_traces(
            texttemplate="%{text:.3f}", textposition="outside", textfont_size=9)
        fig.update_layout(
            coloraxis_showscale=False,
            margin=dict(t=20, b=20, l=0, r=0),
            height=420,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### 🔴 Whitespace LGAs")
        st.caption("High population, low penetration — unmet demand markets")
        if ws_df.empty:
            st.info("No whitespace LGAs in current filter.")
        else:
            display_ws = ws_df.copy()
            display_ws["penetration_rate"] = (
                display_ws["penetration_rate"] * 100).round(1)
            display_ws = display_ws.rename(columns={
                "state":            "State",
                "lga":              "LGA",
                "lga_population":   "Population",
                "penetration_rate": "Penetration %",
                "income_index":     "Income Index",
                "poi_total":        "POI Total",
            }).drop(columns=["whitespace_flag"], errors="ignore")
            st.dataframe(display_ws, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("#### 📊 GTM Score Components")
        if not gtm_df.empty:
            top1 = gtm_df.iloc[0]
            components = pd.DataFrame({
                "Component": [
                    "Whitespace (30%)",
                    "Income Index (25%)",
                    "POI Density (20%)",
                    "Penetration Gap (15%)",
                    "Site Profit (10%)",
                ],
                "Weight": [0.30, 0.25, 0.20, 0.15, 0.10],
            })
            fig_c = px.bar(
                components,
                x="Weight",
                y="Component",
                orientation="h",
                color="Weight",
                color_continuous_scale="Blues",
                text="Weight",
            )
            fig_c.update_traces(
                texttemplate="%{text:.0%}", textposition="outside", textfont_size=9)
            fig_c.update_layout(
                coloraxis_showscale=False,
                margin=dict(t=10, b=10, l=0, r=0),
                height=220,
                xaxis=dict(tickformat=".0%"),
            )
            st.plotly_chart(fig_c, use_container_width=True)

    # ── Row 2: POI vs Penetration scatter ────────────────────
    st.markdown("---")
    col3, col4 = st.columns(2)

    with col3:
        st.markdown("#### POI Total vs Penetration Rate (LGA Level)")
        st.caption(
            "Bubble size = LGA population. "
            "Bottom-right = high commercial activity, low penetration = "
            "highest distribution opportunity."
        )
        latest = df[df["date"] == df["date"].max()].drop_duplicates(
            subset=["state", "lga"]).copy()
        latest["penetration_pct"] = (latest["penetration_rate"] * 100).round(1)

        fig2 = px.scatter(
            latest,
            x="poi_total",
            y="penetration_pct",
            size="lga_population",
            color="whitespace_flag",
            color_continuous_scale=[[0, BLUE], [1, RED]],
            hover_name="lga",
            hover_data={
                "state": True,
                "lga_population": ":,",
                "income_index": True,
                "whitespace_flag": False,
            },
            labels={
                "poi_total":       "Total POIs",
                "penetration_pct": "Penetration Rate (%)",
            },
            size_max=45,
            opacity=0.75,
        )
        fig2.add_hline(y=45, line_dash="dash", line_color=AMBER,
                       annotation_text="45% whitespace threshold")
        fig2.update_layout(
            coloraxis_showscale=False,
            margin=dict(t=20, b=40, l=0, r=0),
            height=380,
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col4:
        st.markdown("#### Income Index vs Penetration Rate (LGA Level)")
        st.caption(
            "Bottom-right = high income, low penetration = "
            "revenue-rich underserved markets."
        )
        fig3 = px.scatter(
            latest,
            x="income_index",
            y="penetration_pct",
            size="lga_population",
            color="state",
            hover_name="lga",
            hover_data={
                "state": True,
                "lga_population": ":,",
                "poi_total": True,
            },
            labels={
                "income_index":    "Income Index (Lagos=100)",
                "penetration_pct": "Penetration Rate (%)",
            },
            size_max=45,
            opacity=0.75,
        )
        fig3.add_hline(y=45, line_dash="dash", line_color=AMBER,
                       annotation_text="45% whitespace threshold")
        fig3.update_layout(
            margin=dict(t=20, b=40, l=0, r=0),
            height=380,
        )
        st.plotly_chart(fig3, use_container_width=True)

    # ── Row 3: Site profitability ranking ────────────────────
    st.markdown("---")
    st.markdown("#### 🏗️ Site Profitability Ranking — Top & Bottom 10 LGAs")

    col5, col6 = st.columns(2)

    with col5:
        st.markdown("**Top 10 — Highest Daily Profit per Site**")
        top10 = site_df.head(10).copy()
        top10["avg_profit_per_site"] = top10["avg_profit_per_site"].apply(
            lambda x: f"₦{x:,.0f}")
        top10["avg_daily_rev_per_site"] = top10["avg_daily_rev_per_site"].apply(
            lambda x: f"₦{x:,.0f}")
        top10 = top10.rename(columns={
            "state":                 "State",
            "lga":                   "LGA",
            "site_count":            "Sites",
            "avg_daily_rev_per_site":"Daily Rev/Site",
            "avg_profit_per_site":   "Daily Profit/Site",
        })[["State", "LGA", "Sites", "Daily Rev/Site", "Daily Profit/Site"]]
        st.dataframe(top10, use_container_width=True, hide_index=True)

    with col6:
        st.markdown("**Bottom 10 — Lowest Daily Profit per Site**")
        bottom10 = site_df.tail(10).copy()
        bottom10["avg_profit_per_site"] = bottom10["avg_profit_per_site"].apply(
            lambda x: f"₦{x:,.0f}")
        bottom10["avg_daily_rev_per_site"] = bottom10["avg_daily_rev_per_site"].apply(
            lambda x: f"₦{x:,.0f}")
        bottom10 = bottom10.rename(columns={
            "state":                 "State",
            "lga":                   "LGA",
            "site_count":            "Sites",
            "avg_daily_rev_per_site":"Daily Rev/Site",
            "avg_profit_per_site":   "Daily Profit/Site",
        })[["State", "LGA", "Sites", "Daily Rev/Site", "Daily Profit/Site"]]
        st.dataframe(bottom10, use_container_width=True, hide_index=True)

    # ── Row 4: Full GTM table ────────────────────────────────
    st.markdown("---")
    st.markdown("#### 📋 Full GTM Opportunity Table — All LGAs Ranked")
    full = gtm_df.copy()
    full["penetration_rate"] = (full["penetration_rate"] * 100).round(1)
    full["site_profit_proxy"] = full["site_profit_proxy"].apply(
        lambda x: f"₦{x:,.0f}")
    full["whitespace_flag"] = full["whitespace_flag"].map(
        {1: "🔴 Yes", 0: "—"})
    full = full.rename(columns={
        "state":            "State",
        "lga":              "LGA",
        "lga_population":   "Population",
        "penetration_rate": "Penetration %",
        "income_index":     "Income Index",
        "poi_total":        "POI Total",
        "whitespace_flag":  "Whitespace",
        "site_profit_proxy":"Site Profit/Day",
        "gtm_score":        "GTM Score",
    })
    st.dataframe(full, use_container_width=True, hide_index=True)

    # ── Footer ───────────────────────────────────────────────
    st.markdown("---")
    st.caption(
        "GTM Score methodology: whitespace flag (0.30) · "
        "normalised income index (0.25) · normalised POI total (0.20) · "
        "penetration gap 1-rate (0.15) · normalised site profit (0.10)  "
        "| Whitespace: population > 300,000 & penetration < 45%"
    )