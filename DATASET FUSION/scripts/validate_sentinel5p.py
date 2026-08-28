"""
SIH 25178 - Phase 2: Sentinel-5P Quality Control & Feature Extraction
Step 7 of Phase 2 Pipeline.

Responsibilities:
1. Loads all processed Sentinel-5P daily extraction CSVs across 10 stations.
2. Extracts product columns ('no2', 'co', 'hcho') for valid pixels (data_mask == 1).
3. Preserves exact UTC observation time, valid pixel count, and spatial mean.
4. Outputs:
   - data/quality_reports/sentinel5p_quality_report.csv
   - data/sentinel5p/processed/<STATION_ID>_s5p_daily.parquet
"""

import os
import glob
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROC_S5P_DIR = os.path.join(PROJECT_ROOT, "data", "sentinel5p", "processed")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "data", "quality_reports")
STATIONS_CSV = os.path.join(PROJECT_ROOT, "config", "stations.csv")

os.makedirs(REPORTS_DIR, exist_ok=True)

def process_station_s5p(station_id):
    stn_dir = os.path.join(PROC_S5P_DIR, station_id)
    if not os.path.isdir(stn_dir):
        return None, []
        
    csv_files = glob.glob(os.path.join(stn_dir, "*.csv"))
    if not csv_files:
        return None, []
        
    daily_records = []
    
    for f in csv_files:
        bn = os.path.basename(f)
        parts = bn.replace(".csv", "").split("_")
        prod = parts[1].upper() # NO2, CO, HCHO
        date_str = parts[-1]    # YYYYMMDD
        
        try:
            df = pd.read_csv(f)
            if df.empty:
                continue
            
            val_col = prod.lower()
            if val_col in df.columns:
                valid_df = df[df["data_mask"] == 1] if "data_mask" in df.columns else df
                if not valid_df.empty:
                    mean_val = valid_df[val_col].mean()
                    px_cnt = len(valid_df)
                    obs_time = valid_df["observation_time"].iloc[0] if "observation_time" in valid_df.columns else None
                    daily_records.append({
                        "station_id": station_id,
                        "date": f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}",
                        "product": prod,
                        "value": mean_val,
                        "pixel_count": px_cnt,
                        "obs_time": obs_time
                    })
        except Exception:
            continue
            
    if not daily_records:
        return None, []
        
    df_all = pd.DataFrame(daily_records)
    
    qc_stats = []
    for prod in ["NO2", "CO", "HCHO"]:
        sub = df_all[df_all["product"] == prod]
        valid_cnt = len(sub)
        expected_cnt = 1096 # 2023-2025 days
        qc_stats.append({
            "station_id": station_id,
            "product": prod,
            "expected_days": expected_cnt,
            "valid_observations": valid_cnt,
            "missing_or_cloud_filtered": expected_cnt - valid_cnt,
            "success_rate_pct": round(valid_cnt / expected_cnt * 100, 2)
        })
        
    # Pivot values
    pivot_val = df_all.pivot_table(index=["station_id", "date"], columns="product", values="value", aggfunc="mean").reset_index()
    for prod in ["NO2", "CO", "HCHO"]:
        if prod not in pivot_val.columns:
            pivot_val[prod] = np.nan
    pivot_val = pivot_val.rename(columns={"NO2": "sat_NO2", "CO": "sat_CO", "HCHO": "sat_HCHO"})
    
    # Pivot observation times
    pivot_time = df_all.pivot_table(index=["station_id", "date"], columns="product", values="obs_time", aggfunc="first").reset_index()
    # Choose most frequent or NO2 obs_time as reference
    ref_time_col = "NO2" if "NO2" in pivot_time.columns else ("CO" if "CO" in pivot_time.columns else "HCHO")
    pivot_val["observation_time"] = pivot_time[ref_time_col] if ref_time_col in pivot_time.columns else None
    
    # Pivot pixel counts
    pivot_px = df_all.pivot_table(index=["station_id", "date"], columns="product", values="pixel_count", aggfunc="mean").reset_index()
    for prod in ["NO2", "CO", "HCHO"]:
        if prod not in pivot_px.columns:
            pivot_px[prod] = 0
    pivot_px = pivot_px.rename(columns={"NO2": "px_count_NO2", "CO": "px_count_CO", "HCHO": "px_count_HCHO"})
    
    merged_daily = pd.merge(pivot_val, pivot_px, on=["station_id", "date"], how="left")
    merged_daily["date"] = pd.to_datetime(merged_daily["date"])
    
    # Save daily station parquet
    out_parquet = os.path.join(PROC_S5P_DIR, f"{station_id}_s5p_daily.parquet")
    merged_daily.to_parquet(out_parquet, index=False)
    print(f"     [SAVED] {out_parquet} ({len(merged_daily):,} daily records)")
    
    return merged_daily, qc_stats

def process_all_sentinel5p():
    print("[STEP 7] Executing Sentinel-5P Quality Control & Daily Aggregation...")
    stations_df = pd.read_csv(STATIONS_CSV)
    all_qc = []
    
    for _, stn_row in stations_df.iterrows():
        stn = stn_row["station_id"]
        print(f"  -> Processing Sentinel-5P: {stn}...")
        df_daily, qc_stats = process_station_s5p(stn)
        if qc_stats:
            all_qc.extend(qc_stats)
            
    qc_df = pd.DataFrame(all_qc)
    qc_report_path = os.path.join(REPORTS_DIR, "sentinel5p_quality_report.csv")
    qc_df.to_csv(qc_report_path, index=False)
    print(f"[DONE] Sentinel-5P QC Report saved to: {qc_report_path}")

if __name__ == "__main__":
    process_all_sentinel5p()
