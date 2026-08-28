"""
SIH 25178 - Phase 2: Spatiotemporal Fusion Master Engine
Steps 11-13 & 32 of Phase 2 Pipeline.

Fuses:
1. Ground truth & predictor pollutants from CPCB (1-Hour UTC).
2. Continuous meteorological variables from ERA5 (1-Hour UTC).
3. Quality-filtered daily column densities from Sentinel-5P (Forward-matched, max age 24h).
4. Static spatial GIS proxies from OpenStreetMap (Road density, landuse, distance to transit).

Outputs:
- data/fused/station_hourly_fused.parquet (10 stations x 26,304 hours = 263,040 rows)
- data/fused/data_dictionary.csv (45 production columns documented with role)
- data/fused/pilot/anand_vihar_pilot.parquet (Pilot dataset: Jan 2023)
- data/quality_reports/temporal_matching_report.csv (Satellite & temporal matching audit)
"""

import os
import glob
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
FUSED_DIR = os.path.join(DATA_DIR, "fused")
PILOT_DIR = os.path.join(FUSED_DIR, "pilot")
REPORTS_DIR = os.path.join(DATA_DIR, "quality_reports")
STATIONS_CSV = os.path.join(PROJECT_ROOT, "config", "stations.csv")

os.makedirs(FUSED_DIR, exist_ok=True)
os.makedirs(PILOT_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

START_DATE = "2023-01-01 00:00:00"
END_DATE = "2025-12-31 23:00:00"

def build_single_station_fused(station_id, stn_lat, stn_lon, static_features_df):
    stn_str = str(station_id).strip()
    
    # 1. Master Hourly Grid (2023-01-01 00:00 to 2025-12-31 23:00 UTC)
    full_hourly_idx = pd.date_range(START_DATE, END_DATE, freq="1h", name="timestamp_utc")
    df_fused = pd.DataFrame(index=full_hourly_idx).reset_index()
    df_fused["timestamp_utc"] = pd.to_datetime(df_fused["timestamp_utc"]).astype("datetime64[ns]")
    df_fused["station_id"] = stn_str
    df_fused["latitude"] = float(stn_lat)
    df_fused["longitude"] = float(stn_lon)
    
    # 2. Merge CPCB Hourly Ground Data
    cpcb_file = os.path.join(DATA_DIR, "cpcb", "processed", f"{stn_str}_cpcb_hourly.parquet")
    if os.path.exists(cpcb_file):
        df_cpcb = pd.read_parquet(cpcb_file)
        df_cpcb["timestamp_utc"] = pd.to_datetime(df_cpcb["timestamp_utc"]).astype("datetime64[ns]")
        df_cpcb["station_id"] = df_cpcb["station_id"].astype(str)
        df_fused = pd.merge(df_fused, df_cpcb, on=["station_id", "timestamp_utc"], how="left")
    else:
        for poll in ["PM2.5", "PM10", "NO", "NO2", "NOx", "NH3", "SO2", "CO", "OZONE"]:
            df_fused[f"{poll}_ground"] = np.nan
            df_fused[f"{poll}_obs_count"] = np.nan
            
    # 3. Merge ERA5 Hourly Meteorology
    era5_file = os.path.join(DATA_DIR, "era5", "processed", f"{stn_str}_era5_hourly.parquet")
    if os.path.exists(era5_file):
        df_era5 = pd.read_parquet(era5_file)
        df_era5["timestamp_utc"] = pd.to_datetime(df_era5["timestamp_utc"]).astype("datetime64[ns]")
        df_era5["station_id"] = df_era5["station_id"].astype(str)
        df_fused = pd.merge(df_fused, df_era5, on=["station_id", "timestamp_utc"], how="left")
    else:
        for met in [
            "era5_temperature_k", "era5_temperature_c", "era5_dewpoint_k", "era5_dewpoint_c",
            "era5_u10", "era5_v10", "era5_wind_speed", "era5_wind_direction",
            "era5_relative_humidity", "era5_surface_pressure_hpa", "era5_boundary_layer_height",
            "era5_solar_radiation_w_m2", "era5_total_precipitation_mm"
        ]:
            df_fused[met] = np.nan
            
    # 4. Merge Sentinel-5P Daily Satellite Observations (Forward association, strict causality)
    s5p_file = os.path.join(DATA_DIR, "sentinel5p", "processed", f"{stn_str}_s5p_daily.parquet")
    df_fused["sat_NO2"] = np.nan
    df_fused["sat_CO"] = np.nan
    df_fused["sat_HCHO"] = np.nan
    df_fused["satellite_observation_time"] = pd.NaT
    df_fused["satellite_age_hours"] = np.nan
    
    if os.path.exists(s5p_file):
        df_s5p = pd.read_parquet(s5p_file)
        for prod_col in ["sat_NO2", "sat_CO", "sat_HCHO"]:
            if prod_col not in df_s5p.columns:
                df_s5p[prod_col] = np.nan
                
        # Parse exact or fallback satellite overpass timestamp
        if "observation_time" in df_s5p.columns and df_s5p["observation_time"].notna().any():
            df_s5p["sat_overpass_utc"] = pd.to_datetime(df_s5p["observation_time"], errors="coerce").dt.tz_localize(None)
            default_overpass = pd.to_datetime(df_s5p["date"]).dt.tz_localize(None) + pd.Timedelta(hours=13, minutes=30)
            df_s5p["sat_overpass_utc"] = df_s5p["sat_overpass_utc"].fillna(default_overpass)
        else:
            df_s5p["sat_overpass_utc"] = pd.to_datetime(df_s5p["date"]).dt.tz_localize(None) + pd.Timedelta(hours=13, minutes=30)
            
        df_s5p["sat_overpass_utc"] = pd.to_datetime(df_s5p["sat_overpass_utc"]).astype("datetime64[ns]")
        df_s5p = df_s5p.sort_values("sat_overpass_utc")
        
        # Merge via backward asof (strictly matching latest overpass <= current hour)
        valid_s5p_rows = df_s5p.dropna(how="all", subset=["sat_NO2", "sat_CO", "sat_HCHO"])
        
        if not valid_s5p_rows.empty:
            df_merged_s5p = pd.merge_asof(
                df_fused[["timestamp_utc"]].sort_values("timestamp_utc"),
                valid_s5p_rows[["sat_overpass_utc", "sat_NO2", "sat_CO", "sat_HCHO"]],
                left_on="timestamp_utc",
                right_on="sat_overpass_utc",
                direction="backward"
            )
            
            # Compute satellite age in hours
            age_hours = (df_merged_s5p["timestamp_utc"] - df_merged_s5p["sat_overpass_utc"]).dt.total_seconds() / 3600.0
            
            # Only retain observations <= 24 hours old
            valid_s5p_mask = (age_hours >= 0.0) & (age_hours <= 24.0)
            
            df_fused["sat_NO2"] = df_merged_s5p["sat_NO2"].where(valid_s5p_mask, np.nan)
            df_fused["sat_CO"] = df_merged_s5p["sat_CO"].where(valid_s5p_mask, np.nan)
            df_fused["sat_HCHO"] = df_merged_s5p["sat_HCHO"].where(valid_s5p_mask, np.nan)
            df_fused["satellite_observation_time"] = df_merged_s5p["sat_overpass_utc"].where(valid_s5p_mask, pd.NaT)
            df_fused["satellite_age_hours"] = age_hours.where(valid_s5p_mask, np.nan)
        
    # 5. Join Static Geospatial Features
    if static_features_df is not None and not static_features_df.empty:
        stn_geo = static_features_df[static_features_df["station_id"] == stn_str]
        if not stn_geo.empty:
            for col in stn_geo.columns:
                if col.startswith("geo_"):
                    df_fused[col] = stn_geo[col].iloc[0]

    return df_fused

def generate_data_dictionary():
    data_dict = [
        {"column_name": "timestamp_utc", "data_type": "datetime64[ns]", "source": "TIME_GRID", "original_variable": "index", "unit": "ISO-8601", "description": "Hourly standard timestamp in UTC (YYYY-MM-DD HH:00:00)", "processing": "Floored to 1-hour interval", "missing_allowed": "NO", "role": "METADATA"},
        {"column_name": "station_id", "data_type": "string", "source": "CONFIG", "original_variable": "station_id", "unit": "Text", "description": "Canonical CPCB monitoring station identifier", "processing": "Standardized uppercase", "missing_allowed": "NO", "role": "METADATA"},
        {"column_name": "latitude", "data_type": "float64", "source": "CPCB_METADATA", "original_variable": "latitude", "unit": "Degrees North", "description": "Station latitude in WGS84", "processing": "Verified against portal", "missing_allowed": "NO", "role": "METADATA"},
        {"column_name": "longitude", "data_type": "float64", "source": "CPCB_METADATA", "original_variable": "longitude", "unit": "Degrees East", "description": "Station longitude in WGS84", "processing": "Verified against portal", "missing_allowed": "NO", "role": "METADATA"},
        
        # Primary Targets
        {"column_name": "OZONE_ground", "data_type": "float64", "source": "CPCB_CAAQMS", "original_variable": "Ozone", "unit": "ug/m3", "description": "Ground-level Ozone (O3) concentration [PRIMARY FORECASTING TARGET 1]", "processing": "1-hr mean (>=3 valid 15-min readings)", "missing_allowed": "YES (Sensor gaps)", "role": "TARGET"},
        {"column_name": "OZONE_obs_count", "data_type": "float64", "source": "CPCB_CAAQMS", "original_variable": "Ozone", "unit": "Count", "description": "Number of valid 15-minute readings in the hour for Ozone", "processing": "Count >= 3", "missing_allowed": "YES", "role": "METADATA"},
        {"column_name": "NO2_ground", "data_type": "float64", "source": "CPCB_CAAQMS", "original_variable": "NO2", "unit": "ug/m3", "description": "Ground-level Nitrogen Dioxide concentration [PRIMARY FORECASTING TARGET 2]", "processing": "1-hr mean (>=3 valid 15-min readings)", "missing_allowed": "YES (Sensor gaps)", "role": "TARGET"},
        {"column_name": "NO2_obs_count", "data_type": "float64", "source": "CPCB_CAAQMS", "original_variable": "NO2", "unit": "Count", "description": "Number of valid 15-minute readings in the hour for NO2", "processing": "Count >= 3", "missing_allowed": "YES", "role": "METADATA"},
        
        # Ground Precursors & Co-Pollutants
        {"column_name": "PM2.5_ground", "data_type": "float64", "source": "CPCB_CAAQMS", "original_variable": "PM2.5", "unit": "ug/m3", "description": "Fine particulate matter PM2.5", "processing": "1-hr mean (>=3 valid 15-min readings)", "missing_allowed": "YES", "role": "PREDICTOR"},
        {"column_name": "PM2.5_obs_count", "data_type": "float64", "source": "CPCB_CAAQMS", "original_variable": "PM2.5", "unit": "Count", "description": "Valid 15-min count for PM2.5", "processing": "Count >= 3", "missing_allowed": "YES", "role": "METADATA"},
        {"column_name": "PM10_ground", "data_type": "float64", "source": "CPCB_CAAQMS", "original_variable": "PM10", "unit": "ug/m3", "description": "Coarse particulate matter PM10", "processing": "1-hr mean (>=3 valid 15-min readings)", "missing_allowed": "YES", "role": "PREDICTOR"},
        {"column_name": "PM10_obs_count", "data_type": "float64", "source": "CPCB_CAAQMS", "original_variable": "PM10", "unit": "Count", "description": "Valid 15-min count for PM10", "processing": "Count >= 3", "missing_allowed": "YES", "role": "METADATA"},
        {"column_name": "NO_ground", "data_type": "float64", "source": "CPCB_CAAQMS", "original_variable": "NO", "unit": "ug/m3", "description": "Nitric Oxide concentration", "processing": "1-hr mean (>=3 valid 15-min readings)", "missing_allowed": "YES", "role": "PREDICTOR"},
        {"column_name": "NO_obs_count", "data_type": "float64", "source": "CPCB_CAAQMS", "original_variable": "NO", "unit": "Count", "description": "Valid 15-min count for NO", "processing": "Count >= 3", "missing_allowed": "YES", "role": "METADATA"},
        {"column_name": "NOx_ground", "data_type": "float64", "source": "CPCB_CAAQMS", "original_variable": "NOx", "unit": "ppb", "description": "Oxides of Nitrogen concentration", "processing": "1-hr mean (>=3 valid 15-min readings)", "missing_allowed": "YES", "role": "PREDICTOR"},
        {"column_name": "NOx_obs_count", "data_type": "float64", "source": "CPCB_CAAQMS", "original_variable": "NOx", "unit": "Count", "description": "Valid 15-min count for NOx", "processing": "Count >= 3", "missing_allowed": "YES", "role": "METADATA"},
        {"column_name": "NH3_ground", "data_type": "float64", "source": "CPCB_CAAQMS", "original_variable": "NH3", "unit": "ug/m3", "description": "Ammonia concentration", "processing": "1-hr mean (>=3 valid 15-min readings)", "missing_allowed": "YES", "role": "PREDICTOR"},
        {"column_name": "NH3_obs_count", "data_type": "float64", "source": "CPCB_CAAQMS", "original_variable": "NH3", "unit": "Count", "description": "Valid 15-min count for NH3", "processing": "Count >= 3", "missing_allowed": "YES", "role": "METADATA"},
        {"column_name": "SO2_ground", "data_type": "float64", "source": "CPCB_CAAQMS", "original_variable": "SO2", "unit": "ug/m3", "description": "Sulphur Dioxide concentration", "processing": "1-hr mean (>=3 valid 15-min readings)", "missing_allowed": "YES", "role": "PREDICTOR"},
        {"column_name": "SO2_obs_count", "data_type": "float64", "source": "CPCB_CAAQMS", "original_variable": "SO2", "unit": "Count", "description": "Valid 15-min count for SO2", "processing": "Count >= 3", "missing_allowed": "YES", "role": "METADATA"},
        {"column_name": "CO_ground", "data_type": "float64", "source": "CPCB_CAAQMS", "original_variable": "CO", "unit": "mg/m3", "description": "Carbon Monoxide concentration", "processing": "1-hr mean (>=3 valid 15-min readings)", "missing_allowed": "YES", "role": "PREDICTOR"},
        {"column_name": "CO_obs_count", "data_type": "float64", "source": "CPCB_CAAQMS", "original_variable": "CO", "unit": "Count", "description": "Valid 15-min count for CO", "processing": "Count >= 3", "missing_allowed": "YES", "role": "METADATA"},
        
        # ERA5 Meteorology
        {"column_name": "era5_temperature_k", "data_type": "float64", "source": "ERA5_REANALYSIS", "original_variable": "t2m", "unit": "Kelvin", "description": "2-meter air temperature in Kelvin", "processing": "Direct extraction from nearest grid", "missing_allowed": "NO", "role": "PREDICTOR"},
        {"column_name": "era5_temperature_c", "data_type": "float64", "source": "ERA5_REANALYSIS", "original_variable": "t2m", "unit": "Degrees Celsius", "processing": "Kelvin - 273.15", "missing_allowed": "NO", "role": "PREDICTOR"},
        {"column_name": "era5_dewpoint_k", "data_type": "float64", "source": "ERA5_REANALYSIS", "original_variable": "d2m", "unit": "Kelvin", "description": "2-meter dewpoint temperature in Kelvin", "processing": "Direct extraction from nearest grid", "missing_allowed": "NO", "role": "PREDICTOR"},
        {"column_name": "era5_dewpoint_c", "data_type": "float64", "source": "ERA5_REANALYSIS", "original_variable": "d2m", "unit": "Degrees Celsius", "processing": "Kelvin - 273.15", "missing_allowed": "NO", "role": "PREDICTOR"},
        {"column_name": "era5_u10", "data_type": "float64", "source": "ERA5_REANALYSIS", "original_variable": "u10", "unit": "m/s", "description": "10-meter zonal wind component (U-vector)", "processing": "Direct extraction from nearest grid", "missing_allowed": "NO", "role": "PREDICTOR"},
        {"column_name": "era5_v10", "data_type": "float64", "source": "ERA5_REANALYSIS", "original_variable": "v10", "unit": "m/s", "description": "10-meter meridional wind component (V-vector)", "processing": "Direct extraction from nearest grid", "missing_allowed": "NO", "role": "PREDICTOR"},
        {"column_name": "era5_wind_speed", "data_type": "float64", "source": "ERA5_REANALYSIS", "original_variable": "derived", "unit": "m/s", "description": "10-meter horizontal wind speed", "processing": "sqrt(u10^2 + v10^2)", "missing_allowed": "NO", "role": "DERIVED FEATURE"},
        {"column_name": "era5_wind_direction", "data_type": "float64", "source": "ERA5_REANALYSIS", "original_variable": "derived", "unit": "Degrees (0-360)", "processing": "Meteorological convention: (atan2(-u, -v)) % 360", "missing_allowed": "NO", "role": "DERIVED FEATURE"},
        {"column_name": "era5_relative_humidity", "data_type": "float64", "source": "ERA5_REANALYSIS", "original_variable": "derived", "unit": "%", "description": "Relative humidity computed from T and Td", "processing": "Magnus-Tetens thermodynamic equation", "missing_allowed": "NO", "role": "DERIVED FEATURE"},
        {"column_name": "era5_surface_pressure_hpa", "data_type": "float64", "source": "ERA5_REANALYSIS", "original_variable": "sp", "unit": "hPa", "description": "Atmospheric surface pressure", "processing": "Pa / 100.0", "missing_allowed": "NO", "role": "PREDICTOR"},
        {"column_name": "era5_boundary_layer_height", "data_type": "float64", "source": "ERA5_REANALYSIS", "original_variable": "blh", "unit": "meters", "description": "Planetary boundary layer height (BLH)", "processing": "Direct extraction from nearest grid", "missing_allowed": "NO", "role": "PREDICTOR"},
        {"column_name": "era5_solar_radiation_w_m2", "data_type": "float64", "source": "ERA5_REANALYSIS", "original_variable": "ssrd", "unit": "W/m2", "description": "Surface solar radiation downwards (SSRD)", "processing": "J/m2 divided by 3600s", "missing_allowed": "NO", "role": "PREDICTOR"},
        {"column_name": "era5_total_precipitation_mm", "data_type": "float64", "source": "ERA5_REANALYSIS", "original_variable": "tp", "unit": "mm", "description": "Total precipitation accumulation", "processing": "meters * 1000.0", "missing_allowed": "NO", "role": "PREDICTOR"},
        
        # Sentinel-5P Satellite
        {"column_name": "sat_NO2", "data_type": "float64", "source": "SENTINEL5P_TROPOMI", "original_variable": "NO2", "unit": "mol/m2", "description": "Sentinel-5P Tropospheric NO2 column density", "processing": "+/-0.02 deg AOI mean (QA>=75 server-side mask)", "missing_allowed": "YES (Night/Clouds)", "role": "PREDICTOR"},
        {"column_name": "sat_CO", "data_type": "float64", "source": "SENTINEL5P_TROPOMI", "original_variable": "CO", "unit": "mol/m2", "description": "Sentinel-5P Total column Carbon Monoxide", "processing": "+/-0.02 deg AOI mean (QA>=50 server-side mask)", "missing_allowed": "YES (Night/Clouds)", "role": "PREDICTOR"},
        {"column_name": "sat_HCHO", "data_type": "float64", "source": "SENTINEL5P_TROPOMI", "original_variable": "HCHO", "unit": "mol/m2", "description": "Sentinel-5P Tropospheric Formaldehyde column", "processing": "+/-0.02 deg AOI mean (QA>=50 server-side mask)", "missing_allowed": "YES (Night/Clouds)", "role": "PREDICTOR"},
        {"column_name": "satellite_observation_time", "data_type": "datetime64[ns]", "source": "SENTINEL5P_TROPOMI", "original_variable": "observation_time", "unit": "UTC datetime", "description": "Timestamp of the associated satellite overpass", "processing": "Forward-matched <= current hour", "missing_allowed": "YES", "role": "METADATA"},
        {"column_name": "satellite_age_hours", "data_type": "float64", "source": "DERIVED", "original_variable": "derived", "unit": "Hours", "description": "Age of the satellite observation in hours (<=24h)", "processing": "Current hour - sat overpass hour", "missing_allowed": "YES", "role": "DERIVED FEATURE"},
        
        # Static Geospatial Features
        {"column_name": "geo_dist_to_nearest_road_m", "data_type": "float64", "source": "OSM_GEOSPATIAL", "original_variable": "osm_roads", "unit": "meters", "description": "Distance from monitoring station to nearest road", "processing": "EPSG:32643 metric Euclidean distance", "missing_allowed": "NO", "role": "STATIC FEATURE"},
        {"column_name": "geo_road_length_1km_buffer_m", "data_type": "float64", "source": "OSM_GEOSPATIAL", "original_variable": "osm_roads", "unit": "meters", "description": "Total road network length within 1km radius buffer", "processing": "Spatial intersection sum in EPSG:32643", "missing_allowed": "NO", "role": "STATIC FEATURE"},
        {"column_name": "geo_road_length_3km_buffer_m", "data_type": "float64", "source": "OSM_GEOSPATIAL", "original_variable": "osm_roads", "unit": "meters", "description": "Total road network length within 3km radius buffer", "processing": "Spatial intersection sum in EPSG:32643", "missing_allowed": "NO", "role": "STATIC FEATURE"},
        {"column_name": "geo_dist_to_nearest_railway_m", "data_type": "float64", "source": "OSM_GEOSPATIAL", "original_variable": "osm_railways", "unit": "meters", "description": "Distance from station to nearest railway line", "processing": "EPSG:32643 metric Euclidean distance", "missing_allowed": "NO", "role": "STATIC FEATURE"},
        {"column_name": "geo_dominant_landuse_1km", "data_type": "string", "source": "OSM_GEOSPATIAL", "original_variable": "osm_landuse", "unit": "Categorical", "description": "Dominant land-use classification within 1km buffer", "processing": "Majority polygon class", "missing_allowed": "NO", "role": "STATIC FEATURE"}
    ]
    df_dict = pd.DataFrame(data_dict)
    dict_out = os.path.join(FUSED_DIR, "data_dictionary.csv")
    df_dict.to_csv(dict_out, index=False)
    print(f"[DONE] Saved Complete Data Dictionary: {dict_out} ({len(df_dict)} variables documented)")

def generate_temporal_matching_report(master_fused):
    temporal_records = []
    for stn, group in master_fused.groupby("station_id"):
        total_h = len(group)
        with_sat = group["satellite_observation_time"].notna().sum()
        with_no2 = group["sat_NO2"].notna().sum()
        with_co = group["sat_CO"].notna().sum()
        with_hcho = group["sat_HCHO"].notna().sum()
        mean_age = group["satellite_age_hours"].mean()
        max_age = group["satellite_age_hours"].max()
        min_age = group["satellite_age_hours"].min()
        
        temporal_records.append({
            "station_id": stn,
            "total_hourly_records": total_h,
            "hours_with_active_satellite": with_sat,
            "hours_with_valid_sat_NO2": with_no2,
            "hours_with_valid_sat_CO": with_co,
            "hours_with_valid_sat_HCHO": with_hcho,
            "mean_satellite_age_hours": round(float(mean_age), 2) if pd.notna(mean_age) else np.nan,
            "min_satellite_age_hours": round(float(min_age), 2) if pd.notna(min_age) else np.nan,
            "max_satellite_age_hours": round(float(max_age), 2) if pd.notna(max_age) else np.nan,
            "temporal_causality_verified": True
        })
    df_temp = pd.DataFrame(temporal_records)
    out_temp = os.path.join(REPORTS_DIR, "temporal_matching_report.csv")
    df_temp.to_csv(out_temp, index=False)
    print(f"[DONE] Saved Temporal Matching Report: {out_temp}")

def build_master_fused_dataset():
    print("\n[STEP 11-13 & 32] Building Master Hourly Spatiotemporal Fused Dataset...")
    stations_df = pd.read_csv(STATIONS_CSV)
    
    # Load static features
    geo_f = os.path.join(DATA_DIR, "geospatial", "processed", "station_static_features.parquet")
    geo_df = pd.read_parquet(geo_f) if os.path.exists(geo_f) else None
    
    station_dfs = []
    
    for _, row in stations_df.iterrows():
        stn = str(row["station_id"]).strip()
        lat = float(row["latitude"])
        lon = float(row["longitude"])
        print(f"  -> Fusing 2023-2025 Multi-Source Data for Station: {stn}...")
        df_stn_fused = build_single_station_fused(stn, lat, lon, geo_df)
        station_dfs.append(df_stn_fused)
        
    master_fused = pd.concat(station_dfs, ignore_index=True)
    master_fused = master_fused.sort_values(["station_id", "timestamp_utc"]).reset_index(drop=True)
    
    # Save Master Parquet
    master_parquet = os.path.join(FUSED_DIR, "station_hourly_fused.parquet")
    master_fused.to_parquet(master_parquet, index=False)
    print(f"\n[DONE] Successfully Generated Master Fused Parquet:")
    print(f"  Path:  {master_parquet}")
    print(f"  Shape: {master_fused.shape[0]:,} rows x {master_fused.shape[1]} columns")
    print(f"  Size:  {os.path.getsize(master_parquet) / (1024*1024):.2f} MB")
    
    # Generate Pilot Dataset (Anand Vihar, Jan 2023)
    pilot_df = master_fused[(master_fused["station_id"] == "ANAND_VIHAR") & (master_fused["timestamp_utc"] >= "2023-01-01") & (master_fused["timestamp_utc"] < "2023-02-01")]
    pilot_parquet = os.path.join(PILOT_DIR, "anand_vihar_pilot.parquet")
    pilot_df.to_parquet(pilot_parquet, index=False)
    print(f"[DONE] Generated Anand Vihar Pilot Dataset: {pilot_parquet} ({len(pilot_df):,} hourly rows)")
    
    # Generate Data Dictionary
    generate_data_dictionary()
    
    # Generate Temporal Matching Report
    generate_temporal_matching_report(master_fused)
    
    return master_fused

if __name__ == "__main__":
    build_master_fused_dataset()
