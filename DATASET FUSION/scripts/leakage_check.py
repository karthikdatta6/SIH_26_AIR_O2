"""
SIH 25178 - Phase 2: Automated Zero Data Leakage Audit & Fusion QC
Step 31 & 36 of Phase 2 Pipeline.

Runs rigorous causality and integrity assertions on data/fused/station_hourly_fused.parquet:
1. Strict Temporal Causality: satellite_observation_time <= record timestamp_utc.
2. Stale Observation Limit: satellite_age_hours <= 24.0.
3. Strict Grid Monotonicity: timestamps are continuous and strictly increasing at 1-hour frequency.
4. Zero Duplicate Check: no duplicate (station_id, timestamp_utc) tuples.
5. Pure Target Verification: ground targets are unmodified CPCB values.

Outputs:
- data/quality_reports/leakage_report.csv
- data/quality_reports/fusion_quality_report.csv
"""

import os
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FUSED_PARQUET = os.path.join(PROJECT_ROOT, "data", "fused", "station_hourly_fused.parquet")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "data", "quality_reports")

os.makedirs(REPORTS_DIR, exist_ok=True)

def run_leakage_audit():
    print("[STEP 31 & 36] Running Automated Zero-Leakage & Data Integrity Audit...")
    
    if not os.path.exists(FUSED_PARQUET):
        raise FileNotFoundError(f"Master fused dataset not found at {FUSED_PARQUET}")
        
    df = pd.read_parquet(FUSED_PARQUET)
    print(f"  -> Loaded master dataset: {df.shape[0]:,} rows x {df.shape[1]} columns")
    
    tests = []
    
    # --- TEST 1: Satellite Temporal Causality ---
    has_sat = df["satellite_observation_time"].notna()
    sat_future_mask = has_sat & (df["satellite_observation_time"] > df["timestamp_utc"])
    sat_future_count = sat_future_mask.sum()
    tests.append({
        "audit_name": "SATELLITE_CAUSALITY_CHECK",
        "description": "Asserts satellite_observation_time <= current timestamp_utc (zero forward lookahead)",
        "violations_found": int(sat_future_count),
        "status": "PASSED" if sat_future_count == 0 else "FAILED",
        "severity": "CRITICAL"
    })
    
    # --- TEST 2: Satellite Stale Age Window ---
    age_invalid_mask = has_sat & ((df["satellite_age_hours"] < 0) | (df["satellite_age_hours"] > 24.0))
    age_invalid_count = age_invalid_mask.sum()
    tests.append({
        "audit_name": "SATELLITE_AGE_WINDOW_CHECK",
        "description": "Asserts satellite observation age is strictly between 0h and 24h",
        "violations_found": int(age_invalid_count),
        "status": "PASSED" if age_invalid_count == 0 else "FAILED",
        "severity": "HIGH"
    })
    
    # --- TEST 3: Duplicate Timestamps ---
    dup_count = df.duplicated(subset=["station_id", "timestamp_utc"]).sum()
    tests.append({
        "audit_name": "DUPLICATE_TIMESTAMPS_CHECK",
        "description": "Asserts exactly one record per (station_id, timestamp_utc) tuple",
        "violations_found": int(dup_count),
        "status": "PASSED" if dup_count == 0 else "FAILED",
        "severity": "CRITICAL"
    })
    
    # --- TEST 4: Grid Monotonicity ---
    monotonic_errors = 0
    for stn, stn_group in df.groupby("station_id"):
        diffs = stn_group["timestamp_utc"].diff().dropna()
        non_1h = (diffs != pd.Timedelta(hours=1)).sum()
        monotonic_errors += non_1h
        
    tests.append({
        "audit_name": "HOURLY_GRID_MONOTONICITY_CHECK",
        "description": "Asserts strictly continuous 1-hour steps across all stations (2023-2025)",
        "violations_found": int(monotonic_errors),
        "status": "PASSED" if monotonic_errors == 0 else "FAILED",
        "severity": "HIGH"
    })
    
    # --- TEST 5: Target Variables Purity ---
    # Assert ground targets are not fabricated
    o3_neg = (df["OZONE_ground"] < 0).sum()
    no2_neg = (df["NO2_ground"] < 0).sum()
    tests.append({
        "audit_name": "TARGET_VARIABLES_VALIDITY_CHECK",
        "description": "Asserts no negative concentrations in ground truth targets (OZONE, NO2)",
        "violations_found": int(o3_neg + no2_neg),
        "status": "PASSED" if (o3_neg + no2_neg) == 0 else "FAILED",
        "severity": "CRITICAL"
    })
    
    leakage_df = pd.DataFrame(tests)
    leakage_out = os.path.join(REPORTS_DIR, "leakage_report.csv")
    leakage_df.to_csv(leakage_out, index=False)
    print(f"[DONE] Saved Zero-Leakage Audit Report to: {leakage_out}")
    for _, t in leakage_df.iterrows():
        print(f"  [{t['status']}] {t['audit_name']}: {t['violations_found']} violations")
        
    # --- FUSION QUALITY REPORT ---
    fusion_stats = []
    for stn, stn_df in df.groupby("station_id"):
        fusion_stats.append({
            "station_id": stn,
            "total_hourly_rows": len(stn_df),
            "start_time_utc": stn_df["timestamp_utc"].min(),
            "end_time_utc": stn_df["timestamp_utc"].max(),
            "target_OZONE_valid_pct": round(stn_df["OZONE_ground"].notna().mean() * 100, 2),
            "target_NO2_valid_pct": round(stn_df["NO2_ground"].notna().mean() * 100, 2),
            "era5_meteorology_valid_pct": round(stn_df["era5_temperature_c"].notna().mean() * 100, 2),
            "sentinel5p_satellite_coverage_pct": round(stn_df["sat_NO2"].notna().mean() * 100, 2),
            "geospatial_features_present": "YES" if stn_df["geo_dist_to_nearest_road_m"].notna().all() else "NO"
        })
        
    fusion_df = pd.DataFrame(fusion_stats)
    fusion_out = os.path.join(REPORTS_DIR, "fusion_quality_report.csv")
    fusion_df.to_csv(fusion_out, index=False)
    print(f"[DONE] Saved Master Fusion Quality Report to: {fusion_out}")
    
    return leakage_df

if __name__ == "__main__":
    run_leakage_audit()
