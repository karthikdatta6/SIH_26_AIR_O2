"""
SIH 25178 - Phase 2: ERA5 Reanalysis QC & Station Extraction
Step 8 of Phase 2 Pipeline.

Responsibilities:
1. Ingests ERA5 meteorological data (2022-2025 across 16 quarterly bundles).
2. For each quarter, merges instantaneous variables (t2m, d2m, u10, v10, sp, blh)
   and accumulated variables (ssrd, tp).
3. Spatially extracts hourly atmospheric variables for each of the 10 stations:
   - t2m (2m Temperature, Kelvin -> Celsius: T - 273.15)
   - d2m (2m Dewpoint Temperature, Kelvin -> Celsius: Td - 273.15)
   - u10, v10 (10m Wind Vectors, m/s)
   - Derived: wind_speed (m/s), wind_direction (deg), relative_humidity (%)
   - sp (Surface Pressure, Pa -> hPa: Pa / 100.0)
   - blh (Boundary Layer Height, m)
   - ssrd (Surface Solar Radiation Downward, W/m2: J/m2 / 3600s)
   - tp (Total Precipitation, mm: meters * 1000.0)
4. Generates spatial mapping audit (station lat/lon vs ERA5 grid lat/lon + haversine distance).
5. Outputs:
   - data/quality_reports/era5_quality_report.csv
   - data/quality_reports/spatial_matching_report.csv
   - data/era5/processed/<STATION_ID>_era5_hourly.parquet
"""

import os
import glob
import math
import pandas as pd
import numpy as np
import xarray as xr

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_ERA5_DIR = os.path.join(PROJECT_ROOT, "data", "era5", "raw")
PROC_ERA5_DIR = os.path.join(PROJECT_ROOT, "data", "era5", "processed")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "data", "quality_reports")
STATIONS_CSV = os.path.join(PROJECT_ROOT, "config", "stations.csv")

os.makedirs(PROC_ERA5_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_relative_humidity(temp_c, dewpoint_c):
    # Magnus-Tetens formulation
    a = 17.67
    b = 243.5
    svp = 6.112 * np.exp((a * temp_c) / (temp_c + b))
    vp = 6.112 * np.exp((a * dewpoint_c) / (dewpoint_c + b))
    rh = 100.0 * (vp / svp)
    return np.clip(rh, 0.0, 100.0)

def calculate_wind_speed_direction(u10, v10):
    ws = np.sqrt(u10**2 + v10**2)
    # Meteorological convention: direction wind is blowing FROM
    wd = (np.degrees(np.arctan2(-u10, -v10))) % 360.0
    return ws, wd

def load_era5_master_dataframe():
    quarter_dirs = sorted([d for d in glob.glob(os.path.join(RAW_ERA5_DIR, "*")) if os.path.isdir(d)])
    
    if quarter_dirs:
        print(f"  -> Found {len(quarter_dirs)} quarterly ERA5 directories. Merging NetCDF bundles...")
        quarter_dfs = []
        for qd in quarter_dirs:
            accum_f = os.path.join(qd, "data_stream-oper_stepType-accum.nc")
            instant_f = os.path.join(qd, "data_stream-oper_stepType-instant.nc")
            
            if os.path.exists(accum_f) and os.path.exists(instant_f):
                ds_a = xr.open_dataset(accum_f)
                ds_i = xr.open_dataset(instant_f)
                ds_merged = xr.merge([ds_a, ds_i], compat="override")
                df_q = ds_merged.to_dataframe().reset_index()
                quarter_dfs.append(df_q)
            elif os.path.exists(instant_f):
                ds_i = xr.open_dataset(instant_f)
                df_q = ds_i.to_dataframe().reset_index()
                quarter_dfs.append(df_q)
            elif os.path.exists(accum_f):
                ds_a = xr.open_dataset(accum_f)
                df_q = ds_a.to_dataframe().reset_index()
                quarter_dfs.append(df_q)
                
        if quarter_dfs:
            df_master = pd.concat(quarter_dfs, ignore_index=True)
            return df_master

    # Fallback to single CSV if present
    csv_fallback = glob.glob(os.path.join(RAW_ERA5_DIR, "*.csv"))
    if csv_fallback:
        print(f"  -> Loading ERA5 timeseries CSV: {csv_fallback[0]}...")
        df_era5 = pd.read_csv(csv_fallback[0])
        return df_era5
        
    raise FileNotFoundError(f"No valid ERA5 NetCDF or CSV files found in {RAW_ERA5_DIR}")

def process_all_era5():
    print("[STEP 8] Executing ERA5 Reanalysis Processing & Station Spatial Extraction...")
    df_raw = load_era5_master_dataframe()
    
    # Standardise column names
    col_map = {c: c.lower().strip() for c in df_raw.columns}
    df_raw = df_raw.rename(columns=col_map)
    
    time_col = None
    for c in ["valid_time", "time", "date"]:
        if c in df_raw.columns:
            time_col = c
            break
            
    df_raw["timestamp_utc"] = pd.to_datetime(df_raw[time_col]).astype("datetime64[ns]")
    
    stations_df = pd.read_csv(STATIONS_CSV)
    
    spatial_mapping_records = []
    era5_qc_records = []
    
    has_spatial_coords = "latitude" in df_raw.columns and "longitude" in df_raw.columns
    
    for _, stn_row in stations_df.iterrows():
        stn = str(stn_row["station_id"]).strip()
        stn_lat = float(stn_row["latitude"])
        stn_lon = float(stn_row["longitude"])
        
        print(f"  -> Extracting ERA5 for Station: {stn} ({stn_lat:.4f}, {stn_lon:.4f})...")
        
        if has_spatial_coords and len(df_raw["latitude"].unique()) > 1:
            # Find nearest grid point
            unique_grid = df_raw[["latitude", "longitude"]].drop_duplicates()
            unique_grid["dist_km"] = unique_grid.apply(
                lambda r: haversine_distance(stn_lat, stn_lon, r["latitude"], r["longitude"]), axis=1
            )
            nearest = unique_grid.sort_values("dist_km").iloc[0]
            grid_lat = nearest["latitude"]
            grid_lon = nearest["longitude"]
            dist_km = nearest["dist_km"]
            
            df_stn = df_raw[(df_raw["latitude"] == grid_lat) & (df_raw["longitude"] == grid_lon)].copy()
        else:
            grid_lat = 28.75
            grid_lon = 77.25
            dist_km = haversine_distance(stn_lat, stn_lon, grid_lat, grid_lon)
            df_stn = df_raw.copy()
            
        # Deduplicate timestamps if any
        df_stn = df_stn.sort_values("timestamp_utc").drop_duplicates(subset=["timestamp_utc"]).reset_index(drop=True)
        
        # Build Standard Feature Columns
        out_df = pd.DataFrame()
        out_df["timestamp_utc"] = df_stn["timestamp_utc"]
        out_df["station_id"] = stn
        
        # Temperature & Dewpoint (Kelvin to Celsius)
        t_col = "t2m" if "t2m" in df_stn.columns else ("temperature" if "temperature" in df_stn.columns else None)
        d_col = "d2m" if "d2m" in df_stn.columns else ("dewpoint" if "dewpoint" in df_stn.columns else None)
        
        if t_col and d_col:
            out_df["era5_temperature_k"] = df_stn[t_col]
            out_df["era5_temperature_c"] = df_stn[t_col] - 273.15 if df_stn[t_col].mean() > 100 else df_stn[t_col]
            out_df["era5_dewpoint_k"] = df_stn[d_col]
            out_df["era5_dewpoint_c"] = df_stn[d_col] - 273.15 if df_stn[d_col].mean() > 100 else df_stn[d_col]
        else:
            out_df["era5_temperature_k"] = np.nan
            out_df["era5_temperature_c"] = np.nan
            out_df["era5_dewpoint_k"] = np.nan
            out_df["era5_dewpoint_c"] = np.nan
            
        # Wind Vectors & Derived Speed / Direction
        u_col = "u10" if "u10" in df_stn.columns else ("u_wind" if "u_wind" in df_stn.columns else None)
        v_col = "v10" if "v10" in df_stn.columns else ("v_wind" if "v_wind" in df_stn.columns else None)
        
        if u_col and v_col:
            out_df["era5_u10"] = df_stn[u_col]
            out_df["era5_v10"] = df_stn[v_col]
            ws, wd = calculate_wind_speed_direction(df_stn[u_col].values, df_stn[v_col].values)
            out_df["era5_wind_speed"] = ws
            out_df["era5_wind_direction"] = wd
        else:
            out_df["era5_u10"] = np.nan
            out_df["era5_v10"] = np.nan
            out_df["era5_wind_speed"] = np.nan
            out_df["era5_wind_direction"] = np.nan
            
        # Relative Humidity
        if t_col and d_col:
            out_df["era5_relative_humidity"] = calculate_relative_humidity(
                out_df["era5_temperature_c"].values, out_df["era5_dewpoint_c"].values
            )
        else:
            out_df["era5_relative_humidity"] = np.nan
            
        # Surface Pressure (Pa -> hPa)
        sp_col = "sp" if "sp" in df_stn.columns else ("surface_pressure" if "surface_pressure" in df_stn.columns else None)
        if sp_col:
            out_df["era5_surface_pressure_hpa"] = df_stn[sp_col] / 100.0 if df_stn[sp_col].mean() > 2000 else df_stn[sp_col]
        else:
            out_df["era5_surface_pressure_hpa"] = np.nan
            
        # Boundary Layer Height (m)
        blh_col = "blh" if "blh" in df_stn.columns else ("boundary_layer_height" if "boundary_layer_height" in df_stn.columns else None)
        out_df["era5_boundary_layer_height"] = df_stn[blh_col] if blh_col else np.nan
        
        # Surface Solar Radiation Downwards (J/m2 -> W/m2)
        ssrd_col = "ssrd" if "ssrd" in df_stn.columns else ("surface_solar_radiation" if "surface_solar_radiation" in df_stn.columns else None)
        if ssrd_col:
            out_df["era5_solar_radiation_w_m2"] = np.maximum(0.0, df_stn[ssrd_col] / 3600.0)
        else:
            out_df["era5_solar_radiation_w_m2"] = np.nan
            
        # Total Precipitation (m -> mm)
        tp_col = "tp" if "tp" in df_stn.columns else ("total_precipitation" if "total_precipitation" in df_stn.columns else None)
        if tp_col:
            out_df["era5_total_precipitation_mm"] = np.maximum(0.0, df_stn[tp_col] * 1000.0)
        else:
            out_df["era5_total_precipitation_mm"] = np.nan
            
        # Save station parquet
        stn_out = os.path.join(PROC_ERA5_DIR, f"{stn}_era5_hourly.parquet")
        out_df.to_parquet(stn_out, index=False)
        print(f"     [SAVED] {stn_out} ({len(out_df):,} hourly rows)")
        
        spatial_mapping_records.append({
            "station_id": stn,
            "station_latitude": stn_lat,
            "station_longitude": stn_lon,
            "era5_grid_latitude": grid_lat,
            "era5_grid_longitude": grid_lon,
            "distance_km": round(dist_km, 3)
        })
        
        era5_qc_records.append({
            "station_id": stn,
            "total_hourly_records": len(out_df),
            "start_timestamp": str(out_df["timestamp_utc"].min()),
            "end_timestamp": str(out_df["timestamp_utc"].max()),
            "mean_temperature_c": round(float(out_df["era5_temperature_c"].mean()), 2),
            "mean_relative_humidity": round(float(out_df["era5_relative_humidity"].mean()), 2),
            "mean_wind_speed": round(float(out_df["era5_wind_speed"].mean()), 2),
            "mean_surface_pressure_hpa": round(float(out_df["era5_surface_pressure_hpa"].mean()), 2)
        })
        
    spatial_df = pd.DataFrame(spatial_mapping_records)
    spatial_out = os.path.join(REPORTS_DIR, "spatial_matching_report.csv")
    spatial_df.to_csv(spatial_out, index=False)
    print(f"[DONE] Saved Spatial Matching Report: {spatial_out}")
    
    era5_qc_df = pd.DataFrame(era5_qc_records)
    era5_qc_out = os.path.join(REPORTS_DIR, "era5_quality_report.csv")
    era5_qc_df.to_csv(era5_qc_out, index=False)
    print(f"[DONE] Saved ERA5 Quality Report: {era5_qc_out}")

if __name__ == "__main__":
    process_all_era5()
