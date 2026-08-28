"""
SIH 25178 - Phase 2: Independent Dataset Audit & Physical Sanity Verification
Fulfills Section 5, 6, 7 & 14 of Forensic Audit Master Prompt.

Generates:
- data/quality_reports/independent_dataset_audit.csv
"""

import os
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FUSED_PARQUET = os.path.join(PROJECT_ROOT, "data", "fused", "station_hourly_fused.parquet")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "data", "quality_reports")

os.makedirs(REPORTS_DIR, exist_ok=True)

def run_independent_audit():
    print("\n[INDEPENDENT AUDIT] Running comprehensive dataset audit on master fused parquet...")
    if not os.path.exists(FUSED_PARQUET):
        raise FileNotFoundError(f"Master parquet not found: {FUSED_PARQUET}")
        
    df = pd.read_parquet(FUSED_PARQUET)
    
    audit_records = []
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    total_rows = len(df)
    
    for col in df.columns:
        null_count = df[col].isna().sum()
        null_pct = (null_count / total_rows) * 100.0
        
        if col in numeric_cols:
            valid_series = df[col].dropna()
            if not valid_series.empty:
                col_min = float(valid_series.min())
                col_max = float(valid_series.max())
                col_mean = float(valid_series.mean())
                col_median = float(valid_series.median())
                col_std = float(valid_series.std())
            else:
                col_min, col_max, col_mean, col_median, col_std = np.nan, np.nan, np.nan, np.nan, np.nan
        else:
            col_min, col_max, col_mean, col_median, col_std = np.nan, np.nan, np.nan, np.nan, np.nan
            
        audit_records.append({
            "column_name": col,
            "data_type": str(df[col].dtype),
            "total_rows": total_rows,
            "null_count": int(null_count),
            "missing_pct": round(float(null_pct), 2),
            "min_val": round(col_min, 4) if pd.notna(col_min) else None,
            "max_val": round(col_max, 4) if pd.notna(col_max) else None,
            "mean_val": round(col_mean, 4) if pd.notna(col_mean) else None,
            "median_val": round(col_median, 4) if pd.notna(col_median) else None,
            "std_dev": round(col_std, 4) if pd.notna(col_std) else None
        })
        
    audit_df = pd.DataFrame(audit_records)
    out_audit = os.path.join(REPORTS_DIR, "independent_dataset_audit.csv")
    audit_df.to_csv(out_audit, index=False)
    print(f"[DONE] Saved Independent Dataset Audit: {out_audit} ({len(audit_df)} columns audited)")
    
    # Print key summary
    print("\n--- Key Summary Statistics ---")
    print(f"Total Rows:     {total_rows:,}")
    print(f"Total Columns:  {len(df.columns)}")
    print(f"Stations:       {df['station_id'].nunique()} stations ({df['station_id'].unique().tolist()})")
    print(f"Time Horizon:   {df['timestamp_utc'].min()} to {df['timestamp_utc'].max()}")
    print(f"Ground O3 Mean: {df['OZONE_ground'].mean():.2f} ug/m3 (Min: {df['OZONE_ground'].min():.2f}, Max: {df['OZONE_ground'].max():.2f})")
    print(f"Ground NO2 Mean:{df['NO2_ground'].mean():.2f} ug/m3 (Min: {df['NO2_ground'].min():.2f}, Max: {df['NO2_ground'].max():.2f})")
    print(f"ERA5 Temp Mean: {df['era5_temperature_c'].mean():.2f} °C (Min: {df['era5_temperature_c'].min():.2f}, Max: {df['era5_temperature_c'].max():.2f})")
    print(f"ERA5 RH Mean:   {df['era5_relative_humidity'].mean():.2f} % (Min: {df['era5_relative_humidity'].min():.2f}, Max: {df['era5_relative_humidity'].max():.2f})")
    print(f"ERA5 Wind Mean: {df['era5_wind_speed'].mean():.2f} m/s (Min: {df['era5_wind_speed'].min():.2f}, Max: {df['era5_wind_speed'].max():.2f})")
    print(f"Sat NO2 Mean:   {df['sat_NO2'].mean():.6f} mol/m2 (Min: {df['sat_NO2'].min():.6f}, Max: {df['sat_NO2'].max():.6f})")

if __name__ == "__main__":
    run_independent_audit()
