# ============================================================
# NigeriaRGI  |  Module 3  |  utils/data_loader.py
# Detects runtime environment and loads master_table from
# the appropriate source:
#   Local dev  → data/processed/nigeria_rgi.db  (SQLite)
#   Streamlit Cloud → data/processed/master_table.csv
# All dashboard pages import get_data() from this module.
# ============================================================

import os
import sqlite3
import pandas as pd
import streamlit as st

# ── Paths ────────────────────────────────────────────────────
_DB_PATH  = "data/processed/nigeria_rgi.db"
_CSV_PATH = "data/processed/master_table.csv"


def _load_from_db() -> pd.DataFrame:
    conn = sqlite3.connect(_DB_PATH)
    df = pd.read_sql("SELECT * FROM master_table", conn)
    conn.close()
    return df


def _load_from_csv() -> pd.DataFrame:
    return pd.read_csv(_CSV_PATH)


def _detect_environment() -> str:
    """
    Returns 'cloud' if running on Streamlit Cloud, 'local' otherwise.
    Streamlit Cloud sets the STREAMLIT_SHARING_MODE env variable.
    CSV is also used as fallback if the .db file is absent.
    """
    if os.environ.get("STREAMLIT_SHARING_MODE"):
        return "cloud"
    if not os.path.exists(_DB_PATH):
        return "cloud"
    return "local"


@st.cache_data(ttl=3600)
def get_data() -> pd.DataFrame:
    """
    Primary data access function for all dashboard pages.
    Returns the full master_table as a cleaned DataFrame.
    Cached for 1 hour to avoid repeated disk reads.
    """
    env = _detect_environment()

    if env == "cloud":
        df = _load_from_csv()
    else:
        df = _load_from_db()

    # ── Type enforcement ─────────────────────────────────────
    df["date"] = pd.to_datetime(df["date"])

    int_cols = [
        "active_subs", "new_subs", "churned_subs",
        "site_count", "lga_population",
        "poi_markets", "poi_motor_parks", "poi_hospitals",
        "poi_schools", "poi_total",
        "qoe_below_threshold", "churn_risk_flag", "whitespace_flag",
        "urban_flag"
    ]
    for col in int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    float_cols = [
        "arpu_daily_ngn", "arpu_monthly_est", "total_revenue_ngn",
        "data_revenue_ngn", "voice_revenue_ngn", "vas_revenue_ngn",
        "data_usage_gb", "voice_minutes",
        "avg_drop_call_rate", "avg_congestion_pct",
        "avg_download_speed", "avg_upload_speed",
        "avg_mos_score", "avg_call_setup_success",
        "total_data_traffic_tb", "total_voice_erlangs",
        "total_monthly_opex", "daily_revenue_per_site",
        "daily_opex_per_site", "site_profit_proxy",
        "penetration_rate", "income_index", "road_density_km",
        "subs_7d_change", "arpu_7d_change"
    ]
    for col in float_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def get_filter_options(df: pd.DataFrame) -> dict:
    """
    Returns sorted lists of available states and LGAs
    for use in sidebar filter widgets.
    """
    return {
        "states": sorted(df["state"].unique().tolist()),
        "lgas":   sorted(df["lga"].unique().tolist()),
        "dates":  (df["date"].min(), df["date"].max())
    }


def apply_filters(
    df: pd.DataFrame,
    selected_states: list,
    date_range: tuple
) -> pd.DataFrame:
    """
    Applies sidebar state and date filters to the master DataFrame.
    Used by every dashboard page to ensure consistent filtering.
    """
    filtered = df.copy()

    if selected_states:
        filtered = filtered[filtered["state"].isin(selected_states)]

    if date_range and len(date_range) == 2:
        filtered = filtered[
            (filtered["date"] >= pd.Timestamp(date_range[0])) &
            (filtered["date"] <= pd.Timestamp(date_range[1]))
        ]

    return filtered