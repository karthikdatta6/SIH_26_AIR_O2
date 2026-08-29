"""
scripts/phase3/00_eda_analysis.py
SIH 25178 — Phase 3 Step 0: Exploratory Data Analysis
Generates: reports/phase3_eda/ (CSV reports + PNG charts)
Run: python scripts/phase3/00_eda_analysis.py
"""

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

warnings.filterwarnings("ignore")

# ─── PATHS ────────────────────────────────────────────────────────────────────
ROOT       = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_PATH  = os.path.join(ROOT, "data", "fused", "station_hourly_fused.parquet")
OUT_DIR    = os.path.join(ROOT, "reports", "phase3_eda")
os.makedirs(OUT_DIR, exist_ok=True)

# ─── LOAD ──────────────────────────────────────────────────────────────────────
print("[EDA] Loading master dataset …")
df = pd.read_parquet(DATA_PATH)
df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"])

assert len(df) == 263040, f"Expected 263,040 rows, got {len(df)}"
print(f"[EDA] Loaded {len(df):,} rows × {df.shape[1]} columns")

TARGETS    = ["OZONE_ground", "NO2_ground"]
STATIONS   = sorted(df["station_id"].unique())
print(f"[EDA] Stations ({len(STATIONS)}): {STATIONS}")

# ─── 1. TARGET DISTRIBUTION REPORT ────────────────────────────────────────────
print("[EDA] 1/5 — Target distributions …")
rows = []
for tgt in TARGETS:
    s = df[tgt].dropna()
    rows.append({
        "pollutant": tgt,
        "count":     int(s.count()),
        "missing":   int(df[tgt].isna().sum()),
        "missing_pct": round(df[tgt].isna().mean() * 100, 2),
        "mean":      round(float(s.mean()), 3),
        "median":    round(float(s.median()), 3),
        "std":       round(float(s.std()), 3),
        "min":       round(float(s.min()), 3),
        "p5":        round(float(s.quantile(0.05)), 3),
        "p25":       round(float(s.quantile(0.25)), 3),
        "p75":       round(float(s.quantile(0.75)), 3),
        "p95":       round(float(s.quantile(0.95)), 3),
        "p99":       round(float(s.quantile(0.99)), 3),
        "max":       round(float(s.max()), 3),
        "skewness":  round(float(s.skew()), 4),
        "kurtosis":  round(float(s.kurt()), 4),
    })
pd.DataFrame(rows).to_csv(os.path.join(OUT_DIR, "target_distribution.csv"), index=False)
print("   → target_distribution.csv saved")

# Plot target distributions
fig, axes = plt.subplots(2, 2, figsize=(14, 8))
for i, tgt in enumerate(TARGETS):
    s = df[tgt].dropna()
    axes[i][0].hist(s, bins=80, color="#3b82f6", edgecolor="none", alpha=0.8)
    axes[i][0].set_title(f"{tgt} — Raw Distribution")
    axes[i][0].set_xlabel("µg/m³")
    axes[i][0].set_ylabel("Frequency")
    axes[i][1].hist(np.log1p(s), bins=80, color="#10b981", edgecolor="none", alpha=0.8)
    axes[i][1].set_title(f"{tgt} — log1p Transformed")
    axes[i][1].set_xlabel("log1p(µg/m³)")
    axes[i][1].set_ylabel("Frequency")
plt.suptitle("Target Variable Distributions (Raw vs log1p)", fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "target_distributions.png"), dpi=150)
plt.close()
print("   → target_distributions.png saved")

# ─── 2. MISSINGNESS REPORT ─────────────────────────────────────────────────────
print("[EDA] 2/5 — Missingness analysis …")
miss_rows = []
for col in df.columns:
    miss_rows.append({
        "column":      col,
        "missing_n":   int(df[col].isna().sum()),
        "missing_pct": round(df[col].isna().mean() * 100, 2),
        "dtype":       str(df[col].dtype),
    })
miss_df = pd.DataFrame(miss_rows).sort_values("missing_pct", ascending=False)
miss_df.to_csv(os.path.join(OUT_DIR, "missingness.csv"), index=False)
print("   → missingness.csv saved")

# ─── 3. STATION STATISTICS ─────────────────────────────────────────────────────
print("[EDA] 3/5 — Station statistics …")
st_rows = []
for station in STATIONS:
    sub = df[df["station_id"] == station]
    for tgt in TARGETS:
        s = sub[tgt].dropna()
        st_rows.append({
            "station_id":  station,
            "pollutant":   tgt,
            "n_valid":     int(s.count()),
            "missing_pct": round(sub[tgt].isna().mean() * 100, 2),
            "mean":        round(float(s.mean()), 3) if len(s) else np.nan,
            "median":      round(float(s.median()), 3) if len(s) else np.nan,
            "std":         round(float(s.std()), 3) if len(s) else np.nan,
            "p95":         round(float(s.quantile(0.95)), 3) if len(s) else np.nan,
            "max":         round(float(s.max()), 3) if len(s) else np.nan,
        })
pd.DataFrame(st_rows).to_csv(os.path.join(OUT_DIR, "station_statistics.csv"), index=False)
print("   → station_statistics.csv saved")

# Plot station mean concentrations
fig, axes = plt.subplots(1, 2, figsize=(16, 6))
for i, tgt in enumerate(TARGETS):
    sub = pd.DataFrame(st_rows)[pd.DataFrame(st_rows)["pollutant"] == tgt]
    axes[i].barh(sub["station_id"], sub["mean"], color="#6366f1", alpha=0.85)
    axes[i].set_title(f"Mean {tgt} by Station (µg/m³)")
    axes[i].set_xlabel("Mean Concentration (µg/m³)")
plt.suptitle("Per-Station Mean Pollutant Concentrations", fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "station_mean_concentrations.png"), dpi=150)
plt.close()
print("   → station_mean_concentrations.png saved")

# ─── 4. HOURLY STATISTICS (DIURNAL PATTERNS) ──────────────────────────────────
print("[EDA] 4/5 — Hourly statistics …")
df["hour"] = df["timestamp_utc"].dt.hour
hourly = []
for tgt in TARGETS:
    h = (df.groupby("hour")[tgt]
           .agg(["mean", "median", "std"])
           .reset_index())
    h["pollutant"] = tgt
    h.columns = ["hour", "mean", "median", "std", "pollutant"]
    hourly.append(h)
hourly_df = pd.concat(hourly, ignore_index=True)
hourly_df.to_csv(os.path.join(OUT_DIR, "hourly_statistics.csv"), index=False)
print("   → hourly_statistics.csv saved")

# Plot diurnal cycle
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
for i, tgt in enumerate(TARGETS):
    sub = hourly_df[hourly_df["pollutant"] == tgt]
    axes[i].plot(sub["hour"], sub["mean"], color="#3b82f6", lw=2, label="Mean")
    axes[i].fill_between(sub["hour"],
                         sub["mean"] - sub["std"],
                         sub["mean"] + sub["std"],
                         alpha=0.2, color="#3b82f6")
    axes[i].set_title(f"Diurnal Cycle — {tgt}")
    axes[i].set_xlabel("Hour of Day (UTC)")
    axes[i].set_ylabel("µg/m³")
    axes[i].set_xticks(range(0, 24, 3))
plt.suptitle("Hourly (Diurnal) Patterns", fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "diurnal_patterns.png"), dpi=150)
plt.close()
print("   → diurnal_patterns.png saved")

# ─── 5. MONTHLY STATISTICS (SEASONAL PATTERNS) ────────────────────────────────
print("[EDA] 5/5 — Monthly statistics …")
df["month"] = df["timestamp_utc"].dt.month
monthly_rows = []
for tgt in TARGETS:
    m = (df.groupby("month")[tgt]
           .agg(["mean", "median", "std"])
           .reset_index())
    m["pollutant"] = tgt
    m.columns = ["month", "mean", "median", "std", "pollutant"]
    monthly_rows.append(m)
monthly_df = pd.concat(monthly_rows, ignore_index=True)
monthly_df.to_csv(os.path.join(OUT_DIR, "monthly_statistics.csv"), index=False)
print("   → monthly_statistics.csv saved")

# Plot seasonal cycle
month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
for i, tgt in enumerate(TARGETS):
    sub = monthly_df[monthly_df["pollutant"] == tgt]
    axes[i].bar(sub["month"], sub["mean"], color="#f59e0b", alpha=0.85)
    axes[i].set_title(f"Seasonal Cycle — {tgt}")
    axes[i].set_xlabel("Month")
    axes[i].set_ylabel("Mean µg/m³")
    axes[i].set_xticks(range(1, 13))
    axes[i].set_xticklabels(month_names, rotation=45)
plt.suptitle("Monthly (Seasonal) Patterns", fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "seasonal_patterns.png"), dpi=150)
plt.close()
print("   → seasonal_patterns.png saved")

print()
print("[EDA] ✅ ALL EDA REPORTS COMPLETE")
print(f"[EDA] Output folder: {OUT_DIR}")
