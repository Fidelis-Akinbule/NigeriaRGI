# ============================================================
# NigeriaRGI  |  Module 4  |  site_profitability.py
# Site profitability forecast using gradient boosting.
# Target: site_profit_proxy (continuous, daily NGN per site)
# ============================================================

import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)

# ── Paths ────────────────────────────────────────────────────
DB_PATH    = "data/processed/nigeria_rgi.db"
OUTPUT_DIR = "module4_models/outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

sns.set_theme(style="whitegrid", font_scale=1.05)
BLUE = "#0057A8"
RED  = "#D62728"
GREEN = "#2CA02C"


# ── 1. Load data ─────────────────────────────────────────────
def load_data() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM master_table", conn)
    conn.close()
    df["date"] = pd.to_datetime(df["date"])
    return df


# ── 2. Feature engineering ───────────────────────────────────
FEATURES = [
    "site_count",
    "avg_congestion_pct",
    "avg_download_speed",
    "avg_mos_score",
    "total_monthly_opex",
    "lga_population",
    "penetration_rate",
    "income_index",
    "poi_total",
    "avg_drop_call_rate",
    "urban_flag",
]

TARGET = "site_profit_proxy"


def prepare_features(df: pd.DataFrame):
    df_model = df[FEATURES + [TARGET]].dropna()
    X = df_model[FEATURES]
    y = df_model[TARGET]
    print(f"  Feature matrix: {X.shape[0]:,} rows × {X.shape[1]} features")
    print(f"  Target — site_profit_proxy:")
    print(f"    Mean:  ₦{y.mean():,.0f}")
    print(f"    Std:   ₦{y.std():,.0f}")
    print(f"    Min:   ₦{y.min():,.0f}")
    print(f"    Max:   ₦{y.max():,.0f}")
    return X, y


# ── 3. Train model ───────────────────────────────────────────
def train_model(X, y):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = GradientBoostingRegressor(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=4,
        min_samples_leaf=10,
        random_state=42,
    )
    model.fit(X_train, y_train)

    # Cross-validation R² on training set
    cv_scores = cross_val_score(model, X_train, y_train,
                                cv=5, scoring="r2")
    print(f"\n  Cross-validation R² (5-fold): "
          f"{cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    return model, X_train, X_test, y_train, y_test


# ── 4. Evaluate ──────────────────────────────────────────────
def evaluate(model, X_test, y_test):
    y_pred = model.predict(X_test)

    mae  = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2   = r2_score(y_test, y_pred)

    print("\n" + "=" * 60)
    print("MODEL EVALUATION — Site Profitability Forecast")
    print("=" * 60)
    print(f"  R² Score:  {r2:.4f}")
    print(f"  MAE:       ₦{mae:,.0f}")
    print(f"  RMSE:      ₦{rmse:,.0f}")
    print(f"\n  Business interpretation:")
    print(f"  The model explains {r2 * 100:.1f}% of variance in daily")
    print(f"  site profit. On average, predictions are off by")
    print(f"  ₦{mae:,.0f} per site per day.")

    return y_pred, r2, mae, rmse


# ── 5. Charts ────────────────────────────────────────────────
def plot_feature_importance(model, output_dir):
    importance = pd.DataFrame({
        "Feature":    FEATURES,
        "Importance": model.feature_importances_,
    }).sort_values("Importance", ascending=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(importance["Feature"],
                   importance["Importance"] * 100, color=BLUE)
    ax.bar_label(bars, fmt="%.1f%%", padding=4, fontsize=9)
    ax.set_title("Site Profitability Model — Feature Importance (%)",
                 fontweight="bold")
    ax.set_xlabel("Importance (%)")
    plt.tight_layout()
    path = os.path.join(output_dir, "site_feature_importance.png")
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"  saved → {path}")


def plot_actual_vs_predicted(y_test, y_pred, r2, output_dir):
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(y_test / 1e6, y_pred / 1e6,
               alpha=0.4, color=BLUE, edgecolors="none", s=20)

    # Perfect prediction line
    mn = min(y_test.min(), y_pred.min()) / 1e6
    mx = max(y_test.max(), y_pred.max()) / 1e6
    ax.plot([mn, mx], [mn, mx], color=RED, lw=1.5,
            linestyle="--", label="Perfect prediction")

    ax.set_xlabel("Actual Daily Profit per Site (₦ Millions)")
    ax.set_ylabel("Predicted Daily Profit per Site (₦ Millions)")
    ax.set_title(f"Site Profitability — Actual vs Predicted (R²={r2:.3f})",
                 fontweight="bold")
    ax.legend()
    plt.tight_layout()
    path = os.path.join(output_dir, "site_actual_vs_predicted.png")
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"  saved → {path}")


def plot_residuals(y_test, y_pred, output_dir):
    residuals = y_test.values - y_pred
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Residual distribution
    axes[0].hist(residuals / 1e6, bins=40, color=BLUE, edgecolor="white")
    axes[0].axvline(0, color=RED, linestyle="--", linewidth=1.2)
    axes[0].set_title("Residual Distribution", fontweight="bold")
    axes[0].set_xlabel("Residual (₦ Millions)")
    axes[0].set_ylabel("Count")

    # Residuals vs predicted
    axes[1].scatter(y_pred / 1e6, residuals / 1e6,
                    alpha=0.4, color=BLUE, edgecolors="none", s=20)
    axes[1].axhline(0, color=RED, linestyle="--", linewidth=1.2)
    axes[1].set_title("Residuals vs Predicted", fontweight="bold")
    axes[1].set_xlabel("Predicted (₦ Millions)")
    axes[1].set_ylabel("Residual (₦ Millions)")

    fig.suptitle("Site Profitability Model — Residual Analysis",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    path = os.path.join(output_dir, "site_residuals.png")
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"  saved → {path}")


def plot_profit_forecast_by_lga(df, model, output_dir):
    """Score all LGAs and rank by predicted daily profit per site."""
    latest = df[df["date"] == df["date"].max()].drop_duplicates(
        subset=["state", "lga"]).copy()

    X_score = latest[FEATURES].dropna()
    latest_scored = latest.loc[X_score.index].copy()
    latest_scored["predicted_profit"] = model.predict(X_score)

    top20 = (
        latest_scored[["state", "lga", "predicted_profit"]]
        .sort_values("predicted_profit", ascending=True)
        .tail(20)
    )

    fig, ax = plt.subplots(figsize=(10, 8))
    colors = [GREEN if v > 0 else RED
              for v in top20["predicted_profit"]]
    bars = ax.barh(
        top20["lga"] + " (" + top20["state"] + ")",
        top20["predicted_profit"] / 1e6,
        color=colors
    )
    ax.bar_label(bars, fmt="₦%.2fM", padding=4, fontsize=8)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_title("Top 20 LGAs — Predicted Daily Profit per Site (₦M)",
                 fontweight="bold")
    ax.set_xlabel("Predicted Daily Profit per Site (₦ Millions)")
    plt.tight_layout()
    path = os.path.join(output_dir, "site_profit_forecast_top20.png")
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"  saved → {path}")


# ── Main ──────────────────────────────────────────────────────
def main():
    print("\nNigeriaRGI | Module 4 | Site Profitability Forecast")
    print("=" * 60)

    print("\n[1] Loading data...")
    df = load_data()
    print(f"  Loaded {len(df):,} rows")

    print("\n[2] Preparing features...")
    X, y = prepare_features(df)

    print("\n[3] Training gradient boosting model...")
    model, X_train, X_test, y_train, y_test = train_model(X, y)
    print("  Model trained.")

    print("\n[4] Evaluating model...")
    y_pred, r2, mae, rmse = evaluate(model, X_test, y_test)

    print("\n[5] Generating charts...")
    plot_feature_importance(model, OUTPUT_DIR)
    plot_actual_vs_predicted(y_test, y_pred, r2, OUTPUT_DIR)
    plot_residuals(y_test, y_pred, OUTPUT_DIR)
    plot_profit_forecast_by_lga(df, model, OUTPUT_DIR)

    print("\n" + "=" * 60)
    print(f"Module 4 (site profitability) complete. "
          f"Outputs in {OUTPUT_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()