# ============================================================
# NigeriaRGI  |  Module 5  |  gtm_scoring.py
# Composite GTM opportunity scoring across all 38+ LGAs.
# Scoring methodology mirrors metrics.py for consistency.
# Output: ranked opportunity table + charts.
# Run: python module5_gtm/gtm_scoring.py
# ============================================================

import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

# ── Paths ────────────────────────────────────────────────────
DB_PATH    = "data/processed/nigeria_rgi.db"
OUTPUT_DIR = "module5_gtm/outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

sns.set_theme(style="whitegrid", font_scale=1.05)
BLUE  = "#0057A8"
RED   = "#D62728"
GREEN = "#2CA02C"
AMBER = "#F5A623"

# ── Scoring weights ──────────────────────────────────────────
WEIGHTS = {
    "whitespace_score": 0.30,   # High pop, low penetration
    "income_score":     0.25,   # Revenue potential
    "poi_score":        0.20,   # Commercial footfall
    "gap_score":        0.15,   # Penetration gap (1 - rate)
    "profit_score":     0.10,   # Existing site economics
}


# ── 1. Load data ─────────────────────────────────────────────
def load_data() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM master_table", conn)
    conn.close()
    df["date"] = pd.to_datetime(df["date"])
    return df


# ── 2. Build LGA snapshot ────────────────────────────────────
def build_lga_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    """
    One row per LGA using the latest date.
    Aggregates all scoring inputs to LGA grain.
    """
    latest_date = df["date"].max()
    latest = df[df["date"] == latest_date].copy()

    snapshot = (
        latest.groupby(["state", "lga"])
        .agg(
            lga_population   =("lga_population",    "first"),
            income_index     =("income_index",       "first"),
            poi_total        =("poi_total",          "first"),
            poi_markets      =("poi_markets",        "first"),
            poi_hospitals    =("poi_hospitals",      "first"),
            poi_schools      =("poi_schools",        "first"),
            road_density_km  =("road_density_km",    "first"),
            urban_flag       =("urban_flag",         "first"),
            penetration_rate =("penetration_rate",   "mean"),
            site_profit_proxy=("site_profit_proxy",  "mean"),
            active_subs      =("active_subs",        "sum"),
            avg_arpu         =("arpu_monthly_est",   "mean"),
            whitespace_flag  =("whitespace_flag",    "first"),
            avg_mos_score    =("avg_mos_score",      "mean"),
            avg_drop_call_rate=("avg_drop_call_rate","mean"),
        )
        .reset_index()
    )
    return snapshot


# ── 3. Compute GTM score ──────────────────────────────────────
def norm(series: pd.Series) -> pd.Series:
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series(np.zeros(len(series)), index=series.index)
    return (series - mn) / (mx - mn)


def compute_gtm_score(snapshot: pd.DataFrame) -> pd.DataFrame:
    df = snapshot.copy()

    df["whitespace_score"] = df["whitespace_flag"].astype(float)
    df["income_score"]     = norm(df["income_index"])
    df["poi_score"]        = norm(df["poi_total"])
    df["gap_score"]        = 1 - df["penetration_rate"]
    df["profit_score"]     = norm(df["site_profit_proxy"])

    df["gtm_score"] = (
        df["whitespace_score"] * WEIGHTS["whitespace_score"] +
        df["income_score"]     * WEIGHTS["income_score"]     +
        df["poi_score"]        * WEIGHTS["poi_score"]        +
        df["gap_score"]        * WEIGHTS["gap_score"]        +
        df["profit_score"]     * WEIGHTS["profit_score"]
    ).round(4)

    df = df.sort_values("gtm_score", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1
    df["priority_tier"] = pd.cut(
        df["rank"],
        bins=[0, 10, 20, len(df)],
        labels=["🔴 Priority (Top 10)",
                "🟡 Watch (11-20)",
                "🔵 Standard"]
    )

    return df


# ── 4. Print opportunity table ────────────────────────────────
def print_opportunity_table(df: pd.DataFrame):
    print("\n" + "=" * 80)
    print("GTM OPPORTUNITY RANKING — ALL LGAs")
    print("=" * 80)

    display = df[[
        "rank", "state", "lga", "lga_population",
        "penetration_rate", "income_index", "poi_total",
        "whitespace_flag", "gtm_score", "priority_tier"
    ]].copy()
    display["penetration_rate"] = (
        display["penetration_rate"] * 100).round(1)
    display = display.rename(columns={
        "rank":             "Rank",
        "state":            "State",
        "lga":              "LGA",
        "lga_population":   "Population",
        "penetration_rate": "Penetration %",
        "income_index":     "Income Idx",
        "poi_total":        "POI Total",
        "whitespace_flag":  "Whitespace",
        "gtm_score":        "GTM Score",
        "priority_tier":    "Tier",
    })
    print(display.to_string(index=False))

    print("\n" + "─" * 80)
    print("TOP 10 PRIORITY TARGETS — FIELD DEPLOYMENT RECOMMENDATION")
    print("─" * 80)
    top10 = df.head(10)[[
        "rank", "state", "lga", "lga_population",
        "penetration_rate", "income_index", "gtm_score"
    ]].copy()
    top10["penetration_rate"] = (top10["penetration_rate"] * 100).round(1)
    print(top10.to_string(index=False))

    print("\n  BUSINESS RECOMMENDATION:")
    print("  Deploy field sales teams and agent recruitment drives")
    print("  to the top 10 LGAs above in the next planning cycle.")
    print("  Priority: whitespace-flagged LGAs first (whitespace_flag=1),")
    print("  followed by high-income, high-POI markets.")


# ── 5. Export CSV ─────────────────────────────────────────────
def export_csv(df: pd.DataFrame):
    path = os.path.join(OUTPUT_DIR, "gtm_opportunity_ranking.csv")
    df.to_csv(path, index=False)
    print(f"\n  Ranking table saved → {path}")


# ── 6. Charts ─────────────────────────────────────────────────
def plot_gtm_ranking(df: pd.DataFrame, output_dir: str):
    top15 = df.head(15).copy()
    colors = [RED if w == 1 else BLUE
              for w in top15["whitespace_flag"]]

    fig, ax = plt.subplots(figsize=(11, 7))
    bars = ax.barh(
        top15["lga"] + " (" + top15["state"] + ")",
        top15["gtm_score"],
        color=colors
    )
    ax.bar_label(bars, fmt="%.3f", padding=4, fontsize=9)
    ax.set_title("Top 15 LGAs — Composite GTM Opportunity Score",
                 fontweight="bold")
    ax.set_xlabel("GTM Score (0–1)")
    ax.invert_yaxis()

    legend_elements = [
        mpatches.Patch(facecolor=RED,  label="Whitespace flagged"),
        mpatches.Patch(facecolor=BLUE, label="Standard opportunity"),
    ]
    ax.legend(handles=legend_elements)
    plt.tight_layout()
    path = os.path.join(output_dir, "gtm_top15_ranking.png")
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"  saved → {path}")


def plot_score_components(df: pd.DataFrame, output_dir: str):
    """Stacked bar showing score component contribution per top 15 LGA."""
    top15 = df.head(15).copy()
    labels = top15["lga"] + " (" + top15["state"] + ")"

    components = {
        "Whitespace (30%)": top15["whitespace_score"] * WEIGHTS["whitespace_score"],
        "Income (25%)":     top15["income_score"]     * WEIGHTS["income_score"],
        "POI (20%)":        top15["poi_score"]        * WEIGHTS["poi_score"],
        "Gap (15%)":        top15["gap_score"]        * WEIGHTS["gap_score"],
        "Site Profit (10%)":top15["profit_score"]     * WEIGHTS["profit_score"],
    }
    colors_stack = [RED, BLUE, "#5BA3D9", AMBER, GREEN]

    fig, ax = plt.subplots(figsize=(11, 7))
    bottom = np.zeros(len(top15))
    for (label, values), color in zip(components.items(), colors_stack):
        ax.barh(labels, values.values, left=bottom,
                label=label, color=color)
        bottom += values.values

    ax.set_title("GTM Score Components — Top 15 LGAs",
                 fontweight="bold")
    ax.set_xlabel("Score Contribution")
    ax.legend(loc="lower right", fontsize=9)
    ax.invert_yaxis()
    plt.tight_layout()
    path = os.path.join(output_dir, "gtm_score_components.png")
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"  saved → {path}")


def plot_penetration_vs_income(df: pd.DataFrame, output_dir: str):
    """Scatter: income index vs penetration, sized by population,
    coloured by GTM tier."""
    df = df.copy()
    df["penetration_pct"] = (df["penetration_rate"] * 100).round(1)
    color_map = {
        "🔴 Priority (Top 10)": RED,
        "🟡 Watch (11-20)":     AMBER,
        "🔵 Standard":          BLUE,
    }

    fig, ax = plt.subplots(figsize=(11, 7))
    for tier, grp in df.groupby("priority_tier", observed=True):
        ax.scatter(
            grp["income_index"],
            grp["penetration_pct"],
            s=grp["lga_population"] / grp["lga_population"].max() * 400 + 30,
            color=color_map.get(str(tier), BLUE),
            alpha=0.75,
            edgecolors="black",
            linewidths=0.4,
            label=str(tier),
        )
    for _, row in df[df["priority_tier"] == "🔴 Priority (Top 10)"].iterrows():
        ax.annotate(
            row["lga"],
            (row["income_index"], row["penetration_pct"]),
            textcoords="offset points", xytext=(6, 4), fontsize=7
        )
    ax.axhline(45, color=RED, linestyle="--", linewidth=1.2,
               label="45% whitespace threshold")
    ax.set_xlabel("Income Index (Lagos = 100)")
    ax.set_ylabel("Penetration Rate (%)")
    ax.set_title("Income vs Penetration — GTM Priority Tiers\n"
                 "(bubble size = LGA population)",
                 fontweight="bold")
    ax.legend(fontsize=9)
    plt.tight_layout()
    path = os.path.join(output_dir, "gtm_income_vs_penetration.png")
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"  saved → {path}")


def plot_state_opportunity_summary(df: pd.DataFrame, output_dir: str):
    """Average GTM score and count of top-10 LGAs per state."""
    state_summary = (
        df.groupby("state")
        .agg(
            avg_gtm_score=("gtm_score", "mean"),
            top10_count=("rank", lambda x: (x <= 10).sum()),
            lga_count=("lga", "count"),
        )
        .reset_index()
        .sort_values("avg_gtm_score", ascending=True)
    )

    fig, axes = plt.subplots(1, 2, figsize=(13, 6))

    axes[0].barh(state_summary["state"],
                 state_summary["avg_gtm_score"], color=BLUE)
    axes[0].set_title("Avg GTM Score by State", fontweight="bold")
    axes[0].set_xlabel("Average GTM Score")

    colors2 = [RED if v > 0 else BLUE
               for v in state_summary["top10_count"]]
    axes[1].barh(state_summary["state"],
                 state_summary["top10_count"], color=colors2)
    axes[1].set_title("No. of Top-10 Priority LGAs by State",
                      fontweight="bold")
    axes[1].set_xlabel("Count in Top 10")

    fig.suptitle("GTM Opportunity — State-Level Summary",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    path = os.path.join(output_dir, "gtm_state_summary.png")
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"  saved → {path}")


# ── Main ──────────────────────────────────────────────────────
def main():
    print("\nNigeriaRGI | Module 5 | GTM Opportunity Scoring")
    print("=" * 60)

    print("\n[1] Loading data...")
    df = load_data()
    print(f"  Loaded {len(df):,} rows")

    print("\n[2] Building LGA snapshot...")
    snapshot = build_lga_snapshot(df)
    print(f"  {len(snapshot)} LGAs in snapshot")

    print("\n[3] Computing GTM scores...")
    scored = compute_gtm_score(snapshot)
    print(f"  Scoring complete. Score range: "
          f"{scored['gtm_score'].min():.3f} – "
          f"{scored['gtm_score'].max():.3f}")

    print_opportunity_table(scored)

    print("\n[4] Exporting CSV...")
    export_csv(scored)

    print("\n[5] Generating charts...")
    plot_gtm_ranking(scored, OUTPUT_DIR)
    plot_score_components(scored, OUTPUT_DIR)
    plot_penetration_vs_income(scored, OUTPUT_DIR)
    plot_state_opportunity_summary(scored, OUTPUT_DIR)

    print("\n" + "=" * 60)
    print(f"Module 5 complete. Outputs in {OUTPUT_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()