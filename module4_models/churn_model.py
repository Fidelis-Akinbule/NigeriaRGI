# ============================================================
# NigeriaRGI  |  Module 4  |  churn_model.py
# Logistic regression churn risk model.
# Target: engineered churn_risk label using bottom-20th
# percentile thresholds on subs_7d_change AND arpu_7d_change.
# Rationale: generator data never crosses the -1% hardcoded
# threshold, so percentile-based labelling is used — a more
# statistically defensible approach in any real deployment.
# ============================================================

import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    roc_curve,
    ConfusionMatrixDisplay,
)

# ── Paths ────────────────────────────────────────────────────
DB_PATH    = "data/processed/nigeria_rgi.db"
OUTPUT_DIR = "module4_models/outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

sns.set_theme(style="whitegrid", font_scale=1.05)
BLUE = "#0057A8"
RED  = "#D62728"


# ── 1. Load data ─────────────────────────────────────────────
def load_data() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM master_table", conn)
    conn.close()
    df["date"] = pd.to_datetime(df["date"])
    return df


# ── 2. Engineer churn target ─────────────────────────────────
def engineer_target(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create churn_risk_engineered using bottom-20th percentile
    thresholds on both subs_7d_change and arpu_7d_change.
    An LGA-day is labelled 1 (at-risk) if BOTH metrics fall
    below their respective 20th percentile values.
    """
    # Drop rows where 7-day changes are NaN (first 7 days)
    df = df.dropna(subset=["subs_7d_change", "arpu_7d_change"]).copy()

    subs_thresh = df["subs_7d_change"].quantile(0.20)
    arpu_thresh = df["arpu_7d_change"].quantile(0.20)

    print(f"  Engineered churn thresholds:")
    print(f"    subs_7d_change  < {subs_thresh:.4f}  (20th percentile)")
    print(f"    arpu_7d_change  < {arpu_thresh:.4f}  (20th percentile)")

    df["churn_risk_engineered"] = (
        (df["subs_7d_change"] < subs_thresh) &
        (df["arpu_7d_change"] < arpu_thresh)
    ).astype(int)

    print(f"\n  Target distribution:")
    vc = df["churn_risk_engineered"].value_counts()
    print(f"    0 (stable):  {vc.get(0, 0):,}")
    print(f"    1 (at-risk): {vc.get(1, 0):,}")
    print(f"    Positive rate: {vc.get(1, 0) / len(df) * 100:.1f}%")

    return df


# ── 3. Prepare features ──────────────────────────────────────
FEATURES = [
    "subs_7d_change",
    "arpu_7d_change",
    "avg_mos_score",
    "avg_drop_call_rate",
    "income_index",
    "penetration_rate",
    "avg_congestion_pct",
    "avg_download_speed",
]

def prepare_features(df: pd.DataFrame):
    df_model = df[FEATURES + ["churn_risk_engineered"]].dropna()
    X = df_model[FEATURES]
    y = df_model["churn_risk_engineered"]
    return X, y


# ── 4. Train model ───────────────────────────────────────────
def train_model(X, y):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc  = scaler.transform(X_test)

    model = LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        random_state=42,
    )
    model.fit(X_train_sc, y_train)

    return model, scaler, X_train_sc, X_test_sc, y_train, y_test


# ── 5. Evaluate ──────────────────────────────────────────────
def evaluate(model, X_test_sc, y_test):
    y_pred      = model.predict(X_test_sc)
    y_pred_prob = model.predict_proba(X_test_sc)[:, 1]
    auc         = roc_auc_score(y_test, y_pred_prob)

    print("\n" + "=" * 60)
    print("MODEL EVALUATION")
    print("=" * 60)
    print(f"\n  ROC-AUC Score: {auc:.4f}")
    print("\n  Classification Report:")
    print(classification_report(y_test, y_pred,
                                 target_names=["Stable", "At-Risk"]))
    return y_pred, y_pred_prob, auc


# ── 6. Charts ────────────────────────────────────────────────
def plot_feature_importance(model, output_dir):
    coefficients = pd.DataFrame({
        "Feature":     FEATURES,
        "Coefficient": model.coef_[0],
    }).sort_values("Coefficient", key=abs, ascending=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = [RED if c > 0 else BLUE for c in coefficients["Coefficient"]]
    bars = ax.barh(coefficients["Feature"],
                   coefficients["Coefficient"], color=colors)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_title("Churn Risk Model — Feature Importance (Log Odds)",
                 fontweight="bold")
    ax.set_xlabel("Coefficient (log odds)")

    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=RED,  label="Increases churn risk"),
        Patch(facecolor=BLUE, label="Reduces churn risk"),
    ]
    ax.legend(handles=legend_elements)
    plt.tight_layout()
    path = os.path.join(output_dir, "churn_feature_importance.png")
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"  saved → {path}")


def plot_roc_curve(y_test, y_pred_prob, auc, output_dir):
    fpr, tpr, _ = roc_curve(y_test, y_pred_prob)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(fpr, tpr, color=BLUE, lw=2,
            label=f"ROC Curve (AUC = {auc:.3f})")
    ax.plot([0, 1], [0, 1], color="grey", lw=1, linestyle="--",
            label="Random classifier")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("Churn Risk Model — ROC Curve", fontweight="bold")
    ax.legend()
    plt.tight_layout()
    path = os.path.join(output_dir, "churn_roc_curve.png")
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"  saved → {path}")


def plot_confusion_matrix(y_test, y_pred, output_dir):
    cm = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots(figsize=(6, 5))
    disp = ConfusionMatrixDisplay(
        confusion_matrix=cm,
        display_labels=["Stable", "At-Risk"]
    )
    disp.plot(ax=ax, colorbar=False, cmap="Blues")
    ax.set_title("Churn Risk Model — Confusion Matrix", fontweight="bold")
    plt.tight_layout()
    path = os.path.join(output_dir, "churn_confusion_matrix.png")
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"  saved → {path}")


def plot_risk_by_state(df, model, scaler, output_dir):
    """Score all LGAs and show average churn probability by state."""
    df_score = df[FEATURES].dropna().copy()
    df_idx   = df.loc[df_score.index].copy()

    X_sc = scaler.transform(df_score)
    df_idx["churn_prob"] = model.predict_proba(X_sc)[:, 1]

    state_risk = (
        df_idx.groupby("state")["churn_prob"]
        .mean()
        .reset_index()
        .sort_values("churn_prob", ascending=True)
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = [RED if v > 0.5 else BLUE for v in state_risk["churn_prob"]]
    bars = ax.barh(state_risk["state"],
                   state_risk["churn_prob"] * 100, color=colors)
    ax.bar_label(bars, fmt="%.1f%%", padding=4, fontsize=9)
    ax.axvline(50, color=RED, linestyle="--", linewidth=1.2,
               label="50% risk threshold")
    ax.set_title("Churn Risk Score by State (%)",
                 fontweight="bold")
    ax.set_xlabel("Average Churn Probability (%)")
    ax.legend()
    plt.tight_layout()
    path = os.path.join(output_dir, "churn_risk_by_state.png")
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"  saved → {path}")


# ── Main ──────────────────────────────────────────────────────
def main():
    print("\nNigeriaRGI | Module 4 | Churn Risk Model")
    print("=" * 60)

    print("\n[1] Loading data...")
    df = load_data()
    print(f"  Loaded {len(df):,} rows")

    print("\n[2] Engineering churn target...")
    df = engineer_target(df)

    print("\n[3] Preparing features...")
    X, y = prepare_features(df)
    print(f"  Feature matrix: {X.shape[0]:,} rows × {X.shape[1]} features")

    print("\n[4] Training logistic regression model...")
    model, scaler, X_train_sc, X_test_sc, y_train, y_test = train_model(X, y)
    print("  Model trained.")

    print("\n[5] Evaluating model...")
    y_pred, y_pred_prob, auc = evaluate(model, X_test_sc, y_test)

    print("\n[6] Generating charts...")
    plot_feature_importance(model, OUTPUT_DIR)
    plot_roc_curve(y_test, y_pred_prob, auc, OUTPUT_DIR)
    plot_confusion_matrix(y_test, y_pred, OUTPUT_DIR)
    plot_risk_by_state(df, model, scaler, OUTPUT_DIR)

    print("\n" + "=" * 60)
    print(f"Module 4 (churn) complete. Outputs in {OUTPUT_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()