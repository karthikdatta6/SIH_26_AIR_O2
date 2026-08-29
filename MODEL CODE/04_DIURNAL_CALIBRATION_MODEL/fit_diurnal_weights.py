"""
fit_diurnal_weights.py - Fit 24-Hour Diurnal Calibration Weights.

Reads matched (timestamp_utc, cams_o3, cpcb_o3) pairs and calculates
the empirical diurnal expectation ratio w(h) = E[cpcb | hour=h] / E[cams | hour=h]
for each UTC hour 00..23.
"""

import sys
import os
import argparse
import pandas as pd
import numpy as np


def fit_diurnal_weights(csv_path: str) -> dict:
    if not os.path.exists(csv_path):
        print(f"Error: Dataset file not found at '{csv_path}'")
        return {}

    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df):,} rows from {csv_path}")

    # Standardize column names
    time_col = next((c for c in df.columns if "time" in c.lower() or "date" in c.lower()), None)
    cams_col = next((c for c in df.columns if "cams" in c.lower() and "o3" in c.lower()), None)
    cpcb_col = next((c for c in df.columns if "cpcb" in c.lower() and "o3" in c.lower()), None)

    if not all([time_col, cams_col, cpcb_col]):
        print(f"Error: Missing required columns. Found: {list(df.columns)}")
        return {}

    df["dt"] = pd.to_datetime(df[time_col], utc=True)
    df["hour_utc"] = df["dt"].dt.hour

    clean = df[[cams_col, cpcb_col, "hour_utc"]].dropna()
    print(f"Clean matched pairs: {len(clean):,}")

    weights = []
    print("\n--- 24-HOUR EMPIRICAL DIURNAL OZONE WEIGHTS ---")
    print(f"{'Hour (UTC)':<12} {'Hour (IST)':<12} {'Sample n':<10} {'Mean CAMS':<12} {'Mean CPCB':<12} {'Weight w(h)':<12}")
    print("-" * 72)

    for h in range(24):
        subset = clean[clean["hour_utc"] == h]
        n = len(subset)
        if n < 30:
            print(f"Warning: Low sample size for hour {h:02d} UTC (n={n})")
        mean_cams = subset[cams_col].mean()
        mean_cpcb = subset[cpcb_col].mean()
        w = round(mean_cpcb / mean_cams, 2) if mean_cams > 0 else 0.50
        ist_h = (h + 5) % 24
        weights.append(w)
        print(f"{h:02d}:00        {ist_h:02d}:30        {n:<10} {mean_cams:<12.2f} {mean_cpcb:<12.2f} {w:<12.2f}")

    print("\nFormatted Python Array:")
    print("DIURNAL_O3_WEIGHTS_UTC = " + str(weights))
    return {"weights": weights}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fit 24-Hour Diurnal Ozone Weights")
    parser.add_argument("--csv", type=str, default="data/cams_cpcb_matched_13k.csv", help="Path to matched pairs CSV")
    args = parser.parse_args()
    fit_diurnal_weights(args.csv)
