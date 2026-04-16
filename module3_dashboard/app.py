# ============================================================
# NigeriaRGI  |  Module 3  |  app.py
# Streamlit entry point — sidebar, shared filters, page routing
# Run locally:  streamlit run module3_dashboard/app.py
# ============================================================

import streamlit as st
from utils.data_loader import get_data, get_filter_options, apply_filters

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="NigeriaRGI — Regional Growth Intelligence",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────
st.markdown("""
<style>
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0A1628;
    }
    [data-testid="stSidebar"] * {
        color: #E8EDF5 !important;
    }
    /* KPI cards */
    [data-testid="metric-container"] {
        background-color: #F0F4FA;
        border: 1px solid #D0DCF0;
        border-radius: 8px;
        padding: 12px 16px;
    }
    /* Page header */
    .page-header {
        background: linear-gradient(90deg, #0057A8 0%, #0A1628 100%);
        color: white;
        padding: 16px 24px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    /* Warning banner */
    .warn-banner {
        background-color: #FFF3CD;
        border-left: 4px solid #D62728;
        padding: 10px 16px;
        border-radius: 4px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ── Load data ────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def load():
    return get_data()

df_full = load()
options = get_filter_options(df_full)

# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📡 NigeriaRGI")
    st.markdown("**Regional Growth Intelligence**")
    st.markdown("---")

    st.markdown("### 🗺️ Region Filter")
    selected_states = st.multiselect(
        "Select States",
        options=options["states"],
        default=options["states"],
        help="Filter all pages by state"
    )

    st.markdown("### 📅 Date Range")
    min_date, max_date = options["dates"]
    date_range = st.date_input(
        "Select Period",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        help="Filter all pages by date range"
    )

    st.markdown("---")
    st.markdown("### 📄 Navigate")
    page = st.radio(
        "Select Page",
        options=[
            "🏠 Regional Command Centre",
            "💰 Revenue & ARPU Deep Dive",
            "👥 Subscriber Health & Churn Risk",
            "📶 Network Quality & QoE",
            "🚀 Growth Opportunity & GTM",
        ],
        index=0,
    )

    st.markdown("---")
    st.caption("NigeriaRGI · Fidelis Akinbule · Lagos")
    st.caption(f"Data: {min_date.strftime('%d %b %Y')} → {max_date.strftime('%d %b %Y')}")
    st.caption(f"{len(df_full):,} records loaded")

# ── Apply shared filters ─────────────────────────────────────
if isinstance(date_range, tuple) and len(date_range) == 2:
    dr = date_range
else:
    dr = (min_date, max_date)

df = apply_filters(df_full, selected_states, dr)

if df.empty:
    st.warning("No data matches the current filters. Adjust the state or date selection.")
    st.stop()

# ── Store filtered df in session state for pages ─────────────
st.session_state["df"] = df
st.session_state["df_full"] = df_full

# ── Page routing ─────────────────────────────────────────────
if page == "🏠 Regional Command Centre":
    from pages import page1_command_centre
    page1_command_centre.render(df)

elif page == "💰 Revenue & ARPU Deep Dive":
    from pages import page2_revenue
    page2_revenue.render(df)

elif page == "👥 Subscriber Health & Churn Risk":
    from pages import page3_subscribers
    page3_subscribers.render(df)

elif page == "📶 Network Quality & QoE":
    from pages import page4_qoe
    page4_qoe.render(df)

elif page == "🚀 Growth Opportunity & GTM":
    from pages import page5_gtm
    page5_gtm.render(df)