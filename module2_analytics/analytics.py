# ============================================================
# NigeriaRGI  |  Module 2  |  analytics.py
# Executes all 12 SQL queries, produces charts with business
# narrative. Run from project root:
#   python module2_analytics/analytics.py
# ============================================================

import sqlite3
import os
import textwrap
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# ── Paths ────────────────────────────────────────────────────
DB_PATH      = "data/processed/nigeria_rgi.db"
SQL_PATH     = "module2_analytics/queries.sql"
OUTPUT_DIR   = "module2_analytics/charts"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Style ────────────────────────────────────────────────────
sns.set_theme(style="whitegrid", palette="Blues_d", font_scale=1.05)
ACCENT   = "#0057A8"   # MTN-adjacent deep blue
WARN     = "#D62728"   # alert red
POSITIVE = "#2CA02C"   # positive green
FIG_W    = 12


# ── Helpers ──────────────────────────────────────────────────
def get_connection():
    return sqlite3.connect(DB_PATH)


def run_query(conn, sql: str) -> pd.DataFrame:
    return pd.read_sql(sql, conn)


def save(fig, filename: str):
    path = os.path.join(OUTPUT_DIR, filename)
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"  saved → {path}")


def narrative(text: str):
    """Print a formatted business narrative block."""
    border = "─" * 72
    print(f"\n{border}")
    for line in textwrap.wrap(text.strip(), width=72):
        print(f"  {line}")
    print(border)


def load_queries(path: str) -> dict:
    """Parse queries.sql into {label: sql} by reading -- Q0N: headers."""
    queries = {}
    current_label = None
    current_lines = []
    with open(path) as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("-- Q") and ":" in stripped:
                if current_label and current_lines:
                    queries[current_label] = "\n".join(current_lines).strip()
                current_label = stripped[4:].split(":")[0].strip()
                current_lines = []
            elif current_label is not None:
                current_lines.append(line.rstrip())
    if current_label and current_lines:
        queries[current_label] = "\n".join(current_lines).strip()
    return queries


# ── Section 2.1  Revenue Performance ─────────────────────────
def section_revenue(conn, Q):
    print("\n" + "=" * 72)
    print("SECTION 2.1 — REVENUE PERFORMANCE BY STATE & LGA")
    print("=" * 72)

    # Q01 — Revenue by state
    df = run_query(conn, Q["01"])
    print(df.to_string(index=False))
    narrative(
        "Lagos, Rivers, and Delta consistently lead regional revenue, "
        "reflecting urban subscriber density and higher ARPU. States in "
        "the Yoruba belt (Oyo, Ogun, Osun) show mid-tier performance with "
        "headroom for data monetisation. The VAS share remains below 15% "
        "across all states — a gap that localised bundling campaigns can close."
    )

    fig, axes = plt.subplots(1, 2, figsize=(FIG_W, 5))

    # Left: stacked revenue bar by state
    states = df["state"]
    x = range(len(states))
    axes[0].bar(x, df["data_revenue_NGN_millions"],
                label="Data", color=ACCENT)
    axes[0].bar(x, df["voice_revenue_NGN_millions"],
                bottom=df["data_revenue_NGN_millions"],
                label="Voice", color="#5BA3D9")
    axes[0].bar(x, df["vas_revenue_NGN_millions"],
                bottom=df["data_revenue_NGN_millions"] + df["voice_revenue_NGN_millions"],
                label="VAS", color="#AED6F1")
    axes[0].set_xticks(list(x))
    axes[0].set_xticklabels(states, rotation=45, ha="right", fontsize=9)
    axes[0].set_title("Total Revenue by State (₦ Millions)", fontweight="bold")
    axes[0].set_ylabel("₦ Millions")
    axes[0].legend()

    # Right: ARPU bar
    axes[1].barh(states, df["avg_monthly_arpu_NGN"], color=ACCENT)
    axes[1].axvline(3200, color=WARN, linestyle="--", linewidth=1.2,
                    label="Rural ARPU floor (₦3,200)")
    axes[1].set_title("Average Monthly ARPU by State (₦)", fontweight="bold")
    axes[1].set_xlabel("₦ NGN")
    axes[1].legend()

    fig.suptitle("Q01 — Revenue & ARPU by State", fontsize=13, fontweight="bold")
    plt.tight_layout()
    save(fig, "Q01_revenue_by_state.png")

    # Q02 — Top 10 LGAs
    df2 = run_query(conn, Q["02"])
    print(df2.to_string(index=False))
    narrative(
        "The top 10 LGAs by revenue are concentrated in Lagos and "
        "Rivers — these micro-markets alone likely account for over 40% "
        "of regional revenue. Penetration in these LGAs is already high, "
        "so growth strategy should shift from acquisition to ARPU uplift "
        "through data upsell and VAS cross-sell."
    )

    fig, ax = plt.subplots(figsize=(FIG_W, 5))
    labels = df2["lga"] + " (" + df2["state"] + ")"
    bars = ax.barh(labels, df2["total_revenue_NGN_millions"], color=ACCENT)
    ax.bar_label(bars, fmt="₦%.1fM", padding=4, fontsize=8)
    ax.set_title("Q02 — Top 10 LGAs by Total Revenue (₦ Millions)",
                 fontweight="bold")
    ax.set_xlabel("₦ Millions")
    ax.invert_yaxis()
    plt.tight_layout()
    save(fig, "Q02_top10_lgas_revenue.png")


# ── Section 2.2  Subscriber Base & Penetration ───────────────
def section_subscribers(conn, Q):
    print("\n" + "=" * 72)
    print("SECTION 2.2 — SUBSCRIBER BASE & PENETRATION")
    print("=" * 72)

    # Q03 — Subscriber summary by state
    df = run_query(conn, Q["03"])
    print(df.to_string(index=False))
    narrative(
        "Lagos leads in absolute subscriber volume. However, penetration "
        "rate is the more actionable metric: states with mid-range "
        "populations and penetration below 50% represent the highest "
        "incremental subscriber opportunity with existing infrastructure."
    )

    fig, axes = plt.subplots(1, 2, figsize=(FIG_W, 5))

    axes[0].bar(df["state"], df["total_active_subs"] / 1e3,
                color=ACCENT)
    axes[0].set_title("Active Subscribers by State ('000s)", fontweight="bold")
    axes[0].set_ylabel("Subscribers (thousands)")
    axes[0].set_xticklabels(df["state"], rotation=45, ha="right", fontsize=9)

    axes[1].bar(df["state"], df["total_churned_subs"] / 1e3,
                color=WARN, alpha=0.85)
    axes[1].set_title("Churned Subscribers by State ('000s)", fontweight="bold")
    axes[1].set_ylabel("Churned (thousands)")
    axes[1].set_xticklabels(df["state"], rotation=45, ha="right", fontsize=9)

    fig.suptitle("Q03 — Subscriber Base by State", fontsize=13, fontweight="bold")
    plt.tight_layout()
    save(fig, "Q03_subscribers_by_state.png")

    # Q04 — Lowest penetration LGAs
    df4 = run_query(conn, Q["04"])
    print(df4.to_string(index=False))
    narrative(
        "The 15 LGAs with lowest penetration include several with "
        "populations above 200,000 — these are not small markets. "
        "Low penetration in high-income-index LGAs points to a distribution "
        "or awareness gap, not a demand gap. These are priority targets "
        "for field sales activation and agent network expansion."
    )

    fig, ax = plt.subplots(figsize=(FIG_W, 5))
    colors = [WARN if p < 30 else ACCENT for p in df4["avg_penetration_pct"]]
    bars = ax.barh(df4["lga"] + " (" + df4["state"] + ")",
                   df4["avg_penetration_pct"], color=colors)
    ax.axvline(45, color=WARN, linestyle="--", linewidth=1.2,
               label="Whitespace threshold (45%)")
    ax.bar_label(bars, fmt="%.1f%%", padding=4, fontsize=8)
    ax.set_title("Q04 — 15 LGAs with Lowest Penetration Rate (%)",
                 fontweight="bold")
    ax.set_xlabel("Penetration Rate (%)")
    ax.legend()
    ax.invert_yaxis()
    plt.tight_layout()
    save(fig, "Q04_lowest_penetration_lgas.png")


# ── Section 2.3  QoE & Network Health ────────────────────────
def section_qoe(conn, Q):
    print("\n" + "=" * 72)
    print("SECTION 2.3 — QoE & NETWORK HEALTH")
    print("=" * 72)

    # Q05 — QoE compliance by state
    df = run_query(conn, Q["05"])
    print(df.to_string(index=False))
    narrative(
        "QoE breach percentage measures how often a state's network "
        "falls below NCC thresholds (MOS < 3.5 or drop call rate > 2%). "
        "States with breach rates above 40% face regulatory risk and "
        "elevated churn probability. The relationship between congestion "
        "and MOS score is direct — congestion relief is the fastest lever "
        "to improve QoE compliance."
    )

    fig, axes = plt.subplots(1, 2, figsize=(FIG_W, 5))

    colors = [WARN if v > 40 else ACCENT for v in df["qoe_breach_pct"]]
    axes[0].bar(df["state"], df["qoe_breach_pct"], color=colors)
    axes[0].axhline(40, color=WARN, linestyle="--", linewidth=1.2,
                    label="40% alert threshold")
    axes[0].set_title("QoE Breach Rate by State (%)", fontweight="bold")
    axes[0].set_ylabel("Breach Rate (%)")
    axes[0].set_xticklabels(df["state"], rotation=45, ha="right", fontsize=9)
    axes[0].legend()

    axes[1].bar(df["state"], df["avg_mos_score"], color=ACCENT)
    axes[1].axhline(3.5, color=WARN, linestyle="--", linewidth=1.2,
                    label="NCC MOS threshold (3.5)")
    axes[1].set_title("Average MOS Score by State", fontweight="bold")
    axes[1].set_ylabel("MOS Score")
    axes[1].set_ylim(2.5, 5.0)
    axes[1].set_xticklabels(df["state"], rotation=45, ha="right", fontsize=9)
    axes[1].legend()

    fig.suptitle("Q05 — QoE Compliance by State", fontsize=13, fontweight="bold")
    plt.tight_layout()
    save(fig, "Q05_qoe_compliance_by_state.png")

    # Q06 — Worst LGAs by drop call rate
    df6 = run_query(conn, Q["06"])
    print(df6.to_string(index=False))
    narrative(
        "These 10 LGAs have the highest average drop call rates in the "
        "region. Each percentage point above the NCC 2% threshold "
        "correlates with measurable churn acceleration. The network "
        "operations team should treat this list as a priority "
        "field-investigation queue — congestion relief or equipment "
        "replacement at these sites will have immediate commercial impact."
    )

    fig, ax = plt.subplots(figsize=(FIG_W, 5))
    colors = [WARN if v > 2 else ACCENT for v in df6["avg_drop_call_rate_pct"]]
    bars = ax.barh(df6["lga"] + " (" + df6["state"] + ")",
                   df6["avg_drop_call_rate_pct"], color=colors)
    ax.axvline(2.0, color=WARN, linestyle="--", linewidth=1.2,
               label="NCC threshold (2%)")
    ax.bar_label(bars, fmt="%.2f%%", padding=4, fontsize=8)
    ax.set_title("Q06 — 10 LGAs with Highest Drop Call Rate (%)",
                 fontweight="bold")
    ax.set_xlabel("Drop Call Rate (%)")
    ax.legend()
    ax.invert_yaxis()
    plt.tight_layout()
    save(fig, "Q06_worst_drop_call_rate_lgas.png")


# ── Section 2.4  Site Profitability ──────────────────────────
def section_site_profitability(conn, Q):
    print("\n" + "=" * 72)
    print("SECTION 2.4 — SITE PROFITABILITY")
    print("=" * 72)

    # Q07 — Site profitability by LGA
    df = run_query(conn, Q["07"])
    print(df.head(15).to_string(index=False))
    narrative(
        "Daily profit per site is the clearest measure of infrastructure "
        "return on investment. Urban LGAs with high subscriber density and "
        "low opex generate the strongest margins. Rural LGAs with few "
        "subscribers spread across many sites show the weakest returns — "
        "candidates for shared infrastructure agreements or passive "
        "network monetisation."
    )

    top15 = df.head(15)
    fig, ax = plt.subplots(figsize=(FIG_W, 6))
    colors = [POSITIVE if v > 0 else WARN
              for v in top15["avg_daily_profit_per_site_NGN"]]
    bars = ax.barh(top15["lga"] + " (" + top15["state"] + ")",
                   top15["avg_daily_profit_per_site_NGN"] / 1e3, color=colors)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.bar_label(bars, fmt="₦%.1fK", padding=4, fontsize=8)
    ax.set_title("Q07 — Top 15 LGAs: Avg Daily Profit per Site (₦ '000s)",
                 fontweight="bold")
    ax.set_xlabel("Daily Profit per Site (₦ thousands)")
    ax.invert_yaxis()
    plt.tight_layout()
    save(fig, "Q07_site_profitability_top15.png")

    # Q08 — Loss-making LGAs
    df8 = run_query(conn, Q["08"])
    if df8.empty:
        print("  No loss-making LGAs found — all sites running at positive margin.")
        narrative(
            "No LGAs are running at a net loss at the site level, which "
            "indicates the simulated opex parameters are well-calibrated. "
            "In a live environment this query surfaces the escalation list "
            "for the RGM to review tower lease renegotiations."
        )
    else:
        print(df8.to_string(index=False))
        narrative(
            "These LGAs are generating less daily revenue per site than "
            "they are spending on opex. Without intervention — opex "
            "renegotiation, traffic offload, or site consolidation — these "
            "markets are a direct drag on regional EBITDA."
        )

        fig, ax = plt.subplots(figsize=(FIG_W, max(4, len(df8) * 0.5)))
        ax.barh(df8["lga"] + " (" + df8["state"] + ")",
                df8["avg_daily_profit_per_site_NGN"] / 1e3, color=WARN)
        ax.axvline(0, color="black", linewidth=0.8)
        ax.set_title("Q08 — Loss-Making LGAs: Daily Profit per Site",
                     fontweight="bold")
        ax.set_xlabel("Daily Profit per Site (₦ thousands)")
        ax.invert_yaxis()
        plt.tight_layout()
        save(fig, "Q08_loss_making_lgas.png")


# ── Section 2.5  Early Warning Signals ───────────────────────
def section_early_warning(conn, Q):
    print("\n" + "=" * 72)
    print("SECTION 2.5 — EARLY WARNING SIGNALS")
    print("=" * 72)

    # Q09 — Active churn risk flags
    df = run_query(conn, Q["09"])
    print(df.to_string(index=False))
    narrative(
        "LGAs appearing on the churn risk flag list are experiencing "
        "simultaneous subscriber decline and ARPU erosion over a 7-day "
        "window. This dual deterioration pattern precedes mass churn by "
        "approximately 14-21 days in typical telecom markets. Retention "
        "offers — targeted data bonuses, loyalty credits — should be "
        "deployed to these LGAs within 48 hours of flag activation."
    )

    if not df.empty:
        fig, ax = plt.subplots(figsize=(FIG_W, max(4, len(df) * 0.45)))
        scatter = ax.scatter(
            df["avg_subs_7d_change_pct"],
            df["avg_arpu_7d_change_pct"],
            c=df["churn_flag_days"],
            cmap="Reds",
            s=df["avg_active_subs"] / df["avg_active_subs"].max() * 300 + 40,
            alpha=0.8,
            edgecolors="black",
            linewidths=0.5
        )
        plt.colorbar(scatter, ax=ax, label="Churn Flag Days")
        ax.axhline(0, color="black", linewidth=0.6, linestyle="--")
        ax.axvline(0, color="black", linewidth=0.6, linestyle="--")

        for _, row in df.iterrows():
            ax.annotate(row["lga"],
                        (row["avg_subs_7d_change_pct"],
                         row["avg_arpu_7d_change_pct"]),
                        textcoords="offset points", xytext=(6, 4), fontsize=7)

        ax.set_title("Q09 — Churn Risk: 7-Day Subscriber vs ARPU Change (%)",
                     fontweight="bold")
        ax.set_xlabel("7-Day Subscriber Change (%)")
        ax.set_ylabel("7-Day ARPU Change (%)")
        plt.tight_layout()
        save(fig, "Q09_churn_risk_scatter.png")

    # Q10 — ARPU deterioration watch
    df10 = run_query(conn, Q["10"])
    print(df10.to_string(index=False))
    narrative(
        "ARPU deterioration without subscriber loss is an early-stage "
        "commercial warning. It signals that subscribers are downgrading "
        "their spend — switching to lower-tier plans, reducing data top-ups, "
        "or shifting voice usage to OTT apps. These LGAs need product "
        "mix and pricing review before the revenue erosion compounds."
    )

    if not df10.empty:
        fig, ax = plt.subplots(figsize=(FIG_W, 5))
        colors = [WARN if v < -1 else "#F5A623"
                  for v in df10["avg_arpu_7d_change_pct"]]
        bars = ax.barh(df10["lga"] + " (" + df10["state"] + ")",
                       df10["avg_arpu_7d_change_pct"], color=colors)
        ax.axvline(0, color="black", linewidth=0.8)
        ax.bar_label(bars, fmt="%.2f%%", padding=4, fontsize=8)
        ax.set_title("Q10 — Top 15 LGAs: ARPU 7-Day Deterioration (%)",
                     fontweight="bold")
        ax.set_xlabel("7-Day ARPU Change (%)")
        ax.invert_yaxis()
        plt.tight_layout()
        save(fig, "Q10_arpu_deterioration_watch.png")


# ── Section 2.6  Whitespace & Demand Gaps ────────────────────
def section_whitespace(conn, Q):
    print("\n" + "=" * 72)
    print("SECTION 2.6 — WHITESPACE & DEMAND GAPS")
    print("=" * 72)

    # Q11 — Whitespace LGAs
    df = run_query(conn, Q["11"])
    print(df.to_string(index=False))
    narrative(
        "Whitespace LGAs are defined as markets with populations above "
        "300,000 and penetration below 45%. These are not marginal markets "
        "— they represent addressable revenue that competitors are either "
        "capturing or that remains entirely untapped. The combination of "
        "population size and low penetration makes these the highest-ROI "
        "targets for network expansion or distribution push."
    )

    if not df.empty:
        fig, ax = plt.subplots(figsize=(FIG_W, 5))
        ax.scatter(
            df["avg_income_index"],
            df["avg_penetration_pct"],
            s=df["lga_population"] / df["lga_population"].max() * 400 + 40,
            color=WARN, alpha=0.75, edgecolors="black", linewidths=0.5
        )
        for _, row in df.iterrows():
            ax.annotate(row["lga"],
                        (row["avg_income_index"], row["avg_penetration_pct"]),
                        textcoords="offset points", xytext=(6, 4), fontsize=7)
        ax.axhline(45, color=ACCENT, linestyle="--", linewidth=1.2,
                   label="Whitespace threshold (45%)")
        ax.set_title("Q11 — Whitespace LGAs: Income Index vs Penetration\n"
                     "(bubble size = population)", fontweight="bold")
        ax.set_xlabel("Income Index (Lagos = 100)")
        ax.set_ylabel("Average Penetration Rate (%)")
        ax.legend()
        plt.tight_layout()
        save(fig, "Q11_whitespace_lgas.png")

    # Q12 — Composite GTM opportunity
    df12 = run_query(conn, Q["12"])
    print(df12.to_string(index=False))
    narrative(
        "The composite opportunity list ranks LGAs by three converging "
        "signals: whitespace flag (unmet demand), income index (revenue "
        "potential), and POI density (commercial footfall and distribution "
        "anchor points). LGAs at the top of this list should receive "
        "immediate field sales team deployment, agent recruitment drives, "
        "and location-specific promotional offers in the next planning cycle."
    )

    fig, ax = plt.subplots(figsize=(FIG_W, 6))
    palette = [WARN if w == 1 else ACCENT for w in df12["whitespace_flag"]]
    bars = ax.barh(
        df12["lga"] + " (" + df12["state"] + ")",
        df12["avg_income_index"],
        color=palette
    )
    ax.bar_label(bars, fmt="%.0f", padding=4, fontsize=8)

    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=WARN, label="Whitespace flagged"),
        Patch(facecolor=ACCENT, label="Standard opportunity")
    ]
    ax.legend(handles=legend_elements)
    ax.set_title("Q12 — Composite GTM Opportunity: Top 15 LGAs by Income Index",
                 fontweight="bold")
    ax.set_xlabel("Income Index (Lagos = 100)")
    ax.invert_yaxis()
    plt.tight_layout()
    save(fig, "Q12_gtm_opportunity_composite.png")


# ── Main ──────────────────────────────────────────────────────
def main():
    print("\nNigeriaRGI | Module 2 | Descriptive Analytics")
    print("=" * 72)

    conn = get_connection()
    Q = load_queries(SQL_PATH)

    print(f"\nLoaded {len(Q)} queries from {SQL_PATH}")
    print(f"Charts will be saved to: {OUTPUT_DIR}/\n")

    section_revenue(conn, Q)
    section_subscribers(conn, Q)
    section_qoe(conn, Q)
    section_site_profitability(conn, Q)
    section_early_warning(conn, Q)
    section_whitespace(conn, Q)

    conn.close()

    print("\n" + "=" * 72)
    print(f"Module 2 complete. {len(os.listdir(OUTPUT_DIR))} charts saved.")
    print("=" * 72)


if __name__ == "__main__":
    main()