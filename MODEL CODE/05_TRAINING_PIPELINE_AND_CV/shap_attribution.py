"""
scripts/phase3/07_shap_and_visualizations.py
SIH 25178 — Phase 3 Step 7: SHAP Attribution + Forecast Curves + Phase 4 API Export
Generates: results/figures/ (PNG charts)
           models/NO2/ and models/O3/ (feature_schema.json, metadata.json, model.pkl)
Run: python scripts/phase3/07_shap_and_visualizations.py
"""

import os
import json
import pickle
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime

warnings.filterwarnings("ignore")

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    print("[SHAP] shap not installed. Run: pip install shap")
    SHAP_AVAILABLE = False

# ─── PATHS ────────────────────────────────────────────────────────────────────
ROOT        = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FE_PATH     = os.path.join(ROOT, "data", "phase3", "features_engineered.parquet")
LGB_DIR     = os.path.join(ROOT, "models", "lightgbm")
O3_DIR      = os.path.join(ROOT, "models", "O3")
NO2_DIR     = os.path.join(ROOT, "models", "NO2")
FIG_DIR     = os.path.join(ROOT, "results", "figures")
DOC_DIR     = os.path.join(ROOT, "docs")
os.makedirs(O3_DIR, exist_ok=True)
os.makedirs(NO2_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)

# ─── CONSTANTS ────────────────────────────────────────────────────────────────
TARGETS   = ["OZONE_ground", "NO2_ground"]
HORIZONS  = [1, 3, 6, 12, 24, 48]
TEST_START = pd.Timestamp("2025-07-01")
SHAP_SAMPLE = 2000   # Rows to use for SHAP computation (subsample for speed)


# ─── LOAD DATA ────────────────────────────────────────────────────────────────
print("[SHAP] Loading engineered features …")
df = pd.read_parquet(FE_PATH)
df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"])
df = df.sort_values(["station_id", "timestamp_utc"]).reset_index(drop=True)
test_df = df[df["timestamp_utc"] >= TEST_START].copy()
print(f"[SHAP] Test set: {len(test_df):,} rows")


# ─── SHAP + FORECAST CURVES PER TARGET ───────────────────────────────────────
for target in TARGETS:
    target_short = "O3" if "OZONE" in target else "NO2"
    unit         = "µg/m³"
    export_dir   = O3_DIR if "OZONE" in target else NO2_DIR
    best_metrics_across_horizons = {}

    print(f"\n[SHAP] Processing {target_short} …")

    # ── Use t+1h model for SHAP (most informative) ──
    lgb_path_h1 = os.path.join(LGB_DIR, f"{target_short}_h1.pkl")
    if not os.path.exists(lgb_path_h1):
        print(f"   [SKIP] No LightGBM h1 model for {target_short}")
        continue

    with open(lgb_path_h1, "rb") as f:
        lgb_bundle = pickle.load(f)

    lgb_model  = lgb_bundle["model"]
    lgb_feats  = lgb_bundle["feature_cols"]

    # ── SHAP Feature Attribution ──
    if SHAP_AVAILABLE:
        print(f"   Computing SHAP values on {SHAP_SAMPLE} test samples …")
        X_shap = test_df[lgb_feats].copy().dropna(subset=lgb_feats[:5])
        X_shap = X_shap.sample(min(SHAP_SAMPLE, len(X_shap)), random_state=42)

        explainer   = shap.TreeExplainer(lgb_model)
        shap_values = explainer.shap_values(X_shap)

        # SHAP summary bar plot
        fig, ax = plt.subplots(figsize=(10, 8))
        shap.summary_plot(shap_values, X_shap, plot_type="bar",
                          show=False, max_display=20)
        plt.title(f"SHAP Feature Importance — {target_short} t+1h", fontsize=13)
        plt.tight_layout()
        shap_path = os.path.join(FIG_DIR, f"shap_summary_{target_short}.png")
        plt.savefig(shap_path, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"   → SHAP chart saved: {shap_path}")

        # Top 10 most important features
        mean_abs_shap = np.abs(shap_values).mean(axis=0)
        top_features  = pd.Series(mean_abs_shap, index=lgb_feats).nlargest(10)
        top_feat_path = os.path.join(FIG_DIR, f"shap_top10_{target_short}.csv")
        top_features.reset_index().rename(
            columns={"index": "feature", 0: "mean_abs_shap"}
        ).to_csv(top_feat_path, index=False)
        print(f"   → Top-10 SHAP features: {list(top_features.index)}")
    else:
        print("   SHAP skipped — install with: pip install shap")
        top_features = None

    # ── Forecast Horizon Degradation Curve ──
    horizon_r2   = []
    horizon_rmse = []
    for horizon in HORIZONS:
        lgb_path_h = os.path.join(LGB_DIR, f"{target_short}_h{horizon}.pkl")
        if not os.path.exists(lgb_path_h):
            horizon_r2.append(np.nan)
            horizon_rmse.append(np.nan)
            continue

        with open(lgb_path_h, "rb") as f:
            bundle_h = pickle.load(f)
        m = bundle_h.get("test_metrics", {})
        horizon_r2.append(m.get("r2", np.nan))
        horizon_rmse.append(m.get("rmse", np.nan))
        best_metrics_across_horizons[horizon] = m

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    ax1.plot(HORIZONS, horizon_r2, "o-", color="#3b82f6", lw=2, markersize=7, label="R²")
    ax1.axhline(0.95, color="#10b981", ls="--", alpha=0.7, label="R²=0.95 Target")
    ax1.set_title(f"{target_short} — R² vs Forecast Horizon")
    ax1.set_xlabel("Forecast Horizon (hours)")
    ax1.set_ylabel("R²")
    ax1.set_ylim(0, 1)
    ax1.set_xticks(HORIZONS)
    ax1.legend()

    ax2.plot(HORIZONS, horizon_rmse, "s-", color="#f59e0b", lw=2, markersize=7)
    ax2.set_title(f"{target_short} — RMSE vs Forecast Horizon")
    ax2.set_xlabel("Forecast Horizon (hours)")
    ax2.set_ylabel(f"RMSE ({unit})")
    ax2.set_xticks(HORIZONS)

    plt.suptitle(f"Forecast Accuracy Degradation — {target_short}", fontsize=13, fontweight="bold")
    plt.tight_layout()
    deg_path = os.path.join(FIG_DIR, f"horizon_degradation_{target_short}.png")
    plt.savefig(deg_path, dpi=150)
    plt.close()
    print(f"   → Horizon degradation chart: {deg_path}")

    # ── Sample Forecast vs Actual Time-Series Plot ──
    sample_station = "ITO"
    station_test   = test_df[test_df["station_id"] == sample_station].copy()

    if len(station_test) > 0:
        X_plot    = station_test[lgb_feats].copy()
        pred_log  = lgb_model.predict(X_plot)
        y_pred    = np.expm1(np.clip(pred_log, 0, None))
        y_true    = station_test[target].values

        fig, ax = plt.subplots(figsize=(15, 5))
        plot_slice = slice(0, min(500, len(station_test)))
        ts = station_test["timestamp_utc"].values[plot_slice]
        ax.plot(ts, y_true[plot_slice], lw=1.2, color="#3b82f6", label="Actual", alpha=0.85)
        ax.plot(ts, y_pred[plot_slice], lw=1.2, color="#ef4444", label="Predicted (t+1h)", alpha=0.85)
        ax.set_title(f"{target_short} Forecast vs Actual — Station: {sample_station}")
        ax.set_xlabel("Date (UTC)")
        ax.set_ylabel(f"{target_short} ({unit})")
        ax.legend()
        plt.tight_layout()
        ts_path = os.path.join(FIG_DIR, f"forecast_vs_actual_{target_short}_{sample_station}.png")
        plt.savefig(ts_path, dpi=150)
        plt.close()
        print(f"   → Forecast vs actual chart: {ts_path}")

    # ── Phase 4 API Export ──
    print(f"\n   [EXPORT] Writing Phase 4 API artifacts for {target_short} …")

    # feature_schema.json
    feature_schema = {
        "model_version": "1.0.0",
        "target":        target,
        "target_short":  target_short,
        "feature_count": len(lgb_feats),
        "features": [
            {"name": f, "dtype": "float64", "missing_strategy": "native_nan" if "sat_" in f or "_ground" in f else "error"}
            for f in lgb_feats
        ],
        "input_frequency": "hourly",
        "target_unit":     "ug/m3",
        "transform":       "log1p applied during training; expm1 for inference",
    }
    schema_path = os.path.join(export_dir, "feature_schema.json")
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(feature_schema, f, indent=2)
    print(f"   → feature_schema.json saved")

    # metadata.json
    best_h1 = best_metrics_across_horizons.get(1, {})
    best_h24 = best_metrics_across_horizons.get(24, {})
    best_h48 = best_metrics_across_horizons.get(48, {})
    metadata = {
        "model_name":       f"LightGBM_{target_short}",
        "target_variable":  target,
        "forecast_horizons_hours": HORIZONS,
        "training_period":  "2023-01-01 to 2024-12-31",
        "validation_period": "2025-01-01 to 2025-06-30",
        "test_period":      "2025-07-01 to 2025-12-31",
        "n_stations":       10,
        "algorithm":        "LightGBM (regression_l1 objective)",
        "metrics": {
            "h1_r2":    best_h1.get("r2"),
            "h1_rmse":  best_h1.get("rmse"),
            "h24_r2":   best_h24.get("r2"),
            "h24_rmse": best_h24.get("rmse"),
            "h48_r2":   best_h48.get("r2"),
            "h48_rmse": best_h48.get("rmse"),
        },
        "trained_at": datetime.now().isoformat(),
    }
    meta_path = os.path.join(export_dir, "metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"   → metadata.json saved")

    # model.pkl (bundle all horizons together)
    all_horizon_models = {}
    for horizon in HORIZONS:
        h_path = os.path.join(LGB_DIR, f"{target_short}_h{horizon}.pkl")
        if os.path.exists(h_path):
            with open(h_path, "rb") as f:
                all_horizon_models[horizon] = pickle.load(f)

    model_export_path = os.path.join(export_dir, "model.pkl")
    with open(model_export_path, "wb") as f:
        pickle.dump({
            "horizon_models": all_horizon_models,
            "feature_schema": feature_schema,
            "metadata":       metadata,
        }, f)
    print(f"   → model.pkl saved (all horizons bundled)")
    print(f"   ✅ Phase 4 export complete for {target_short}: {export_dir}")

print()
print("[SHAP] ✅ SHAP + VISUALIZATION + PHASE 4 EXPORT COMPLETE")
print(f"[SHAP] Figures:        {FIG_DIR}")
print(f"[SHAP] O3  API model:  {O3_DIR}")
print(f"[SHAP] NO2 API model:  {NO2_DIR}")
