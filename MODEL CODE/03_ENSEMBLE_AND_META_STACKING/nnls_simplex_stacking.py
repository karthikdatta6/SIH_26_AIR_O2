"""
scripts/phase3/05_ensemble_stacking.py
SIH 25178 — Phase 3 Step 5: Fast Batched NNLS Simplex Stacking Meta-Learner
Combines LightGBM + Deep Learning predictions using Non-Negative Least Squares (GPU Batched)
Saves: models/ensemble/stacker_{pollutant}_h{horizon}.pkl
Run: python scripts/phase3/05_ensemble_stacking.py
"""

import os
import pickle
import warnings
import numpy as np
import pandas as pd
from scipy.optimize import nnls
from datetime import datetime

warnings.filterwarnings("ignore")

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import TensorDataset, DataLoader
    TORCH_AVAILABLE = True
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
except ImportError:
    TORCH_AVAILABLE = False
    DEVICE = "cpu"

# ─── PATHS ────────────────────────────────────────────────────────────────────
ROOT       = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FE_PATH    = os.path.join(ROOT, "data", "phase3", "features_engineered.parquet")
LGB_DIR    = os.path.join(ROOT, "models", "lightgbm")
DL_DIR     = os.path.join(ROOT, "models", "deep_learning")
STACK_DIR  = os.path.join(ROOT, "models", "ensemble")
OUT_METRICS = os.path.join(ROOT, "results", "metrics")
os.makedirs(STACK_DIR, exist_ok=True)
os.makedirs(OUT_METRICS, exist_ok=True)

# ─── CONSTANTS ────────────────────────────────────────────────────────────────
TARGETS   = ["OZONE_ground", "NO2_ground"]
HORIZONS  = [1, 3, 6, 12, 24, 48]
SEQ_LEN   = 24
BATCH_SIZE = 2048
NUM_STATIONS = 10
EMBED_DIM    = 8

VAL_START  = pd.Timestamp("2025-01-01")
VAL_END    = pd.Timestamp("2025-07-01")
TEST_START = pd.Timestamp("2025-07-01")


# ─── NEURAL NETWORK DEFINITION ────────────────────────────────────────────────
if TORCH_AVAILABLE:
    class TemporalResNet(nn.Module):
        def __init__(self, num_features, num_stations=NUM_STATIONS, embed_dim=EMBED_DIM,
                     hidden_size=64, num_layers=2, num_heads=4, dropout=0.15):
            super().__init__()
            self.station_embedding = nn.Embedding(num_stations, embed_dim)
            in_dim = num_features + embed_dim
            self.input_proj = nn.Linear(in_dim, hidden_size)
            self.gru = nn.GRU(
                input_size=hidden_size, hidden_size=hidden_size,
                num_layers=num_layers, batch_first=True,
                bidirectional=True, dropout=dropout if num_layers > 1 else 0.0,
            )
            self.attn = nn.MultiheadAttention(
                embed_dim=hidden_size * 2, num_heads=num_heads,
                dropout=dropout, batch_first=True,
            )
            self.norm = nn.LayerNorm(hidden_size * 2)
            self.head = nn.Sequential(
                nn.Linear(hidden_size * 2, 64),
                nn.GELU(),
                nn.Dropout(dropout),
                nn.Linear(64, 32),
                nn.GELU(),
                nn.Linear(32, 1),
            )

        def forward(self, x_seq, station_enc):
            B, T, F = x_seq.shape
            emb = self.station_embedding(station_enc).unsqueeze(1).expand(B, T, -1)
            x = torch.cat([x_seq, emb], dim=-1)
            x = self.input_proj(x)
            gru_out, _ = self.gru(x)
            attn_out, _ = self.attn(gru_out, gru_out, gru_out)
            out = self.norm(gru_out + attn_out)
            repr_vec = (out[:, -1, :] + out.mean(dim=1)) / 2.0
            return self.head(repr_vec).squeeze(-1)


# ─── FAST BATCHED INFERENCE FUNCTION ──────────────────────────────────────────
def get_dl_preds_batched(subset_df, subset_mask, net, dl_feats, scaler_mean, scaler_scale):
    """
    Blazing-fast GPU batched inference for Deep Learning models.
    Processes tens of thousands of hourly sequences in milliseconds.
    """
    all_seqs = []
    all_sts  = []

    for st_id in subset_df["station_id"].unique():
        sub = subset_df[subset_df["station_id"] == st_id].sort_values("timestamp_utc")
        st_enc = int(sub["station_enc"].iloc[0])

        X_arr = sub[dl_feats].fillna(0.0).values
        X_scaled = ((X_arr - scaler_mean) / (scaler_scale + 1e-8)).astype(np.float32)

        # Pad with first row for sequence warmup
        pad_seq = np.pad(X_scaled, ((SEQ_LEN - 1, 0), (0, 0)), mode="edge")

        sub_mask = subset_mask[subset_df["station_id"] == st_id].values
        valid_indices = np.where(sub_mask)[0]

        for i in valid_indices:
            all_seqs.append(pad_seq[i : i + SEQ_LEN])
            all_sts.append(st_enc)

    if not all_seqs:
        return np.array([])

    X_tensor  = torch.tensor(np.array(all_seqs), dtype=torch.float32)
    st_tensor = torch.tensor(all_sts, dtype=torch.long)

    ds = TensorDataset(X_tensor, st_tensor)
    dl = DataLoader(ds, batch_size=BATCH_SIZE, shuffle=False)

    net = net.to(DEVICE)
    net.eval()
    preds = []
    with torch.no_grad():
        for bx, bst in dl:
            bx, bst = bx.to(DEVICE), bst.to(DEVICE)
            p = net(bx, bst).cpu().numpy()
            preds.extend(p)

    return np.expm1(np.clip(np.array(preds), 0, None))


# ─── HELPER ───────────────────────────────────────────────────────────────────
def safe_metrics(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask   = (~np.isnan(y_true)) & (~np.isnan(y_pred))
    if mask.sum() < 2:
        return {"rmse": np.nan, "mae": np.nan, "r2": np.nan}
    yt, yp = y_true[mask], y_pred[mask]
    rmse   = float(np.sqrt(np.mean((yt - yp) ** 2)))
    mae    = float(np.mean(np.abs(yt - yp)))
    ss_res = np.sum((yt - yp) ** 2)
    ss_tot = np.sum((yt - yt.mean()) ** 2)
    r2     = float(1.0 - ss_res / (ss_tot + 1e-12))
    return {"rmse": round(rmse, 3), "mae": round(mae, 3), "r2": round(r2, 4)}


# ─── LOAD DATA ────────────────────────────────────────────────────────────────
print(f"[STACK] Loading engineered features (Device: {DEVICE}) …")
df = pd.read_parquet(FE_PATH)
df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"])
df = df.sort_values(["station_id", "timestamp_utc"]).reset_index(drop=True)

val_df  = df[(df["timestamp_utc"] >= VAL_START) & (df["timestamp_utc"] < VAL_END)].copy()
test_df = df[df["timestamp_utc"] >= TEST_START].copy()

all_results = []

# ─── MAIN STACKING LOOP ───────────────────────────────────────────────────────
for target in TARGETS:
    target_short = "O3" if "OZONE" in target else "NO2"

    for horizon in HORIZONS:
        print(f"\n[STACK] Processing {target_short} t+{horizon}h …")

        # ── Load LightGBM model ──
        lgb_path = os.path.join(LGB_DIR, f"{target_short}_h{horizon}.pkl")
        if not os.path.exists(lgb_path):
            print(f"   [SKIP] LightGBM model not found: {lgb_path}")
            continue

        with open(lgb_path, "rb") as f:
            lgb_bundle = pickle.load(f)

        lgb_model = lgb_bundle["model"]
        lgb_feats = lgb_bundle["feature_cols"]

        # Shift target h steps forward to get ground truth
        y_val_raw  = val_df.groupby("station_id")[target].shift(-horizon)
        y_test_raw = test_df.groupby("station_id")[target].shift(-horizon)

        val_mask  = ~y_val_raw.isna()
        test_mask = ~y_test_raw.isna()

        # LightGBM predictions
        lgb_val_pred  = np.expm1(np.clip(lgb_model.predict(val_df.loc[val_mask, lgb_feats]), 0, None))
        lgb_test_pred = np.expm1(np.clip(lgb_model.predict(test_df.loc[test_mask, lgb_feats]), 0, None))

        y_val_true  = np.clip(y_val_raw[val_mask].values, 0, None)
        y_test_true = np.clip(y_test_raw[test_mask].values, 0, None)

        # ── Fast GPU Batched Deep Learning Predictions ──
        dl_path = os.path.join(DL_DIR, f"bilstm_{target_short}_h{horizon}.pt")
        dl_val_pred  = None
        dl_test_pred = None

        if TORCH_AVAILABLE and os.path.exists(dl_path):
            try:
                ckpt = torch.load(dl_path, map_location=DEVICE, weights_only=False)
                dl_feats     = ckpt["feature_cols"]
                scaler_mean  = ckpt["scaler_mean"]
                scaler_scale = ckpt["scaler_scale"]

                net = TemporalResNet(num_features=len(dl_feats))
                net.load_state_dict(ckpt["model_state_dict"])

                dl_val_pred  = get_dl_preds_batched(val_df, val_mask, net, dl_feats, scaler_mean, scaler_scale)
                dl_test_pred = get_dl_preds_batched(test_df, test_mask, net, dl_feats, scaler_mean, scaler_scale)
            except Exception as e:
                print(f"   DL inference note: {e}")

        # ── Fit NNLS Simplex Meta-Learner ──
        if dl_val_pred is not None and len(dl_val_pred) == len(lgb_val_pred):
            oof_matrix = np.column_stack([lgb_val_pred, dl_val_pred])
            weights_raw, residual = nnls(oof_matrix, y_val_true)
            weights = weights_raw / (np.sum(weights_raw) + 1e-12)
            ensemble_test = weights[0] * lgb_test_pred + weights[1] * dl_test_pred
            model_order = ["lightgbm", "bilstm_attention"]
        else:
            weights = np.array([1.0])
            ensemble_test = lgb_test_pred
            model_order = ["lightgbm"]

        print(f"   NNLS Stacking weights: {[round(float(w), 4) for w in weights]}")

        # ── Evaluate ──
        test_metrics = safe_metrics(y_test_true, ensemble_test)
        lgb_metrics  = safe_metrics(y_test_true, lgb_test_pred)

        # Persistence baseline
        lag_col = f"{target}_lag_1h"
        if lag_col in test_df.columns:
            pers_pred  = test_df.loc[test_mask, lag_col].values
            pers_valid = ~np.isnan(pers_pred)
            pers_metrics = safe_metrics(y_test_true[pers_valid], pers_pred[pers_valid])
        else:
            pers_metrics = {"rmse": np.nan, "mae": np.nan, "r2": np.nan}

        delta_r2 = round(test_metrics["r2"] - pers_metrics.get("r2", np.nan), 4)

        print(f"   LGB    R²={lgb_metrics['r2']:.4f}  RMSE={lgb_metrics['rmse']:.2f}")
        print(f"   ENSEMB R²={test_metrics['r2']:.4f}  RMSE={test_metrics['rmse']:.2f}")
        print(f"   PERS   R²={pers_metrics['r2']:.4f}  ΔR²={delta_r2}")

        # ── Save stacker bundle ──
        stacker_bundle = {
            "weights":          weights,
            "model_order":      model_order,
            "lgb_feature_cols": lgb_feats,
            "target":           target,
            "target_short":     target_short,
            "horizon":          horizon,
            "test_metrics":     test_metrics,
            "pers_metrics":     pers_metrics,
            "delta_r2":         delta_r2,
            "trained_at":       datetime.now().isoformat(),
        }
        stacker_path = os.path.join(STACK_DIR, f"stacker_{target_short}_h{horizon}.pkl")
        with open(stacker_path, "wb") as f:
            pickle.dump(stacker_bundle, f)
        print(f"   → Saved: stacker_{target_short}_h{horizon}.pkl")

        all_results.append({
            "experiment_id": f"ensemble_{target_short}_h{horizon}",
            "model":         "NNLS_Ensemble",
            "pollutant":     target_short,
            "horizon":       horizon,
            "test_r2":       test_metrics["r2"],
            "test_rmse":     test_metrics["rmse"],
            "test_mae":      test_metrics["mae"],
            "pers_r2":       pers_metrics["r2"],
            "delta_r2":      delta_r2,
            "nnls_weights":  str([round(float(w), 4) for w in weights]),
            "trained_at":    datetime.now().isoformat(),
        })

# ─── SAVE SUMMARY ─────────────────────────────────────────────────────────────
if all_results:
    results_df = pd.DataFrame(all_results)
    results_df.to_csv(os.path.join(OUT_METRICS, "ensemble_evaluation_summary.csv"), index=False)
    print(f"\n[STACK] → Saved ensemble_evaluation_summary.csv")

print("\n[STACK] ✅ ENSEMBLE STACKING COMPLETE")
