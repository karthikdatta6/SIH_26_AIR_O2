"""
scripts/phase3/06_evaluate_and_benchmark.py
SIH 25178 — Phase 3 Step 6: Comprehensive Test Set Evaluation
Generates: results/metrics/phase3_evaluation_summary.csv
           results/metrics/station_evaluation_summary.csv
           reports/phase3/error_analysis.md
Run: python scripts/phase3/06_evaluate_and_benchmark.py
"""

import os
import pickle
import warnings
import json
import numpy as np
import pandas as pd
from datetime import datetime

warnings.filterwarnings("ignore")

# ─── PATHS ────────────────────────────────────────────────────────────────────
ROOT        = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FE_PATH     = os.path.join(ROOT, "data", "phase3", "features_engineered.parquet")
LGB_DIR     = os.path.join(ROOT, "models", "lightgbm")
STACK_DIR   = os.path.join(ROOT, "models", "ensemble")
OUT_METRICS = os.path.join(ROOT, "results", "metrics")
OUT_REPORTS = os.path.join(ROOT, "reports", "phase3")
os.makedirs(OUT_METRICS, exist_ok=True)
os.makedirs(OUT_REPORTS, exist_ok=True)

# ─── CONSTANTS ────────────────────────────────────────────────────────────────
TARGETS   = ["OZONE_ground", "NO2_ground"]
HORIZONS  = [1, 3, 6, 12, 24, 48]
STATIONS  = [
    "ANAND_VIHAR", "ITO", "OKHLA_PHASE_2", "AYA_NAGAR", "RK_PURAM",
    "DHYAN_CHAND_STADIUM", "MANDIR_MARG", "PUNJABI_BAGH", "JAHANGIRPURI", "DWARKA_SECTOR_8"
]

TEST_START = pd.Timestamp("2025-07-01")
# High-pollution event thresholds (CPCB AQI standards)
OZONE_SEVERE_THRESHOLD = 100.0   # µg/m³ (CPCB Very Poor AQI)
NO2_SEVERE_THRESHOLD   = 150.0   # µg/m³ (CPCB Very Poor AQI)


# ─── HELPER ───────────────────────────────────────────────────────────────────
def safe_metrics(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask   = (~np.isnan(y_true)) & (~np.isnan(y_pred))
    if mask.sum() < 2:
        return {"n": int(mask.sum()), "rmse": np.nan, "mae": np.nan,
                "r2": np.nan, "smape": np.nan, "willmott_d": np.nan}
    yt, yp  = y_true[mask], y_pred[mask]
    rmse    = float(np.sqrt(np.mean((yt - yp) ** 2)))
    mae     = float(np.mean(np.abs(yt - yp)))
    ss_res  = np.sum((yt - yp) ** 2)
    ss_tot  = np.sum((yt - yt.mean()) ** 2)
    r2      = float(1.0 - ss_res / (ss_tot + 1e-12))
    smape   = 100.0 * float(np.mean(2.0 * np.abs(yp - yt) / (np.abs(yt) + np.abs(yp) + 1e-12)))
    d_denom = np.sum((np.abs(yp - yt.mean()) + np.abs(yt - yt.mean())) ** 2)
    willmott_d = float(1.0 - ss_res / (d_denom + 1e-12))
    return {
        "n":           int(mask.sum()),
        "rmse":        round(rmse, 3),
        "mae":         round(mae, 3),
        "r2":          round(r2, 4),
        "smape":       round(smape, 2),
        "willmott_d":  round(willmott_d, 4),
    }


# ─── LOAD DATA ────────────────────────────────────────────────────────────────
print("[EVAL] Loading engineered features …")
df = pd.read_parquet(FE_PATH)
df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"])
df = df.sort_values(["station_id", "timestamp_utc"]).reset_index(drop=True)

test_df = df[df["timestamp_utc"] >= TEST_START].copy()
print(f"[EVAL] Test set: {len(test_df):,} rows")

all_rows        = []
station_rows    = []
error_sections  = []

# ─── MAIN EVALUATION LOOP ─────────────────────────────────────────────────────
for target in TARGETS:
    target_short = "O3" if "OZONE" in target else "NO2"
    severe_thresh = OZONE_SEVERE_THRESHOLD if "OZONE" in target else NO2_SEVERE_THRESHOLD

    for horizon in HORIZONS:
        # ── Load best available model (ensemble > LightGBM) ──
        stacker_path = os.path.join(STACK_DIR, f"stacker_{target_short}_h{horizon}.pkl")
        lgb_path     = os.path.join(LGB_DIR,   f"{target_short}_h{horizon}.pkl")

        if os.path.exists(stacker_path):
            with open(stacker_path, "rb") as f:
                bundle = pickle.load(f)
            model_name = "NNLS_Ensemble"
            lgb_feats  = bundle["lgb_feature_cols"]
            with open(lgb_path, "rb") as f:
                lgb_bundle = pickle.load(f)
            lgb_model  = lgb_bundle["model"]
        elif os.path.exists(lgb_path):
            with open(lgb_path, "rb") as f:
                lgb_bundle = pickle.load(f)
            lgb_model  = lgb_bundle["model"]
            lgb_feats  = lgb_bundle["feature_cols"]
            model_name = "LightGBM"
        else:
            print(f"[EVAL] No model found for {target_short} h{horizon} — skipping")
            continue

        # Build future target
        y_future = test_df.groupby("station_id")[target].shift(-horizon)
        test_mask = ~y_future.isna()

        X_test     = test_df.loc[test_mask, lgb_feats].copy()
        y_true_all = np.clip(y_future[test_mask].values, 0, None)

        # Model predictions
        pred_log   = lgb_model.predict(X_test)
        y_pred_all = np.expm1(np.clip(pred_log, 0, None))

        # ── Persistence baseline ──
        lag_col = f"{target}_lag_1h"
        if lag_col in test_df.columns:
            pers_pred  = test_df.loc[test_mask, lag_col].values
            pers_valid = ~np.isnan(pers_pred)
            pers_m     = safe_metrics(y_true_all[pers_valid], pers_pred[pers_valid])
        else:
            pers_m = {"r2": np.nan, "rmse": np.nan, "mae": np.nan}

        # ── Overall metrics ──
        overall = safe_metrics(y_true_all, y_pred_all)
        delta_r2 = round(overall["r2"] - pers_m.get("r2", np.nan), 4)

        print(f"[EVAL] {model_name} {target_short} t+{horizon}h: "
              f"R²={overall['r2']:.4f} | RMSE={overall['rmse']:.2f} | ΔR²={delta_r2}")

        all_rows.append({
            "model":      model_name,
            "pollutant":  target_short,
            "horizon_h":  horizon,
            "n_samples":  overall["n"],
            "model_r2":   overall["r2"],
            "pers_r2":    pers_m.get("r2", np.nan),
            "delta_r2":   delta_r2,
            "rmse":       overall["rmse"],
            "mae":        overall["mae"],
            "smape_pct":  overall["smape"],
            "willmott_d": overall["willmott_d"],
        })

        # ── Per-Station Evaluation ──
        for station in STATIONS:
            st_mask = test_df["station_id"] == station
            y_fut_st = test_df.loc[st_mask].groupby("station_id")[target].shift(-horizon)
            st_future_mask = ~y_fut_st.isna() & st_mask[st_mask].reset_index(drop=True).values

            X_st    = test_df.loc[st_mask & test_mask, lgb_feats].copy()
            y_st    = np.clip(y_future[st_mask & test_mask].values, 0, None)
            if len(X_st) == 0:
                continue

            pred_st = np.expm1(np.clip(lgb_model.predict(X_st), 0, None))
            st_m    = safe_metrics(y_st, pred_st)

            station_rows.append({
                "station_id": station,
                "pollutant":  target_short,
                "horizon_h":  horizon,
                "n_samples":  st_m["n"],
                "r2":         st_m["r2"],
                "rmse":       st_m["rmse"],
                "mae":        st_m["mae"],
                "smape_pct":  st_m["smape"],
            })

        # ── High-Pollution Event Analysis ──
        severe_idx  = y_true_all >= severe_thresh
        severe_n    = int(severe_idx.sum())
        if severe_n > 0:
            severe_m = safe_metrics(y_true_all[severe_idx], y_pred_all[severe_idx])
        else:
            severe_m = {"r2": np.nan, "rmse": np.nan, "n": 0}

        error_sections.append(
            f"### {target_short} — t+{horizon}h\n"
            f"- Overall R²: **{overall['r2']:.4f}** | RMSE: {overall['rmse']:.2f} µg/m³\n"
            f"- Persistence R²: {pers_m.get('r2', 'N/A'):.4f}  |  ΔR² (Skill Gain): **{delta_r2}**\n"
            f"- Severe Events (≥{severe_thresh} µg/m³): {severe_n} samples | "
            f"R²: {severe_m.get('r2', 'N/A')} | RMSE: {severe_m.get('rmse', 'N/A')}\n"
        )

# ─── SAVE RESULTS ─────────────────────────────────────────────────────────────
if all_rows:
    eval_df = pd.DataFrame(all_rows)
    eval_path = os.path.join(OUT_METRICS, "phase3_evaluation_summary.csv")
    eval_df.to_csv(eval_path, index=False)
    print(f"\n[EVAL] → Saved: {eval_path}")

if station_rows:
    st_df = pd.DataFrame(station_rows)
    st_path = os.path.join(OUT_METRICS, "station_evaluation_summary.csv")
    st_df.to_csv(st_path, index=False)
    print(f"[EVAL] → Saved: {st_path}")

# ─── ERROR ANALYSIS REPORT ────────────────────────────────────────────────────
error_md = "# Phase 3 — Error Analysis Report\n\n"
error_md += f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
error_md += "## Model Performance vs Persistence Baseline (All Horizons)\n\n"
for section in error_sections:
    error_md += section + "\n"

error_md += "\n---\n\n## Notes on Known High-Uncertainty Periods\n\n"
error_md += "- **Monsoon (Jul–Sep):** Sentinel-5P missingness spikes to ~70-80%; model relies on ERA5 + ground only.\n"
error_md += "- **Diwali/Stubble Burning (Oct–Nov):** Expect under-prediction of extreme spikes due to non-meteorological impulse sources.\n"
error_md += "- **Winter Inversions (Dec–Feb):** BLH drops to <100m; high concentration variance; model typically performs well due to strong BLH signal.\n"

with open(os.path.join(OUT_REPORTS, "error_analysis.md"), "w", encoding="utf-8") as f:
    f.write(error_md)
print(f"[EVAL] → Saved: reports/phase3/error_analysis.md")

# ─── FINAL RESULTS SUMMARY TABLE ──────────────────────────────────────────────
if all_rows:
    print("\n[EVAL] ═══════════ FINAL RESULTS SUMMARY ═══════════")
    print(f"{'Pollutant':<10} {'Horizon':<10} {'Model R²':<10} {'Pers R²':<10} {'ΔR²':<8} {'RMSE':<8} {'MAE'}")
    print("─" * 70)
    for row in all_rows:
        print(f"{row['pollutant']:<10} t+{row['horizon_h']}h{'':<6} "
              f"{row['model_r2']:<10.4f} {str(round(row['pers_r2'],4)):<10} "
              f"{str(row['delta_r2']):<8} {row['rmse']:<8.3f} {row['mae']:.3f}")

print("\n[EVAL] ✅ EVALUATION COMPLETE")
