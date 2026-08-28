"""
SIH 25178 - Phase 2: Comprehensive Missingness & Gap Analysis
Step 10 of Phase 2 Pipeline.

Responsibilities:
1. Calculates missingness statistics across all 10 stations and all variables over 2023-2025:
   - CPCB ground pollutants (OZONE, NO2, PM2.5, PM10, CO, NO, NOx, NH3, SO2)
   - Sentinel-5P satellite observations (NO2, CO, HCHO)
   - ERA5 meteorological variables
2. Computes:
   - Total expected observation periods (26,304 hourly timestamps)
   - Valid count, missing count, missing percentage
   - Longest consecutive missing gap (hours)
   - Expected scientific reason for missingness
3. Output:
   - data/quality_reports/missingness_report.csv
"""

import os
import glob
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
REPORTS_DIR = os.path.join(DATA_DIR, "quality_reports")
STATIONS_CSV = os.path.join(PROJECT_ROOT, "config", "stations.csv")

os.makedirs(REPORTS_DIR, exist_ok=True)

def find_longest_nan_streak(series):
    is_nan = series.isna().astype(int)
    streaks = is_nan * (is_nan.groupby((is_nan != is_nan.shift()).cumsum()).cumcount() + 1)
    return streaks.max() if not streaks.empty else 0

def run_missingness_audit():
    print("[STEP 10] Executing Comprehensive Missingness & Temporal Gap Audit...")
    stations_df = pd.read_csv(STATIONS_CSV)
    
    expected_hours = 26304 # 1096 days * 24 hours (2023-01-01 to 2025-12-31)
    
    missing_records = []
    
    for _, stn_row in stations_df.iterrows():
        stn = stn_row["station_id"]
        
        # 1. CPCB Ground Pollutants
        cpcb_f = os.path.join(DATA_DIR, "cpcb", "processed", f"{stn}_cpcb_hourly.parquet")
        if os.path.exists(cpcb_f):
            df_cpcb = pd.read_parquet(cpcb_f)
            # Reindex to complete hourly date range
            full_idx = pd.date_range("2023-01-01 00:00:00", "2025-12-31 23:00:00", freq="1h")
            df_cpcb = df_cpcb.set_index("timestamp_utc").reindex(full_idx).reset_index()
            
            for poll in ["OZONE_ground", "NO2_ground", "CO_ground", "PM2.5_ground", "PM10_ground", "SO2_ground", "NH3_ground"]:
                if poll in df_cpcb.columns:
                    s = df_cpcb[poll]
                    valid = s.notna().sum()
                    missing = expected_hours - valid
                    pct = round(missing / expected_hours * 100, 2)
                    max_gap = find_longest_nan_streak(s)
                    
                    reason = "Normal sensor downtime"
                    if pct > 90.0:
                        reason = "Sensor absent at this station"
                    elif poll in ["OZONE_ground", "NO2_ground"]:
                        reason = "Primary target (High Data Health)"
                        
                    missing_records.append({
                        "station_id": stn,
                        "source": "CPCB_GROUND",
                        "variable": poll,
                        "expected_hours": expected_hours,
                        "valid_observations": valid,
                        "missing_observations": missing,
                        "missing_percentage": pct,
                        "longest_missing_gap_hours": max_gap,
                        "scientific_reason": reason
                    })
                    
        # 2. Sentinel-5P Satellite
        s5p_f = os.path.join(DATA_DIR, "sentinel5p", "processed", f"{stn}_s5p_daily.parquet")
        if os.path.exists(s5p_f):
            df_s5p = pd.read_parquet(s5p_f)
            for prod in ["sat_NO2", "sat_CO", "sat_HCHO"]:
                if prod in df_s5p.columns:
                    s = df_s5p[prod]
                    total_days = 1096
                    valid_days = s.notna().sum()
                    missing_days = total_days - valid_days
                    pct = round(missing_days / total_days * 100, 2)
                    max_gap_days = find_longest_nan_streak(s)
                    
                    missing_records.append({
                        "station_id": stn,
                        "source": "SENTINEL5P_SATELLITE",
                        "variable": prod,
                        "expected_hours": 1096, # Daily overpasses
                        "valid_observations": valid_days,
                        "missing_observations": missing_days,
                        "missing_percentage": pct,
                        "longest_missing_gap_hours": max_gap_days * 24,
                        "scientific_reason": "Intermittent orbit overpass (~13:30 UTC) and cloud/QA filtering"
                    })
                    
        # 3. ERA5 Reanalysis
        era5_f = os.path.join(DATA_DIR, "era5", "processed", f"{stn}_era5_hourly.parquet")
        if os.path.exists(era5_f):
            df_era5 = pd.read_parquet(era5_f)
            for var in ["era5_temperature_c", "era5_wind_speed", "era5_surface_pressure_hpa", "era5_boundary_layer_height"]:
                if var in df_era5.columns:
                    s = df_era5[var]
                    valid = s.notna().sum()
                    missing = len(df_era5) - valid
                    pct = round(missing / len(df_era5) * 100, 2)
                    max_gap = find_longest_nan_streak(s)
                    
                    missing_records.append({
                        "station_id": stn,
                        "source": "ERA5_METEOROLOGY",
                        "variable": var,
                        "expected_hours": len(df_era5),
                        "valid_observations": valid,
                        "missing_observations": missing,
                        "missing_percentage": pct,
                        "longest_missing_gap_hours": max_gap,
                        "scientific_reason": "Continuous numerical weather reanalysis"
                    })

    missing_df = pd.DataFrame(missing_records)
    out_path = os.path.join(REPORTS_DIR, "missingness_report.csv")
    missing_df.to_csv(out_path, index=False)
    print(f"[DONE] Saved Missingness Audit Report to: {out_path} ({len(missing_df)} variable rows)")

if __name__ == "__main__":
    run_missingness_audit()
