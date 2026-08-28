"""
SIH 25178 - Phase 2: CPCB Quality Control & Hourly Standardisation
Step 6 of Phase 2 Pipeline.

Responsibilities:
1. Loads all 30 CPCB XLSX files (10 stations x 3 years: 2023-2025).
2. Standardises timestamps: Converts 15-minute IST ('DD-MM-YYYY HH:MM') to UTC.
3. Quality Control (QC):
   - Audits missingness, negative values, and out-of-bounds instrument anomalies.
   - Cleans invalid readings to NaN (NEVER replaces with 0).
4. Aggregation: Aggregates 15-min observations to 1-Hour UTC intervals.
   - Requires >= 3 valid 15-min readings per hour to produce a valid hourly mean.
   - Retains 'obs_count' per hourly cell.
5. Outputs:
   - data/quality_reports/cpcb_quality_report.csv
   - data/cpcb/processed/<STATION_ID>_hourly.parquet
"""

import os
import glob
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_CPCB_DIR = os.path.join(PROJECT_ROOT, "data", "cpcb", "raw")
PROC_CPCB_DIR = os.path.join(PROJECT_ROOT, "data", "cpcb", "processed")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "data", "quality_reports")
STATIONS_CSV = os.path.join(PROJECT_ROOT, "config", "stations.csv")

os.makedirs(PROC_CPCB_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# Canonical pollutant columns & physical validity bounds (ug/m3, CO in mg/m3)
POLLUTANT_BOUNDS = {
    "PM2.5": (0, 1000),
    "PM10": (0, 1500),
    "NO": (0, 1000),
    "NO2": (0, 1000),
    "NOx": (0, 1500),
    "NH3": (0, 1000),
    "SO2": (0, 1000),
    "CO": (0, 50),        # mg/m3
    "OZONE": (0, 1000),    # Target variable
}

def clean_cpcb_dataframe(df_raw, station_id, year):
    # Standardise column headers
    cols = [str(c).strip() for c in df_raw.columns]
    df_raw.columns = cols
    
    # Identify date column
    date_col = None
    for c in ["From Date", "FromDate", "Date"]:
        if c in df_raw.columns:
            date_col = c
            break
    if date_col is None:
        raise ValueError(f"No valid date column found in {station_id} {year}")
        
    # Convert IST timestamp to UTC
    # Format is DD-MM-YYYY HH:MM
    df_raw["timestamp_ist"] = pd.to_datetime(df_raw[date_col], format="%d-%m-%Y %H:%M", errors="coerce")
    df_clean = df_raw.dropna(subset=["timestamp_ist"]).copy()
    
    # Localise to IST (UTC+5:30) and convert to UTC
    df_clean["timestamp_utc"] = df_clean["timestamp_ist"].dt.tz_localize("Asia/Kolkata").dt.tz_convert("UTC").dt.tz_localize(None)
    df_clean["station_id"] = station_id
    
    # Map pollutant columns
    col_mapping = {}
    for standard_name in POLLUTANT_BOUNDS.keys():
        for col in df_clean.columns:
            clean_c = col.upper().replace(".", "").replace(" ", "").replace("_", "")
            std_c = standard_name.upper().replace(".", "").replace(" ", "").replace("_", "")
            if clean_c == std_c:
                col_mapping[col] = standard_name
                break
                
    df_clean = df_clean.rename(columns=col_mapping)
    
    qc_stats = []
    
    # Validate and clean each pollutant
    for poll, (min_val, max_val) in POLLUTANT_BOUNDS.items():
        if poll in df_clean.columns:
            s = pd.to_numeric(df_clean[poll], errors="coerce")
            total = len(s)
            missing = s.isna().sum()
            negatives = (s < 0).sum()
            out_of_bounds = ((s < min_val) | (s > max_val)).sum()
            
            # Clean: set out of bounds and negatives to NaN
            s_clean = s.copy()
            s_clean[(s_clean < min_val) | (s_clean > max_val)] = np.nan
            valid = s_clean.notna().sum()
            
            df_clean[poll] = s_clean
            
            qc_stats.append({
                "station_id": station_id,
                "year": year,
                "pollutant": poll,
                "total_records": total,
                "valid_records": valid,
                "missing_records": missing,
                "missing_pct": round(missing / total * 100, 2),
                "negative_records": negatives,
                "out_of_bounds_records": out_of_bounds
            })
        else:
            qc_stats.append({
                "station_id": station_id,
                "year": year,
                "pollutant": poll,
                "total_records": len(df_clean),
                "valid_records": 0,
                "missing_records": len(df_clean),
                "missing_pct": 100.0,
                "negative_records": 0,
                "out_of_bounds_records": 0
            })
            df_clean[poll] = np.nan

    return df_clean, qc_stats

def aggregate_to_hourly(df_15min, station_id):
    # Floor timestamps to nearest 1-hour UTC
    df_15min["timestamp_hour"] = df_15min["timestamp_utc"].dt.floor("1h")
    
    # Aggregation requires >= 3 of 4 valid readings (75% threshold)
    poll_cols = list(POLLUTANT_BOUNDS.keys())
    
    grouped = df_15min.groupby("timestamp_hour")
    
    agg_dict = {}
    for col in poll_cols:
        # Calculate mean only if count >= 3
        mean_s = grouped[col].mean()
        count_s = grouped[col].count()
        valid_mask = count_s >= 3
        agg_dict[f"{col}_ground"] = mean_s.where(valid_mask, np.nan)
        agg_dict[f"{col}_obs_count"] = count_s
        
    df_hourly = pd.DataFrame(agg_dict).reset_index()
    df_hourly["station_id"] = station_id
    df_hourly = df_hourly.rename(columns={"timestamp_hour": "timestamp_utc"})
    
    return df_hourly

def process_all_cpcb():
    print("[STEP 6] Executing CPCB Quality Control & 1-Hour Aggregation...")
    stations_df = pd.read_csv(STATIONS_CSV)
    all_qc_records = []
    
    for _, stn_row in stations_df.iterrows():
        stn = stn_row["station_id"]
        station_dfs = []
        print(f"  -> Processing CPCB: {stn}...")
        
        for year in [2023, 2024, 2025]:
            fpath = os.path.join(RAW_CPCB_DIR, f"{stn}_{year}_DATA.xlsx")
            if not os.path.exists(fpath):
                print(f"     [WARNING] Missing {fpath}")
                continue
            
            try:
                df_raw = pd.read_excel(fpath, sheet_name="CPCB Ambient AQ", header=10)
                df_clean, qc_stats = clean_cpcb_dataframe(df_raw, stn, year)
                station_dfs.append(df_clean)
                all_qc_records.extend(qc_stats)
            except Exception as e:
                print(f"     [ERROR] Failed to read {fpath}: {e}")
                
        if station_dfs:
            combined_15min = pd.concat(station_dfs, ignore_index=True)
            df_hourly = aggregate_to_hourly(combined_15min, stn)
            
            out_parquet = os.path.join(PROC_CPCB_DIR, f"{stn}_cpcb_hourly.parquet")
            df_hourly.to_parquet(out_parquet, index=False)
            print(f"     [SAVED] {out_parquet} ({len(df_hourly):,} hourly rows)")
            
    # Save master CPCB QC report
    qc_df = pd.DataFrame(all_qc_records)
    qc_report_path = os.path.join(REPORTS_DIR, "cpcb_quality_report.csv")
    qc_df.to_csv(qc_report_path, index=False)
    print(f"[DONE] Master CPCB QC Report saved to: {qc_report_path}")

if __name__ == "__main__":
    process_all_cpcb()
