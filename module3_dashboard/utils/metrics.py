# ============================================================
# NigeriaRGI  |  Module 3  |  utils/metrics.py
# All computed measures for the dashboard.
# This is the DAX equivalent — single source of truth for
# every derived metric used across all 5 dashboard pages.
# ============================================================

import pandas as pd
import numpy as np


# ── NCC Thresholds ───────────────────────────────────────────
NCC_MOS_THRESHOLD         = 3.5
NCC_DROP_CALL_THRESHOLD   = 0.02   # 2%
WHITESPACE_PENETRATION    = 0.45   # 45%
WHITESPACE_POPULATION     = 300_000
CHURN_RISK_SUBS_CHANGE    = -0.01  # -1% 7d change
CHURN_RISK_ARPU_CHANGE    = -0.01  # -1% 7d change


# ── Revenue Metrics ──────────────────────────────────────────
def total_revenue(df: pd.DataFrame) -> float:
    """Total revenue in NGN across filtered dataset."""
    return df["total_revenue_ngn"].sum()


def total_revenue_millions(df: pd.DataFrame) -> float:
    """Total revenue in NGN millions."""
    return round(total_revenue(df) / 1_000_000, 2)


def avg_monthly_arpu(df: pd.DataFrame) -> float:
    """Average monthly ARPU across filtered dataset."""
    return round(df["arpu_monthly_est"].mean(), 0)


def revenue_by_state(df: pd.DataFrame) -> pd.DataFrame:
    """Total and split revenue aggregated by state."""
    return (
        df.groupby("state")
        .agg(
            total_revenue_ngn_m=("total_revenue_ngn",
                                  lambda x: round(x.sum() / 1e6, 2)),
            data_revenue_ngn_m=("data_revenue_ngn",
                                 lambda x: round(x.sum() / 1e6, 2)),
            voice_revenue_ngn_m=("voice_revenue_ngn",
                                  lambda x: round(x.sum() / 1e6, 2)),
            vas_revenue_ngn_m=("vas_revenue_ngn",
                                lambda x: round(x.sum() / 1e6, 2)),
            avg_arpu=("arpu_monthly_est", "mean"),
        )
        .reset_index()
        .sort_values("total_revenue_ngn_m", ascending=False)
    )


def revenue_by_lga(df: pd.DataFrame) -> pd.DataFrame:
    """Total revenue aggregated by LGA."""
    return (
        df.groupby(["state", "lga"])
        .agg(
            total_revenue_ngn_m=("total_revenue_ngn",
                                  lambda x: round(x.sum() / 1e6, 2)),
            avg_arpu=("arpu_monthly_est", "mean"),
            avg_penetration=("penetration_rate", "mean"),
        )
        .reset_index()
        .sort_values("total_revenue_ngn_m", ascending=False)
    )


def revenue_mix(df: pd.DataFrame) -> dict:
    """Revenue split percentages: data / voice / VAS."""
    total = df["total_revenue_ngn"].sum()
    if total == 0:
        return {"data": 0, "voice": 0, "vas": 0}
    return {
        "data":  round(df["data_revenue_ngn"].sum()  / total * 100, 1),
        "voice": round(df["voice_revenue_ngn"].sum() / total * 100, 1),
        "vas":   round(df["vas_revenue_ngn"].sum()   / total * 100, 1),
    }


def revenue_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Daily total revenue trend for line chart."""
    return (
        df.groupby("date")["total_revenue_ngn"]
        .sum()
        .reset_index()
        .rename(columns={"total_revenue_ngn": "daily_revenue_ngn"})
        .sort_values("date")
    )


# ── Subscriber Metrics ───────────────────────────────────────
def total_active_subs(df: pd.DataFrame) -> int:
    """Total active subscribers (latest date in filtered data)."""
    latest = df[df["date"] == df["date"].max()]
    return int(latest["active_subs"].sum())


def total_churned_subs(df: pd.DataFrame) -> int:
    """Total churned subscribers across filtered period."""
    return int(df["churned_subs"].sum())


def avg_penetration_rate(df: pd.DataFrame) -> float:
    """Average penetration rate across filtered dataset."""
    return round(df["penetration_rate"].mean() * 100, 1)


def subscriber_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Daily active subscriber trend."""
    return (
        df.groupby("date")["active_subs"]
        .sum()
        .reset_index()
        .sort_values("date")
    )


def churn_risk_lgas(df: pd.DataFrame) -> pd.DataFrame:
    """
    LGAs currently showing churn risk signals.
    Returns latest snapshot per LGA with risk metrics.
    """
    latest = df[df["date"] == df["date"].max()].copy()
    risk = latest[
        (latest["subs_7d_change"] < CHURN_RISK_SUBS_CHANGE) &
        (latest["arpu_7d_change"] < CHURN_RISK_ARPU_CHANGE)
    ][["state", "lga", "active_subs", "subs_7d_change",
       "arpu_7d_change", "avg_mos_score", "churn_risk_flag"]].copy()

    risk["subs_7d_change_pct"]  = round(risk["subs_7d_change"] * 100, 2)
    risk["arpu_7d_change_pct"]  = round(risk["arpu_7d_change"] * 100, 2)
    return risk.sort_values("subs_7d_change_pct")


def penetration_by_lga(df: pd.DataFrame) -> pd.DataFrame:
    """Average penetration rate per LGA."""
    return (
        df.groupby(["state", "lga"])
        .agg(
            avg_penetration=("penetration_rate", "mean"),
            lga_population=("lga_population", "first"),
            income_index=("income_index", "first"),
            urban_flag=("urban_flag", "first"),
        )
        .reset_index()
        .sort_values("avg_penetration")
    )


# ── QoE & Network Metrics ────────────────────────────────────
def qoe_compliance_rate(df: pd.DataFrame) -> float:
    """
    Percentage of LGA-day records meeting BOTH NCC thresholds:
    MOS >= 3.5 AND drop call rate <= 2%.
    """
    total = len(df)
    if total == 0:
        return 0.0
    compliant = df[df["qoe_below_threshold"] == 0].shape[0]
    return round(compliant / total * 100, 1)


def avg_mos(df: pd.DataFrame) -> float:
    return round(df["avg_mos_score"].mean(), 2)


def avg_drop_call_rate(df: pd.DataFrame) -> float:
    return round(df["avg_drop_call_rate"].mean() * 100, 2)


def avg_download_speed(df: pd.DataFrame) -> float:
    return round(df["avg_download_speed"].mean(), 1)


def qoe_by_state(df: pd.DataFrame) -> pd.DataFrame:
    """QoE compliance and key network KPIs aggregated by state."""
    return (
        df.groupby("state")
        .agg(
            qoe_breach_pct=("qoe_below_threshold",
                             lambda x: round(x.mean() * 100, 1)),
            avg_mos=("avg_mos_score", "mean"),
            avg_drop_call_rate=("avg_drop_call_rate",
                                 lambda x: round(x.mean() * 100, 2)),
            avg_congestion=("avg_congestion_pct", "mean"),
            avg_download_speed=("avg_download_speed", "mean"),
        )
        .reset_index()
        .sort_values("qoe_breach_pct", ascending=False)
    )


def qoe_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Daily average MOS score trend."""
    return (
        df.groupby("date")["avg_mos_score"]
        .mean()
        .reset_index()
        .sort_values("date")
    )


# ── Site Economics ───────────────────────────────────────────
def avg_site_profit(df: pd.DataFrame) -> float:
    """Average daily profit per site across filtered data."""
    return round(df["site_profit_proxy"].mean(), 0)


def site_profitability_by_lga(df: pd.DataFrame) -> pd.DataFrame:
    """Site profit metrics aggregated by LGA."""
    return (
        df.groupby(["state", "lga"])
        .agg(
            site_count=("site_count", "first"),
            avg_daily_rev_per_site=("daily_revenue_per_site", "mean"),
            avg_daily_opex_per_site=("daily_opex_per_site", "mean"),
            avg_profit_per_site=("site_profit_proxy", "mean"),
        )
        .reset_index()
        .sort_values("avg_profit_per_site", ascending=False)
    )


# ── GTM & Whitespace ─────────────────────────────────────────
def whitespace_lgas(df: pd.DataFrame) -> pd.DataFrame:
    """LGAs meeting whitespace criteria (high pop, low penetration)."""
    latest = df[df["date"] == df["date"].max()]
    return (
        latest[latest["whitespace_flag"] == 1]
        [[  "state", "lga", "lga_population", "penetration_rate",
            "income_index", "poi_total", "whitespace_flag"]]
        .drop_duplicates(subset=["state", "lga"])
        .sort_values("lga_population", ascending=False)
    )


def gtm_opportunity_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Composite GTM opportunity score per LGA.
    Components:
      - whitespace_score : 1 if whitespace_flag == 1, else 0          (weight 0.30)
      - income_score     : normalised income_index 0-1                 (weight 0.25)
      - poi_score        : normalised poi_total 0-1                    (weight 0.20)
      - gap_score        : 1 - penetration_rate (bigger gap = higher)  (weight 0.15)
      - profit_score     : normalised site_profit_proxy 0-1            (weight 0.10)
    """
    latest = (
        df[df["date"] == df["date"].max()]
        .drop_duplicates(subset=["state", "lga"])
        .copy()
    )

    def norm(series: pd.Series) -> pd.Series:
        mn, mx = series.min(), series.max()
        if mx == mn:
            return pd.Series(np.zeros(len(series)), index=series.index)
        return (series - mn) / (mx - mn)

    latest["whitespace_score"] = latest["whitespace_flag"].astype(float)
    latest["income_score"]     = norm(latest["income_index"])
    latest["poi_score"]        = norm(latest["poi_total"])
    latest["gap_score"]        = 1 - latest["penetration_rate"]
    latest["profit_score"]     = norm(latest["site_profit_proxy"])

    latest["gtm_score"] = (
        latest["whitespace_score"] * 0.30 +
        latest["income_score"]     * 0.25 +
        latest["poi_score"]        * 0.20 +
        latest["gap_score"]        * 0.15 +
        latest["profit_score"]     * 0.10
    ).round(4)

    return (
        latest[[
            "state", "lga", "lga_population", "penetration_rate",
            "income_index", "poi_total", "whitespace_flag",
            "site_profit_proxy", "gtm_score"
        ]]
        .sort_values("gtm_score", ascending=False)
        .reset_index(drop=True)
    )


# ── KPI Card Helpers ─────────────────────────────────────────
def kpi_delta_colour(value: float, positive_is_good: bool = True) -> str:
    """Returns 'normal', 'inverse' for Streamlit metric delta_color."""
    if positive_is_good:
        return "normal"
    return "inverse"


def format_ngn_millions(value: float) -> str:
    return f"₦{value:,.1f}M"


def format_ngn_billions(value: float) -> str:
    return f"₦{value / 1000:,.2f}B"


def format_pct(value: float) -> str:
    return f"{value:.1f}%"