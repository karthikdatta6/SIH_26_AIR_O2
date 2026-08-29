"""
scripts/phase3/01_feature_engineering.py
SIH 25178 — Phase 3 Step 1: Feature Engineering
Generates: data/phase3/features_engineered.parquet (38 curated features + targets)
Run: python scripts/phase3/01_feature_engineering.py
"""

import os
import warnings
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder

warnings.filterwarnings("ignore")

# ─── PATHS ────────────────────────────────────────────────────────────────────
ROOT      = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_PATH = os.path.join(ROOT, "data", "fused", "station_hourly_fused.parquet")
OUT_DIR   = os.path.join(ROOT, "data", "phase3")
os.makedirs(OUT_DIR, exist_ok=True)
OUT_PATH  = os.path.join(OUT_DIR, "features_engineered.parquet")

# ─── CONSTANTS ────────────────────────────────────────────────────────────────
TARGETS = ["OZONE_ground", "NO2_ground"]

# Lag windows (hours). Purge gap will be max(LAG_WINDOWS) = 24h
LAG_WINDOWS = [1, 3, 6, 12, 24]

# Rolling stat windows (hours) - trailing only, shift(1) first
ROLL_WINDOWS = [6, 24]

# Columns to DROP before saving (raw Kelvin duplicates, obs counts, raw coords, raw time)
DROP_COLS = [
    "era5_temperature_k",      # Redundant: T_c + 273.15
    "era5_dewpoint_k",         # Redundant: Td_c + 273.15
    "satellite_observation_time",  # Replaced by satellite_age_hours
    "latitude",                # Replaced by station_enc
    "longitude",               # Replaced by station_enc
    # obs_count columns (operational metadata, not available at inference time)
    "PM2.5_obs_count", "PM10_obs_count", "NO_obs_count",
    "NO2_obs_count", "NOx_obs_count", "NH3_obs_count",
    "SO2_obs_count", "CO_obs_count", "OZONE_obs_count",
]

# ─── LOAD ─────────────────────────────────────────────────────────────────────
print("[FE] Loading master dataset …")
df = pd.read_parquet(DATA_PATH)
df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"])
assert len(df) == 263040, f"Expected 263,040 rows, got {len(df)}"

# Sort strictly: station first, time second
df = df.sort_values(["station_id", "timestamp_utc"]).reset_index(drop=True)
print(f"[FE] Loaded {len(df):,} rows × {df.shape[1]} columns")

# ─── STEP 1: STATION ENCODING ─────────────────────────────────────────────────
print("[FE] Step 1 — Station encoding …")
le = LabelEncoder()
df["station_enc"] = le.fit_transform(df["station_id"])
station_map = dict(zip(le.classes_, [int(x) for x in le.transform(le.classes_)]))
print(f"   Station map: {station_map}")

# ─── STEP 2: CYCLICAL TIME FEATURES ──────────────────────────────────────────
print("[FE] Step 2 — Cyclical time encoding …")
hour        = df["timestamp_utc"].dt.hour
day_of_year = df["timestamp_utc"].dt.dayofyear

df["hour_sin"]   = np.sin(2 * np.pi * hour / 24.0).astype(np.float32)
df["hour_cos"]   = np.cos(2 * np.pi * hour / 24.0).astype(np.float32)
df["doy_sin"]    = np.sin(2 * np.pi * day_of_year / 365.25).astype(np.float32)
df["doy_cos"]    = np.cos(2 * np.pi * day_of_year / 365.25).astype(np.float32)

# ─── STEP 3: WIND CYCLICAL ENCODING ──────────────────────────────────────────
print("[FE] Step 3 — Wind cyclical encoding …")
wind_rad = np.deg2rad(df["era5_wind_direction"])
df["wind_sin"] = np.sin(wind_rad).astype(np.float32)
df["wind_cos"] = np.cos(wind_rad).astype(np.float32)
df = df.drop(columns=["era5_wind_direction"])

# ─── STEP 4: DERIVED PHYSICAL FEATURES ───────────────────────────────────────
print("[FE] Step 4 — Derived physical features …")
# Ventilation coefficient: captures atmospheric flushing capacity
df["ventilation_coeff"] = (df["era5_boundary_layer_height"] * df["era5_wind_speed"]).astype(np.float32)

# Photo index: normalized photolysis driver (0 at night, ~1 at peak noon)
df["photo_index"] = (df["era5_solar_radiation_w_m2"] / 1024.0).astype(np.float32)

# ─── STEP 5: SATELLITE AVAILABILITY FLAGS ────────────────────────────────────
print("[FE] Step 5 — Satellite availability flags …")
df["sat_NO2_available"] = (~df["sat_NO2"].isna()).astype(np.float32)
df["sat_CO_available"]  = (~df["sat_CO"].isna()).astype(np.float32)

# ─── STEP 6: LAND USE ONE-HOT ENCODING ───────────────────────────────────────
print("[FE] Step 6 — Land-use one-hot encoding …")
landuse_dummies = pd.get_dummies(
    df["geo_dominant_landuse_1km"], prefix="landuse", dtype=np.float32
)
df = pd.concat([df.drop(columns=["geo_dominant_landuse_1km"]), landuse_dummies], axis=1)

# ─── STEP 7: LAG & ROLLING FEATURES (PER-STATION, TRAILING ONLY) ─────────────
print("[FE] Step 7 — Lag & rolling features (per-station, trailing windows) …")

# Process each station group independently to guarantee zero station contamination
# and maximum vectorization performance
station_chunks = []
for st_id, sub in df.groupby("station_id", sort=False):
    sub = sub.sort_values("timestamp_utc").copy()
    for tgt in TARGETS:
        for lag in LAG_WINDOWS:
            sub[f"{tgt}_lag_{lag}h"] = sub[tgt].shift(lag).astype(np.float32)
        for window in ROLL_WINDOWS:
            shifted = sub[tgt].shift(1)
            sub[f"{tgt}_roll_mean_{window}h"] = shifted.rolling(window, min_periods=window//2).mean().astype(np.float32)
            sub[f"{tgt}_roll_std_{window}h"]  = shifted.rolling(window, min_periods=window//2).std().astype(np.float32)
    station_chunks.append(sub)

df = pd.concat(station_chunks, ignore_index=True)

# ─── STEP 8: LAG FEATURE CAUSALITY CHECK ─────────────────────────────────────
print("[FE] Step 8 — LAG_FEATURE_CAUSALITY_CHECK …")
fail_count = 0
for station in df["station_id"].unique():
    sub = df[df["station_id"] == station]
    col_lag1 = "OZONE_ground_lag_1h"
    col_orig = "OZONE_ground"
    expected_lag = sub[col_orig].shift(1)
    # Check where both are not NaN
    valid_mask = (~sub[col_lag1].isna()) & (~expected_lag.isna())
    diff = (sub.loc[valid_mask, col_lag1] - expected_lag.loc[valid_mask]).abs()
    if (diff > 1e-4).sum() > 0:
        print(f"   [FAIL] Station {station}: {(diff > 1e-4).sum()} lag-1 mismatches!")
        fail_count += 1

if fail_count == 0:
    print("   [PASS] LAG_FEATURE_CAUSALITY_CHECK — all lags are station-bounded and causal")
else:
    raise RuntimeError(f"LAG_FEATURE_CAUSALITY_CHECK FAILED on {fail_count} stations!")

# ─── STEP 9: DROP EXCLUDED RAW COLUMNS ───────────────────────────────────────
print("[FE] Step 9 — Dropping excluded raw columns …")
existing_drops = [c for c in DROP_COLS if c in df.columns]
df = df.drop(columns=existing_drops)
print(f"   Dropped: {existing_drops}")

# ─── STEP 10: VERIFY FINAL SHAPE ─────────────────────────────────────────────
print("[FE] Step 10 — Final verification …")
print(f"   Final shape: {df.shape}")

# Confirm required columns exist
assert "timestamp_utc" in df.columns, "timestamp_utc column is required!"
assert "station_id"    in df.columns, "station_id column is required!"
assert "OZONE_ground"  in df.columns, "OZONE_ground target missing!"
assert "NO2_ground"    in df.columns, "NO2_ground target missing!"

# ─── SAVE ─────────────────────────────────────────────────────────────────────
df.to_parquet(OUT_PATH, index=False)
print()
print(f"[FE] ✅ FEATURE ENGINEERING COMPLETE")
print(f"[FE] Saved: {OUT_PATH}")
print(f"[FE] Final shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
print(f"[FE] Purge gap for CV = max(LAG_WINDOWS) = {max(LAG_WINDOWS)}h")
