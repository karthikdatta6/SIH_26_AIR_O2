"""
scripts/phase3/03_train_lightgbm.py
SIH 25178 — Phase 3 Step 3: Multi-Horizon LightGBM Training
Trains one LightGBM model per horizon per pollutant (12 models total: 6h × 2 targets)
Saves: models/lightgbm/O3_h{horizon}.pkl, models/lightgbm/NO2_h{horizon}.pkl
Run: python scripts/phase3/03_train_lightgbm.py
"""

import os
import pickle
import warnings
import json
import numpy as np
import pandas as pd
import lightgbm as lgb
from datetime import datetime

warnings.filterwarnings("ignore")

# ─── PATHS ────────────────────────────────────────────────────────────────────
ROOT       = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FE_PATH    = os.path.join(ROOT, "data", "phase3", "features_engineered.parquet")
MODEL_DIR  = os.path.join(ROOT, "models", "lightgbm")
OUT_METRICS = os.path.join(ROOT, "results", "metrics")
EXP_DIR    = os.path.join(ROOT, "experiments")
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(OUT_METRICS, exist_ok=True)
os.makedirs(EXP_DIR, exist_ok=True)

# ─── CONSTANTS ────────────────────────────────────────────────────────────────
TARGETS   = ["OZONE_ground", "NO2_ground"]
HORIZONS  = [1, 3, 6, 12, 24, 48]     # hours ahead

# All feature columns (exclude metadata, targets, and engineered target cols)
META_COLS  = ["timestamp_utc", "station_id"]
TARGET_RAW = ["OZONE_ground", "NO2_ground"]

# LightGBM hyperparameters
LGB_PARAMS = {
    "objective":       "regression_l1",   # MAE loss — robust to pollution spikes
    "metric":          "rmse",
    "boosting_type":   "gbdt",
    "num_leaves":      127,
    "learning_rate":   0.03,
    "n_estimators":    2500,
    "feature_fraction": 0.7,             # Subsample features → prevents overfit
    "bagging_fraction": 0.8,             # Subsample rows
    "bagging_freq":    5,
    "min_child_samples": 30,
    "reg_alpha":       0.1,              # L1 regularization
    "reg_lambda":      1.0,             # L2 regularization
    "n_jobs":          -1,
    "verbose":         -1,
    "random_state":    42,
}

EARLY_STOP_ROUNDS = 80
TRAIN_END  = pd.Timestamp("2025-01-01")
VAL_START  = pd.Timestamp("2025-01-01")
VAL_END    = pd.Timestamp("2025-07-01")


# ─── HELPER FUNCTIONS ─────────────────────────────────────────────────────────
def safe_metrics(y_true, y_pred):
    """Compute RMSE, MAE, R² safely ignoring NaN pairs."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask   = (~np.isnan(y_true)) & (~np.isnan(y_pred))
    if mask.sum() == 0:
        return {"rmse": np.nan, "mae": np.nan, "r2": np.nan}
    yt, yp   = y_true[mask], y_pred[mask]
    rmse     = float(np.sqrt(np.mean((yt - yp) ** 2)))
    mae      = float(np.mean(np.abs(yt - yp)))
    ss_res   = np.sum((yt - yp) ** 2)
    ss_tot   = np.sum((yt - yt.mean()) ** 2)
    r2       = float(1.0 - ss_res / (ss_tot + 1e-12))
    return {"rmse": round(rmse, 3), "mae": round(mae, 3), "r2": round(r2, 4)}


def persistence_metrics(y_true, y_true_lag1):
    """Compute persistence baseline metrics: ŷ_{t+h} = y_t (current value)."""
    return safe_metrics(y_true, y_true_lag1)


# ─── LOAD DATA ────────────────────────────────────────────────────────────────
print("[LGB] Loading engineered features …")
df = pd.read_parquet(FE_PATH)
df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"])
df = df.sort_values(["station_id", "timestamp_utc"]).reset_index(drop=True)
print(f"[LGB] Loaded {len(df):,} rows × {df.shape[1]} columns")

# ─── IDENTIFY FEATURE COLUMNS ─────────────────────────────────────────────────
# Exclude metadata, raw targets, and horizon-specific target columns
exclude_prefixes = ["OZONE_ground_lag_", "OZONE_ground_roll_",
                    "NO2_ground_lag_",   "NO2_ground_roll_"]
all_feature_cols = [
    c for c in df.columns
    if c not in META_COLS + TARGET_RAW
    and not any(c.startswith(p) for p in exclude_prefixes)
]
print(f"[LGB] Base feature count (excluding lag targets): {len(all_feature_cols)}")

# Lag/rolling feature names for each target
def get_lag_cols(target):
    return [c for c in df.columns if c.startswith(f"{target}_lag_") or
            c.startswith(f"{target}_roll_")]

# ─── TRAIN/VAL/TEST SPLIT ─────────────────────────────────────────────────────
train_mask = df["timestamp_utc"] < TRAIN_END
val_mask   = (df["timestamp_utc"] >= VAL_START) & (df["timestamp_utc"] < VAL_END)
test_mask  = df["timestamp_utc"] >= VAL_END

# ─── EXPERIMENT LOG ───────────────────────────────────────────────────────────
exp_log = []

# ─── MAIN TRAINING LOOP ───────────────────────────────────────────────────────
all_results = []

for target in TARGETS:
    target_short = "O3" if "OZONE" in target else "NO2"

    # Feature columns = base features + lag/rolling features of THIS target
    # (using the OTHER target's lags as cross-pollutant predictors is also valid)
    feature_cols = all_feature_cols + get_lag_cols(target) + get_lag_cols(
        "NO2_ground" if "OZONE" in target else "OZONE_ground"
    )
    feature_cols = list(dict.fromkeys(feature_cols))  # deduplicate

    for horizon in HORIZONS:
        print(f"\n[LGB] Training {target_short} horizon t+{horizon}h …")

        # Build target shifted h steps into the future (per station)
        target_col = f"{target}_h{horizon}"
        df[target_col] = df.groupby("station_id")[target].shift(-horizon)

        # Apply log1p transform (handles right-skew and stabilises gradients)
        y = np.log1p(np.clip(df[target_col], 0, None))

        X = df[feature_cols].copy()

        # --- Train / Val splits ---
        X_train, y_train = X[train_mask].copy(), y[train_mask].copy()
        X_val,   y_val   = X[val_mask].copy(),   y[val_mask].copy()
        X_test,  y_test  = X[test_mask].copy(),  y[test_mask].copy()

        # Remove rows where target is NaN (future target unavailable)
        train_valid = ~y_train.isna()
        val_valid   = ~y_val.isna()
        test_valid  = ~y_test.isna()

        X_train, y_train = X_train[train_valid], y_train[train_valid]
        X_val,   y_val   = X_val[val_valid],     y_val[val_valid]
        X_test,  y_test  = X_test[test_valid],   y_test[test_valid]

        print(f"   Train: {len(X_train):,} | Val: {len(X_val):,} | Test: {len(X_test):,}")

        # --- Fit LightGBM ---
        model = lgb.LGBMRegressor(**LGB_PARAMS)
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            callbacks=[
                lgb.early_stopping(EARLY_STOP_ROUNDS, verbose=False),
                lgb.log_evaluation(period=500),
            ],
        )

        # --- Evaluate on Val ---
        val_pred_log   = model.predict(X_val)
        val_pred_orig  = np.expm1(np.clip(val_pred_log, 0, None))
        val_true_orig  = np.expm1(np.clip(y_val.values, 0, None))
        val_metrics    = safe_metrics(val_true_orig, val_pred_orig)

        # --- Evaluate on Test ---
        test_pred_log  = model.predict(X_test)
        test_pred_orig = np.expm1(np.clip(test_pred_log, 0, None))
        test_true_orig = np.expm1(np.clip(y_test.values, 0, None))
        test_metrics   = safe_metrics(test_true_orig, test_pred_orig)

        # --- Persistence Baseline ---
        # Persistence: predict current y_t value for future y_{t+h}
        lag1_col = f"{target}_lag_1h"
        if lag1_col in df.columns:
            pers_true  = test_true_orig
            pers_pred  = df.loc[test_mask, lag1_col].loc[test_valid].values
            pers_valid = ~np.isnan(pers_pred)
            pers_metrics = safe_metrics(pers_true[pers_valid], pers_pred[pers_valid])
        else:
            pers_metrics = {"rmse": np.nan, "mae": np.nan, "r2": np.nan}

        delta_r2 = round(test_metrics["r2"] - pers_metrics["r2"], 4) if not np.isnan(pers_metrics["r2"]) else np.nan
        best_iter = getattr(model, "best_iteration_", model.n_estimators)

        print(f"   Val   R²={val_metrics['r2']:.4f}  RMSE={val_metrics['rmse']:.2f}")
        print(f"   Test  R²={test_metrics['r2']:.4f}  RMSE={test_metrics['rmse']:.2f}")
        print(f"   Pers  R²={pers_metrics['r2']:.4f}  ΔR²={delta_r2}")
        print(f"   Best iteration: {best_iter}")

        # --- Save model ---
        model_name = f"{target_short}_h{horizon}.pkl"
        model_path = os.path.join(MODEL_DIR, model_name)
        with open(model_path, "wb") as f:
            pickle.dump({
                "model":        model,
                "feature_cols": feature_cols,
                "target":       target,
                "target_short": target_short,
                "horizon":      horizon,
                "train_period": "2023-01-01 to 2024-12-31",
                "test_period":  "2025-07-01 to 2025-12-31",
                "val_metrics":  val_metrics,
                "test_metrics": test_metrics,
                "pers_metrics": pers_metrics,
                "delta_r2":     delta_r2,
                "lgb_params":   LGB_PARAMS,
                "trained_at":   datetime.now().isoformat(),
            }, f)
        print(f"   → Saved: {model_name}")

        # Log results
        row = {
            "experiment_id":   f"lgb_{target_short}_h{horizon}",
            "model":           "LightGBM",
            "pollutant":       target_short,
            "horizon":         horizon,
            "feature_version": "v1.0",
            "train_rows":      len(X_train),
            "val_r2":          val_metrics["r2"],
            "val_rmse":        val_metrics["rmse"],
            "test_r2":         test_metrics["r2"],
            "test_rmse":       test_metrics["rmse"],
            "test_mae":        test_metrics["mae"],
            "pers_r2":         pers_metrics["r2"],
            "delta_r2":        delta_r2,
            "best_iteration":  best_iter,
            "trained_at":      datetime.now().isoformat(),
        }
        all_results.append(row)
        exp_log.append(row)

        # Cleanup shifted target column
        df.drop(columns=[target_col], inplace=True)

# ─── SAVE RESULTS ─────────────────────────────────────────────────────────────
results_df = pd.DataFrame(all_results)
results_path = os.path.join(OUT_METRICS, "lightgbm_evaluation_summary.csv")
results_df.to_csv(results_path, index=False)
print(f"\n[LGB] → Saved evaluation summary: {results_path}")

exp_log_path = os.path.join(EXP_DIR, "experiment_log.csv")
exp_df = pd.DataFrame(exp_log)
if os.path.exists(exp_log_path):
    existing = pd.read_csv(exp_log_path)
    exp_df = pd.concat([existing, exp_df], ignore_index=True)
exp_df.to_csv(exp_log_path, index=False)
print(f"[LGB] → Updated experiment log: {exp_log_path}")

# ─── SUMMARY TABLE ────────────────────────────────────────────────────────────
print("\n[LGB] ═══════════ RESULTS SUMMARY ═══════════")
print(f"{'Model':<12} {'Pollutant':<8} {'Horizon':<10} {'Test R²':<10} {'Pers R²':<10} {'ΔR²':<8} {'RMSE'}")
print("─" * 70)
for row in all_results:
    print(f"{'LightGBM':<12} {row['pollutant']:<8} t+{row['horizon']}h{'':<7} "
          f"{row['test_r2']:<10.4f} {row['pers_r2']:<10.4f} "
          f"{str(row['delta_r2']):<8} {row['test_rmse']:.3f}")

print()
print("[LGB] ✅ LIGHTGBM TRAINING COMPLETE")
print(f"[LGB] Models saved to: {MODEL_DIR}")
