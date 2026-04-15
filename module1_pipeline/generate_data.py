import pandas as pd
import numpy as np
import sqlite3
import os
import logging
from datetime import datetime, timedelta
import random

# ─── LOGGING ─────────────────────────────────────────────────────────────────
os.makedirs("module1_pipeline", exist_ok=True)
logging.basicConfig(
    filename="module1_pipeline/pipeline.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)
np.random.seed(42)
random.seed(42)

# ─── GEOGRAPHIC HIERARCHY ────────────────────────────────────────────────────
# 12 states across South-West, South-South, South-East, and North-Central.
# Each LGA carries real population figures disaggregated from NBS/WorldPop 2024
# state totals. Urban LGAs get higher density; rural LGAs get lower.
# Structure: state → LGA → clusters → site_count

GEO = {
    # ── SOUTH-WEST ──────────────────────────────────────────────────────────
    "Lagos": {
        "Ikeja":          {"clusters": ["IK1", "IK2"], "sites": 10, "population": 890_000, "urban": True},
        "Surulere":       {"clusters": ["SU1", "SU2"], "sites": 8,  "population": 760_000, "urban": True},
        "Lekki":          {"clusters": ["LK1", "LK2"], "sites": 9,  "population": 820_000, "urban": True},
        "Alimosho":       {"clusters": ["AL1", "AL2"], "sites": 11, "population": 1_280_000, "urban": True},
        "Badagry":        {"clusters": ["BD1"],        "sites": 4,  "population": 310_000, "urban": False},
        "Epe":            {"clusters": ["EP1"],        "sites": 3,  "population": 280_000, "urban": False},
        "Ikorodu":        {"clusters": ["IKO1"],       "sites": 6,  "population": 650_000, "urban": True},
    },
    "Ogun": {
        "Abeokuta North": {"clusters": ["AB1", "AB2"], "sites": 6,  "population": 520_000, "urban": True},
        "Sagamu":         {"clusters": ["SG1"],        "sites": 4,  "population": 360_000, "urban": False},
        "Ijebu Ode":      {"clusters": ["IJ1"],        "sites": 3,  "population": 290_000, "urban": False},
        "Ota":            {"clusters": ["OT1"],        "sites": 5,  "population": 480_000, "urban": True},
    },
    "Oyo": {
        "Ibadan North":   {"clusters": ["IBN1","IBN2"],"sites": 9,  "population": 780_000, "urban": True},
        "Ibadan South":   {"clusters": ["IBS1"],       "sites": 6,  "population": 620_000, "urban": True},
        "Ogbomoso":       {"clusters": ["OGB1"],       "sites": 4,  "population": 390_000, "urban": False},
        "Oyo East":       {"clusters": ["OYE1"],       "sites": 3,  "population": 270_000, "urban": False},
    },
    "Osun": {
        "Osogbo":         {"clusters": ["OS1"],        "sites": 5,  "population": 490_000, "urban": True},
        "Ife Central":    {"clusters": ["IF1"],        "sites": 4,  "population": 370_000, "urban": False},
        "Ilesa East":     {"clusters": ["ILE1"],       "sites": 3,  "population": 260_000, "urban": False},
    },
    "Ondo": {
        "Akure South":    {"clusters": ["AK1"],        "sites": 5,  "population": 450_000, "urban": True},
        "Ondo West":      {"clusters": ["OW1"],        "sites": 3,  "population": 280_000, "urban": False},
        "Okitipupa":      {"clusters": ["OKI1"],       "sites": 3,  "population": 230_000, "urban": False},
    },
    "Ekiti": {
        "Ado Ekiti":      {"clusters": ["AD1"],        "sites": 5,  "population": 420_000, "urban": True},
        "Ikole":          {"clusters": ["IKL1"],       "sites": 3,  "population": 240_000, "urban": False},
    },

    # ── NORTH-CENTRAL ───────────────────────────────────────────────────────
    "Kwara": {
        "Ilorin West":    {"clusters": ["ILW1","ILW2"],"sites": 6,  "population": 580_000, "urban": True},
        "Ilorin East":    {"clusters": ["ILE1"],       "sites": 4,  "population": 340_000, "urban": False},
        "Offa":           {"clusters": ["OF1"],        "sites": 3,  "population": 200_000, "urban": False},
    },

    # ── SOUTH-SOUTH ─────────────────────────────────────────────────────────
    "Edo": {
        "Oredo":          {"clusters": ["OR1","OR2"],  "sites": 7,  "population": 620_000, "urban": True},
        "Egor":           {"clusters": ["EG1"],        "sites": 4,  "population": 380_000, "urban": True},
        "Etsako West":    {"clusters": ["ETW1"],       "sites": 3,  "population": 240_000, "urban": False},
    },
    "Delta": {
        "Warri South":    {"clusters": ["WS1","WS2"],  "sites": 8,  "population": 700_000, "urban": True},
        "Oshimili South": {"clusters": ["OSH1"],       "sites": 4,  "population": 360_000, "urban": False},
        "Ethiope East":   {"clusters": ["ETH1"],       "sites": 3,  "population": 270_000, "urban": False},
    },
    "Rivers": {
        "Port Harcourt":  {"clusters": ["PH1","PH2"],  "sites": 10, "population": 1_100_000,"urban": True},
        "Obio-Akpor":     {"clusters": ["OBK1"],       "sites": 6,  "population": 590_000, "urban": True},
        "Degema":         {"clusters": ["DEG1"],       "sites": 3,  "population": 220_000, "urban": False},
    },

    # ── SOUTH-EAST ──────────────────────────────────────────────────────────
    "Anambra": {
        "Onitsha North":  {"clusters": ["ONI1","ONI2"],"sites": 7,  "population": 650_000, "urban": True},
        "Awka South":     {"clusters": ["AWK1"],       "sites": 5,  "population": 480_000, "urban": True},
        "Nnewi North":    {"clusters": ["NNW1"],       "sites": 4,  "population": 330_000, "urban": False},
    },
    "Enugu": {
        "Enugu North":    {"clusters": ["ENN1","ENN2"],"sites": 6,  "population": 560_000, "urban": True},
        "Igbo-Eze North": {"clusters": ["IGE1"],       "sites": 3,  "population": 240_000, "urban": False},
        "Nkanu East":     {"clusters": ["NKE1"],       "sites": 3,  "population": 210_000, "urban": False},
    },
}

# ─── REALISTIC TELECOM PARAMETERS BY URBANICITY ──────────────────────────────
# Grounded in NCC 2024 data:
# - ARPU: ₦3,600–₦4,800/month post-tariff hike (₦120–₦160/day)
# - Data usage: MTN avg 11.3GB, Airtel 8.1GB → blended ~9–11GB urban, 3–6GB rural
# - Voice: 205B minutes nationally / ~165M subs = ~1,240 min/sub/year = ~103/month
# - Drop call rate: NCC threshold <2%, actual urban 1.5–3.5%, rural 3–6%
# - Download speed: urban 4G 15–28 Mbps, rural 3G/4G 4–12 Mbps
# - Congestion: urban busy-hour 15–35%, rural 5–15%
# - Penetration: Lagos ~85%, other SW urban ~65%, rural ~40%

URBAN_PARAMS = {
    "arpu_daily_mean": 148,      # ₦/day (~₦4,440/month)
    "arpu_daily_std": 32,
    "data_usage_gb_mean": 10.2,  # GB/month per active sub
    "data_usage_gb_std": 2.8,
    "voice_min_mean": 112,       # minutes/month per sub
    "voice_min_std": 28,
    "drop_call_rate_mean": 0.022, # 2.2% — above NCC 2% threshold, realistic urban
    "drop_call_rate_std": 0.008,
    "download_speed_mean": 18.5, # Mbps
    "download_speed_std": 5.2,
    "congestion_mean": 0.24,     # 24% busy-hour
    "congestion_std": 0.07,
    "penetration_base": 0.72,    # 72% of population are active subs
}

RURAL_PARAMS = {
    "arpu_daily_mean": 98,       # ₦/day (~₦2,940/month) — lower purchasing power
    "arpu_daily_std": 22,
    "data_usage_gb_mean": 4.8,
    "data_usage_gb_std": 1.6,
    "voice_min_mean": 78,
    "voice_min_std": 20,
    "drop_call_rate_mean": 0.045, # 4.5% — degraded rural infrastructure
    "drop_call_rate_std": 0.012,
    "download_speed_mean": 7.2,
    "download_speed_std": 2.8,
    "congestion_mean": 0.10,
    "congestion_std": 0.03,
    "penetration_base": 0.41,
}

# Lagos premium — highest penetration and ARPU in Nigeria
LAGOS_MULTIPLIER = {
    "arpu": 1.18,
    "data_usage": 1.22,
    "penetration": 1.15,
    "download_speed": 1.20,
}

# Rivers/Delta oil economy premium
OIL_STATE_MULTIPLIER = {
    "arpu": 1.12,
    "data_usage": 1.10,
    "penetration": 1.08,
}


def get_params(state: str, urban: bool) -> dict:
    """Return KPI parameter set with state-level adjustments applied."""
    p = URBAN_PARAMS.copy() if urban else RURAL_PARAMS.copy()
    if state == "Lagos":
        p["arpu_daily_mean"] *= LAGOS_MULTIPLIER["arpu"]
        p["data_usage_gb_mean"] *= LAGOS_MULTIPLIER["data_usage"]
        p["penetration_base"] = min(p["penetration_base"] * LAGOS_MULTIPLIER["penetration"], 0.92)
        p["download_speed_mean"] *= LAGOS_MULTIPLIER["download_speed"]
    elif state in ("Rivers", "Delta"):
        p["arpu_daily_mean"] *= OIL_STATE_MULTIPLIER["arpu"]
        p["data_usage_gb_mean"] *= OIL_STATE_MULTIPLIER["data_usage"]
        p["penetration_base"] = min(p["penetration_base"] * OIL_STATE_MULTIPLIER["penetration"], 0.90)
    return p


# ─── STEP 1: BUILD SITE MASTER ───────────────────────────────────────────────
def build_site_master() -> pd.DataFrame:
    """
    Create one row per network site with its full geographic hierarchy
    and static site attributes. This is the spine every other table joins to.
    """
    rows = []
    site_id = 1
    for state, lgas in GEO.items():
        for lga, meta in lgas.items():
            clusters = meta["clusters"]
            n_sites = meta["sites"]
            population = meta["population"]
            urban = meta["urban"]
            p = get_params(state, urban)

            sites_per_cluster = max(1, n_sites // len(clusters))
            for i in range(n_sites):
                cluster = clusters[i % len(clusters)]
                # Simulate realistic Nigerian lat/lon per state centroid ± spread
                lat_centre, lon_centre = STATE_CENTROIDS[state]
                lat = lat_centre + np.random.uniform(-0.35, 0.35)
                lon = lon_centre + np.random.uniform(-0.35, 0.35)

                rows.append({
                    "site_id":       f"SITE_{site_id:04d}",
                    "state":         state,
                    "lga":           lga,
                    "cluster":       f"Cluster_{cluster}",
                    "urban_flag":    urban,
                    "latitude":      round(lat, 6),
                    "longitude":     round(lon, 6),
                    "lga_population":population,
                    # Site capacity tier — larger sites in urban cores
                    "site_capacity": "High" if urban and i < 3 else ("Medium" if urban else "Low"),
                    # Monthly opex proxy: tower lease + power + maintenance (₦)
                    # Urban: ₦850k–₦1.1M, Rural: ₦420k–₦620k (diesel-heavy)
                    "monthly_opex":  int(np.random.uniform(850_000, 1_100_000)) if urban
                                     else int(np.random.uniform(420_000, 620_000)),
                })
                site_id += 1

    return pd.DataFrame(rows)


# Geographic centroids (lat, lon) per state — realistic coordinates
STATE_CENTROIDS = {
    "Lagos":    (6.52,  3.38),
    "Ogun":     (6.99,  3.35),
    "Oyo":      (7.85,  3.93),
    "Osun":     (7.56,  4.52),
    "Ondo":     (7.09,  5.08),
    "Ekiti":    (7.72,  5.30),
    "Kwara":    (8.50,  4.55),
    "Edo":      (6.34,  5.63),
    "Delta":    (5.70,  5.95),
    "Rivers":   (4.82,  7.03),
    "Anambra":  (6.22,  6.94),
    "Enugu":    (6.46,  7.55),
}


# ─── STEP 2: GENERATE NETWORK KPIs ──────────────────────────────────────────
def generate_network_kpis(sites_df: pd.DataFrame, days: int = 90) -> pd.DataFrame:
    """
    Daily site-level network KPIs for the past `days` days.
    All values grounded in NCC QoS 2024 regulations and operator reports.
    """
    records = []
    end_date = datetime.today().date()
    date_range = [end_date - timedelta(days=i) for i in range(days - 1, -1, -1)]

    for _, site in sites_df.iterrows():
        p = get_params(site["state"], site["urban_flag"])
        for date in date_range:
            # Weekend effect: slightly lower congestion, lower voice, higher data browsing
            weekend = date.weekday() >= 5
            cong_mult = 0.82 if weekend else 1.0
            voice_mult = 0.88 if weekend else 1.0

            drop_rate = np.clip(
                np.random.normal(p["drop_call_rate_mean"], p["drop_call_rate_std"]), 0.005, 0.12
            )
            congestion = np.clip(
                np.random.normal(p["congestion_mean"] * cong_mult, p["congestion_std"]), 0.02, 0.65
            )
            dl_speed = np.clip(
                np.random.normal(p["download_speed_mean"], p["download_speed_std"]), 1.5, 55.0
            )
            # Upload is typically 25–35% of download in Nigerian 4G networks
            ul_speed = np.clip(dl_speed * np.random.uniform(0.25, 0.38), 0.5, 20.0)

            # MOS score: 1–5 scale. Derived from drop rate and speed.
            # Good: 4.0–4.5, Acceptable: 3.5–4.0, Poor: <3.5
            mos = np.clip(4.8 - (drop_rate * 35) - (congestion * 1.8) + (dl_speed * 0.018), 1.0, 5.0)

            records.append({
                "site_id":              site["site_id"],
                "date":                 date.strftime("%Y-%m-%d"),
                "drop_call_rate":       round(drop_rate, 4),
                "congestion_pct":       round(congestion, 4),
                "download_speed_mbps":  round(dl_speed, 2),
                "upload_speed_mbps":    round(ul_speed, 2),
                "mos_score":            round(mos, 2),         # Mean Opinion Score
                "call_setup_success":   round(np.clip(1 - drop_rate * 1.6, 0.82, 0.995), 4),
                "data_traffic_tb":      round(np.random.exponential(0.18 if site["urban_flag"] else 0.07), 4),
                "voice_traffic_erlangs":round(np.random.normal(
                                            28 if site["urban_flag"] else 11,
                                            6 if site["urban_flag"] else 3) * voice_mult, 2),
            })

    return pd.DataFrame(records)


# ─── STEP 3: GENERATE SUBSCRIBER + REVENUE TABLE ────────────────────────────
def generate_revenue_table(sites_df: pd.DataFrame, days: int = 90) -> pd.DataFrame:
    """
    Daily LGA-level revenue and subscriber metrics.
    ARPU grounded in post-tariff-hike NCC 2025 data (₦3,600–₦5,500/month).
    Subscriber counts derived from population × penetration rate.
    """
    records = []
    end_date = datetime.today().date()
    date_range = [end_date - timedelta(days=i) for i in range(days - 1, -1, -1)]

    # One revenue row per LGA per day (aggregated, not per-site)
    lga_meta = sites_df[["state","lga","lga_population","urban_flag"]].drop_duplicates()

    for _, row in lga_meta.iterrows():
        p = get_params(row["state"], row["urban_flag"])
        base_subs = int(row["lga_population"] * p["penetration_base"])

        for date in date_range:
            # Slight subscriber growth trend: +0.04% per day compound
            days_elapsed = (date - (end_date - timedelta(days=days - 1))).days
            growth_factor = 1 + (0.0004 * days_elapsed)
            # Small random daily churn/acquisition noise
            daily_subs = int(base_subs * growth_factor * np.random.uniform(0.995, 1.005))
            new_subs = int(daily_subs * np.random.uniform(0.0015, 0.0035))   # 0.15–0.35% daily new
            churned = int(daily_subs * np.random.uniform(0.0008, 0.0022))    # 0.08–0.22% daily churn

            # ARPU: daily individual amount × active subs
            arpu_today = max(0, np.random.normal(p["arpu_daily_mean"], p["arpu_daily_std"]))
            total_revenue = arpu_today * daily_subs

            # Revenue split: data ~45%, voice ~42%, SMS/VAS ~13% (NCC 2024 ratios)
            data_rev  = total_revenue * np.random.uniform(0.42, 0.48)
            voice_rev = total_revenue * np.random.uniform(0.39, 0.44)
            vas_rev   = total_revenue - data_rev - voice_rev

            # Data usage per sub (GB/month → GB/day)
            data_gb = (np.random.normal(p["data_usage_gb_mean"], p["data_usage_gb_std"]) / 30) * daily_subs
            voice_min = (np.random.normal(p["voice_min_mean"], p["voice_min_std"]) / 30) * daily_subs

            records.append({
                "state":            row["state"],
                "lga":              row["lga"],
                "date":             date.strftime("%Y-%m-%d"),
                "active_subs":      daily_subs,
                "new_subs":         new_subs,
                "churned_subs":     churned,
                "arpu_daily_ngn":   round(arpu_today, 2),
                "total_revenue_ngn":round(total_revenue, 2),
                "data_revenue_ngn": round(data_rev, 2),
                "voice_revenue_ngn":round(voice_rev, 2),
                "vas_revenue_ngn":  round(vas_rev, 2),
                "data_usage_gb":    round(max(0, data_gb), 2),
                "voice_minutes":    round(max(0, voice_min), 2),
            })

    return pd.DataFrame(records)


# ─── STEP 4: SIMULATE EXTERNAL DATA (POPULATION + POI PROXIES) ──────────────
def generate_external_data(sites_df: pd.DataFrame) -> pd.DataFrame:
    """
    External enrichment layer per LGA:
    - Population already seeded from real NBS/WorldPop 2024 figures
    - POI density: markets, motor parks, hospitals, schools per LGA
      (proxied from OSM density patterns for SW Nigeria)
    - Income proxy: based on state GDP per capita differentials
    """
    lga_meta = sites_df[["state","lga","lga_population","urban_flag"]].drop_duplicates()

    # State-level income index (Lagos = 100 baseline)
    # Grounded in NBS GDP per capita 2024 estimates
    INCOME_INDEX = {
        "Lagos": 100, "Rivers": 92, "Delta": 78, "Ogun": 68,
        "Anambra": 61, "Edo": 58, "Oyo": 54, "Enugu": 52,
        "Osun": 44, "Ondo": 43, "Kwara": 40, "Ekiti": 38,
    }

    rows = []
    for _, row in lga_meta.iterrows():
        pop = row["lga_population"]
        urban = row["urban_flag"]
        income_idx = INCOME_INDEX.get(row["state"], 50)

        # POI counts scale with population and urbanicity
        market_density = int(pop / 15_000 * (1.6 if urban else 0.9) * np.random.uniform(0.8, 1.2))
        motor_parks    = int(pop / 80_000 * (1.4 if urban else 0.7) * np.random.uniform(0.7, 1.3))
        hospitals      = int(pop / 50_000 * (1.2 if urban else 0.6) * np.random.uniform(0.8, 1.2))
        schools        = int(pop / 20_000 * (1.1 if urban else 0.8) * np.random.uniform(0.85, 1.15))

        rows.append({
            "state":             row["state"],
            "lga":               row["lga"],
            "lga_population":    pop,
            "income_index":      income_idx,
            "urban_flag":        urban,
            "poi_markets":       max(1, market_density),
            "poi_motor_parks":   max(1, motor_parks),
            "poi_hospitals":     max(1, hospitals),
            "poi_schools":       max(1, schools),
            "poi_total":         max(4, market_density + motor_parks + hospitals + schools),
            "road_density_km":   round(np.random.uniform(180, 420) if urban else np.random.uniform(40, 160), 1),
        })

    return pd.DataFrame(rows)


# ─── STEP 5: MERGE INTO MASTER TABLE ────────────────────────────────────────
def build_master_table(
    sites_df: pd.DataFrame,
    kpi_df: pd.DataFrame,
    rev_df: pd.DataFrame,
    ext_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Join all four tables into one master flat table.
    Every downstream module (Module 2 SQL, Module 3 Power BI,
    Module 4 ML) reads ONLY from this table.
    """
    # Aggregate site KPIs to LGA+date level for joining with revenue
    kpi_lga = kpi_df.merge(
        sites_df[["site_id","state","lga","urban_flag","monthly_opex","site_capacity"]],
        on="site_id", how="left"
    )
    kpi_agg = (
        kpi_lga.groupby(["state","lga","date"], as_index=False)
        .agg(
            avg_drop_call_rate    =("drop_call_rate",      "mean"),
            avg_congestion_pct    =("congestion_pct",      "mean"),
            avg_download_speed    =("download_speed_mbps", "mean"),
            avg_upload_speed      =("upload_speed_mbps",   "mean"),
            avg_mos_score         =("mos_score",           "mean"),
            avg_call_setup_success=("call_setup_success",  "mean"),
            total_data_traffic_tb =("data_traffic_tb",     "sum"),
            total_voice_erlangs   =("voice_traffic_erlangs","sum"),
            total_monthly_opex    =("monthly_opex",        "sum"),
            site_count            =("site_id",             "nunique"),
        )
    )
    # Round aggregated floats
    for col in ["avg_drop_call_rate","avg_congestion_pct","avg_download_speed",
                "avg_upload_speed","avg_mos_score","avg_call_setup_success"]:
        kpi_agg[col] = kpi_agg[col].round(4)

    # Merge revenue + KPI
    master = rev_df.merge(kpi_agg, on=["state","lga","date"], how="left")

    # Merge external enrichment (static per LGA — broadcasts across all dates)
    master = master.merge(ext_df, on=["state","lga"], how="left")

    # ── DERIVED COLUMNS ──────────────────────────────────────────────────────
    # Penetration rate
    master["penetration_rate"] = (master["active_subs"] / master["lga_population"]).round(4)

    # Site profitability proxy:
    # daily_revenue_per_site minus daily_opex_per_site
    master["daily_revenue_per_site"] = (
        master["total_revenue_ngn"] / master["site_count"]
    ).round(2)
    master["daily_opex_per_site"] = (
        master["total_monthly_opex"] / master["site_count"] / 30
    ).round(2)
    master["site_profit_proxy"] = (
        master["daily_revenue_per_site"] - master["daily_opex_per_site"]
    ).round(2)

    # ARPU monthly estimate
    master["arpu_monthly_est"] = (master["arpu_daily_ngn"] * 30).round(2)

    # QoE flag: 1 if below NCC threshold (MOS < 3.5 or drop rate > 2%)
    master["qoe_below_threshold"] = (
        (master["avg_mos_score"] < 3.5) | (master["avg_drop_call_rate"] > 0.02)
    ).astype(int)

    # Churn risk flag: active subs declining AND ARPU dropping
    master = master.sort_values(["state","lga","date"])
    master["subs_7d_change"] = (
        master.groupby(["state","lga"])["active_subs"]
        .transform(lambda x: x.pct_change(7).round(4))
    )
    master["arpu_7d_change"] = (
        master.groupby(["state","lga"])["arpu_daily_ngn"]
        .transform(lambda x: x.pct_change(7).round(4))
    )
    master["churn_risk_flag"] = (
        (master["subs_7d_change"] < -0.01) & (master["arpu_7d_change"] < -0.01)
    ).astype(int)

    # White space flag: high population, low penetration
    master["whitespace_flag"] = (
        (master["lga_population"] > 300_000) & (master["penetration_rate"] < 0.45)
    ).astype(int)

    return master.reset_index(drop=True)


# ─── STEP 6: SAVE TO SQLITE ──────────────────────────────────────────────────
def save_to_db(master: pd.DataFrame, db_path: str = "data/processed/nigeria_rgi.db"):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    master.to_sql("master_table", conn, if_exists="replace", index=False)
    conn.close()
    logger.info(f"Master table saved: {len(master):,} rows × {len(master.columns)} columns → {db_path}")
    print(f"Done. Master table: {len(master):,} rows × {len(master.columns)} columns")
    print(f"Saved to: {db_path}")


# ─── MAIN ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("Pipeline started")
    print("Building site master...")
    sites = build_site_master()

    print("Generating network KPIs (90 days × all sites)...")
    kpis = generate_network_kpis(sites, days=90)

    print("Generating revenue & subscriber table...")
    revenue = generate_revenue_table(sites, days=90)

    print("Generating external enrichment data...")
    external = generate_external_data(sites)

    print("Merging into master table...")
    master = build_master_table(sites, kpis, revenue, external)

    save_to_db(master)
    logger.info("Pipeline complete")