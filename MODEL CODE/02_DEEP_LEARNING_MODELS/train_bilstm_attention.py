"""
scripts/phase3/04_train_deep_learning.py
SIH 25178 — Phase 3 Step 4: Deep Learning Model with Feature Normalization
Uses PyTorch with CUDA acceleration (RTX 4050 Laptop GPU).
Saves: models/deep_learning/bilstm_{pollutant}_h{horizon}.pt
Run: python scripts/phase3/04_train_deep_learning.py
"""

import os
import json
import pickle
import warnings
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    TORCH_AVAILABLE = True
    print(f"[DL] PyTorch {torch.__version__} loaded")
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[DL] Using device: {DEVICE}")
    if torch.cuda.is_available():
        print(f"[DL] GPU: {torch.cuda.get_device_name(0)}")
        print(f"[DL] GPU VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
except ImportError:
    print("[DL] PyTorch not installed.")
    TORCH_AVAILABLE = False

# ─── PATHS ────────────────────────────────────────────────────────────────────
ROOT       = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FE_PATH    = os.path.join(ROOT, "data", "phase3", "features_engineered.parquet")
MODEL_DIR  = os.path.join(ROOT, "models", "deep_learning")
OUT_METRICS = os.path.join(ROOT, "results", "metrics")
EXP_DIR    = os.path.join(ROOT, "experiments")
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(OUT_METRICS, exist_ok=True)

# ─── CONSTANTS ────────────────────────────────────────────────────────────────
TARGETS    = ["OZONE_ground", "NO2_ground"]
HORIZONS   = [1, 3, 6, 12, 24, 48]
SEQ_LEN    = 24        # 24-hour lookback window (captures full diurnal cycle)
BATCH_SIZE = 512
MAX_EPOCHS = 25
PATIENCE   = 5
LR         = 3e-3
WEIGHT_DECAY = 1e-4
NUM_STATIONS = 10
EMBED_DIM    = 8

TRAIN_END  = pd.Timestamp("2025-01-01")
VAL_START  = pd.Timestamp("2025-01-01")
VAL_END    = pd.Timestamp("2025-07-01")

META_COLS  = ["timestamp_utc", "station_id"]
TARGET_RAW = ["OZONE_ground", "NO2_ground"]


# ─── DATASET CLASS ────────────────────────────────────────────────────────────
class ScaledSequenceDataset(Dataset):
    """
    Produces (X_sequence, station_enc, y_log) triplets from pre-scaled features.
    """
    def __init__(self, station_chunks, seq_len=SEQ_LEN):
        self.samples = []
        for X_scaled, station_enc, y_future_log in station_chunks:
            T = len(X_scaled)
            for i in range(seq_len, T):
                y_val = y_future_log[i]
                if np.isnan(y_val):
                    continue
                X_seq = X_scaled[i - seq_len: i]  # shape: (SEQ_LEN, num_features)
                self.samples.append((X_seq, station_enc, y_val))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        X_seq, station_enc, y_val = self.samples[idx]
        return (
            torch.tensor(X_seq, dtype=torch.float32),
            torch.tensor(station_enc, dtype=torch.long),
            torch.tensor(y_val, dtype=torch.float32),
        )


# ─── MODEL ARCHITECTURE ───────────────────────────────────────────────────────
class TemporalResNet(nn.Module):
    """
    BiLSTM + Multi-Head Attention + Residual Feedforward Network
    Standardized input + Station Embedding -> GRU/LSTM -> Multihead Attention -> Output
    """
    def __init__(self, num_features, num_stations=NUM_STATIONS, embed_dim=EMBED_DIM,
                 hidden_size=64, num_layers=2, num_heads=4, dropout=0.15):
        super().__init__()
        self.station_embedding = nn.Embedding(num_stations, embed_dim)
        in_dim = num_features + embed_dim

        self.input_proj = nn.Linear(in_dim, hidden_size)
        self.gru = nn.GRU(
            input_size=hidden_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )

        self.attn = nn.MultiheadAttention(
            embed_dim=hidden_size * 2,
            num_heads=num_heads,
            dropout=dropout,
            batch_first=True,
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

        # Context vector from mean pooling + last step
        last_step = out[:, -1, :]
        mean_pool = out.mean(dim=1)
        repr_vec = (last_step + mean_pool) / 2.0

        return self.head(repr_vec).squeeze(-1)


# ─── TRAINING FUNCTION ────────────────────────────────────────────────────────
def train_deep_model(target, horizon, feature_cols, df_train, df_val, df_test):
    target_short = "O3" if "OZONE" in target else "NO2"
    print(f"\n[DL] Training Deep Learning — {target_short} t+{horizon}h …")

    # 1. Fit StandardScaler strictly on TRAIN set only (zero data leakage)
    scaler = StandardScaler()
    X_train_raw = df_train[feature_cols].copy().fillna(0.0).values
    scaler.fit(X_train_raw)

    def prepare_station_chunks(df_subset):
        chunks = []
        for station_id in df_subset["station_id"].unique():
            sub = df_subset[df_subset["station_id"] == station_id].sort_values("timestamp_utc").reset_index(drop=True)
            st_enc = int(sub["station_enc"].iloc[0])

            # Standardize features (fill NaNs with 0.0 before scaling)
            X_raw = sub[feature_cols].fillna(0.0).values
            X_scaled = scaler.transform(X_raw).astype(np.float32)

            # Target shifted forward by horizon
            y_raw = sub[target].values.astype(np.float32)
            y_future = np.full(len(sub), np.nan, dtype=np.float32)
            if len(sub) > horizon:
                y_future[:-horizon] = y_raw[horizon:]

            # log1p target
            y_future_log = np.where(~np.isnan(y_future), np.log1p(np.clip(y_future, 0, None)), np.nan)
            chunks.append((X_scaled, st_enc, y_future_log))
        return chunks

    train_chunks = prepare_station_chunks(df_train)
    val_chunks   = prepare_station_chunks(df_val)
    test_chunks  = prepare_station_chunks(df_test)

    train_ds = ScaledSequenceDataset(train_chunks, seq_len=SEQ_LEN)
    val_ds   = ScaledSequenceDataset(val_chunks,   seq_len=SEQ_LEN)
    test_ds  = ScaledSequenceDataset(test_chunks,  seq_len=SEQ_LEN)

    if len(train_ds) == 0:
        print(f"   [SKIP] No valid training samples for {target_short} h{horizon}")
        return None

    train_dl = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,  num_workers=0, pin_memory=True if torch.cuda.is_available() else False)
    val_dl   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    test_dl  = DataLoader(test_ds,  batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    print(f"   Train samples: {len(train_ds):,} | Val: {len(val_ds):,} | Test: {len(test_ds):,}")

    model = TemporalResNet(num_features=len(feature_cols)).to(DEVICE)
    optimizer = optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=MAX_EPOCHS, eta_min=1e-5)
    criterion = nn.SmoothL1Loss(beta=0.1)

    best_val_loss = float("inf")
    best_state    = None
    patience_ctr  = 0

    for epoch in range(1, MAX_EPOCHS + 1):
        model.train()
        train_losses = []
        for X_seq, st_enc, y_true in train_dl:
            X_seq  = X_seq.to(DEVICE)
            st_enc = st_enc.to(DEVICE)
            y_true = y_true.to(DEVICE)

            optimizer.zero_grad()
            y_pred = model(X_seq, st_enc)
            loss   = criterion(y_pred, y_true)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            train_losses.append(loss.item())

        scheduler.step()

        # Validation
        model.eval()
        val_losses = []
        with torch.no_grad():
            for X_seq, st_enc, y_true in val_dl:
                X_seq  = X_seq.to(DEVICE)
                st_enc = st_enc.to(DEVICE)
                y_true = y_true.to(DEVICE)
                y_pred = model(X_seq, st_enc)
                val_losses.append(criterion(y_pred, y_true).item())

        train_loss = np.mean(train_losses)
        val_loss   = np.mean(val_losses)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_state    = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            patience_ctr  = 0
        else:
            patience_ctr += 1

        if epoch % 5 == 0 or epoch == 1:
            print(f"   Epoch {epoch:>2}/{MAX_EPOCHS} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Best Val: {best_val_loss:.4f}")

        if patience_ctr >= PATIENCE:
            print(f"   Early stopping triggered at epoch {epoch}")
            break

    # Restore best checkpoint
    if best_state is not None:
        model.load_state_dict({k: v.to(DEVICE) for k, v in best_state.items()})

    # Evaluate on Test Set
    model.eval()
    y_true_all, y_pred_all = [], []
    with torch.no_grad():
        for X_seq, st_enc, y_true in test_dl:
            X_seq  = X_seq.to(DEVICE)
            st_enc = st_enc.to(DEVICE)
            y_pred = model(X_seq, st_enc).cpu().numpy()
            y_true_all.extend(y_true.numpy())
            y_pred_all.extend(y_pred)

    y_true_orig = np.expm1(np.clip(np.array(y_true_all), 0, None))
    y_pred_orig = np.expm1(np.clip(np.array(y_pred_all), 0, None))

    mask = (~np.isnan(y_true_orig)) & (~np.isnan(y_pred_orig))
    yt, yp = y_true_orig[mask], y_pred_orig[mask]
    rmse   = float(np.sqrt(np.mean((yt - yp) ** 2)))
    mae    = float(np.mean(np.abs(yt - yp)))
    ss_res = np.sum((yt - yp) ** 2)
    ss_tot = np.sum((yt - yt.mean()) ** 2)
    r2     = float(1.0 - ss_res / (ss_tot + 1e-12))
    print(f"   Test R²={r2:.4f} | RMSE={rmse:.3f} | MAE={mae:.3f}")

    # Save model checkpoint
    model_name = f"bilstm_{target_short}_h{horizon}.pt"
    model_path = os.path.join(MODEL_DIR, model_name)
    torch.save({
        "model_state_dict": best_state,
        "feature_cols":     feature_cols,
        "scaler_mean":      scaler.mean_,
        "scaler_scale":     scaler.scale_,
        "num_features":     len(feature_cols),
        "target":           target,
        "target_short":     target_short,
        "horizon":          horizon,
        "seq_len":          SEQ_LEN,
        "test_r2":          r2,
        "test_rmse":        rmse,
        "test_mae":         mae,
        "trained_at":       datetime.now().isoformat(),
    }, model_path)
    print(f"   → Saved: {model_name}")

    return {"r2": round(r2, 4), "rmse": round(rmse, 3), "mae": round(mae, 3)}


# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not TORCH_AVAILABLE:
        print("[DL] PyTorch not available.")
        exit(0)

    print("[DL] Loading engineered features …")
    df = pd.read_parquet(FE_PATH)
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"])
    df = df.sort_values(["station_id", "timestamp_utc"]).reset_index(drop=True)
    print(f"[DL] Loaded {len(df):,} rows × {df.shape[1]} columns")

    META_EXCL = META_COLS + TARGET_RAW
    feature_cols = [c for c in df.columns if c not in META_EXCL]
    print(f"[DL] Feature count: {len(feature_cols)}")

    train_df = df[df["timestamp_utc"] < TRAIN_END].copy()
    val_df   = df[(df["timestamp_utc"] >= VAL_START) & (df["timestamp_utc"] < VAL_END)].copy()
    test_df  = df[df["timestamp_utc"] >= VAL_END].copy()

    all_results = []
    for target in TARGETS:
        for horizon in HORIZONS:
            result = train_deep_model(target, horizon, feature_cols, train_df, val_df, test_df)
            if result:
                all_results.append({
                    "experiment_id": f"bilstm_{'O3' if 'OZONE' in target else 'NO2'}_h{horizon}",
                    "model":         "BiLSTM+Attention",
                    "pollutant":     "O3" if "OZONE" in target else "NO2",
                    "horizon":       horizon,
                    "test_r2":       result["r2"],
                    "test_rmse":     result["rmse"],
                    "test_mae":      result["mae"],
                    "trained_at":    datetime.now().isoformat(),
                })

    if all_results:
        results_df = pd.DataFrame(all_results)
        results_df.to_csv(os.path.join(OUT_METRICS, "bilstm_evaluation_summary.csv"), index=False)
        print(f"\n[DL] → Saved results to: {OUT_METRICS}/bilstm_evaluation_summary.csv")

    print("\n[DL] ✅ DEEP LEARNING TRAINING COMPLETE")
    import os
    os._exit(0)
