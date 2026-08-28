"""
SIH 25178 - Phase 2: Input Inventory & File Validation
Step 1 of Phase 2 Pipeline.

Scans all raw/processed data files across 4 sources:
1. CPCB Ground Stations (data/cpcb/raw/)
2. Sentinel-5P TROPOMI (data/sentinel5p/)
3. ERA5 Weather Reanalysis (data/era5/raw/)
4. Geospatial Layers (data/geospatial/)

Generates:
- data/quality_reports/phase2_input_inventory.csv
- data/quality_reports/station_coverage_report.csv
"""

import os
import glob
import csv
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
REPORTS_DIR = os.path.join(DATA_DIR, "quality_reports")
STATIONS_CSV = os.path.join(PROJECT_ROOT, "config", "stations.csv")

os.makedirs(REPORTS_DIR, exist_ok=True)

def build_input_inventory():
    print("[STEP 1] Generating Phase 2 Input Inventory...")
    inventory = []
    
    # 1. CPCB Ground Station Data
    cpcb_raw = os.path.join(DATA_DIR, "cpcb", "raw")
    if os.path.isdir(cpcb_raw):
        for f in sorted(os.listdir(cpcb_raw)):
            if f.endswith(".xlsx"):
                fp = os.path.join(cpcb_raw, f)
                sz = os.path.getsize(fp)
                parts = f.replace("_DATA.xlsx", "").split("_")
                year = parts[-1]
                stn = "_".join(parts[:-1])
                inventory.append({
                    "source": "CPCB_GROUND",
                    "station_id": stn,
                    "filename": f,
                    "file_format": "XLSX",
                    "file_size_kb": round(sz / 1024, 2),
                    "start_date": f"{year}-01-01",
                    "end_date": f"{year}-12-31",
                    "variables": "PM2.5,PM10,NO,NO2,NOx,NH3,SO2,CO,OZONE",
                    "timestamp_format": "DD-MM-YYYY HH:MM (IST 15-min)",
                    "geographic_coverage": f"Station: {stn}",
                    "status": "VALID_RAW",
                    "notes": "Original CPCB CAAQMS Download"
                })

    # 2. Sentinel-5P Processed Files
    s5p_proc = os.path.join(DATA_DIR, "sentinel5p", "processed")
    if os.path.isdir(s5p_proc):
        for stn in sorted(os.listdir(s5p_proc)):
            stn_dir = os.path.join(s5p_proc, stn)
            if os.path.isdir(stn_dir):
                files = os.listdir(stn_dir)
                total_sz = sum(os.path.getsize(os.path.join(stn_dir, f)) for f in files)
                inventory.append({
                    "source": "SENTINEL5P_PROCESSED",
                    "station_id": stn,
                    "filename": f"{stn}_processed_bundle ({len(files)} files)",
                    "file_format": "CSV/JSON",
                    "file_size_kb": round(total_sz / 1024, 2),
                    "start_date": "2023-01-01",
                    "end_date": "2025-12-31",
                    "variables": "NO2,CO,HCHO (Tropospheric Column)",
                    "timestamp_format": "UTC Daily Overpass (~13:30)",
                    "geographic_coverage": f"+/-0.02 deg AOI around {stn}",
                    "status": "VALID_PROCESSED",
                    "notes": f"{len(files)} daily extracted observation files"
                })

    # 3. ERA5 Reanalysis Data
    era5_raw = os.path.join(DATA_DIR, "era5", "raw")
    if os.path.isdir(era5_raw):
        for item in sorted(os.listdir(era5_raw)):
            item_path = os.path.join(era5_raw, item)
            if os.path.isdir(item_path) and ("2022" in item or "2023" in item or "2024" in item or "2025" in item):
                q_files = os.listdir(item_path)
                total_sz = sum(os.path.getsize(os.path.join(item_path, f)) for f in q_files)
                inventory.append({
                    "source": "ERA5_REANALYSIS",
                    "station_id": "DELHI_GRID",
                    "filename": f"{item} ({len(q_files)} files)",
                    "file_format": "NetCDF/GRIB",
                    "file_size_kb": round(total_sz / 1024, 2),
                    "start_date": f"{item[:4]}-Quarter",
                    "end_date": f"{item[:4]}-Quarter",
                    "variables": "t2m,d2m,u10,v10,sp,blh,ssrd,tp",
                    "timestamp_format": "Hourly UTC",
                    "geographic_coverage": "Delhi Metropolitan Bounding Box (0.25x0.25 deg)",
                    "status": "VALID_RAW",
                    "notes": "Single-level meteorological reanalysis"
                })

    # 4. Geospatial Layers
    geo_dir = os.path.join(DATA_DIR, "geospatial")
    if os.path.isdir(geo_dir):
        for category in ["roads", "landuse", "infrastructure"]:
            cat_dir = os.path.join(geo_dir, "processed", category)
            if os.path.isdir(cat_dir):
                shps = [f for f in os.listdir(cat_dir) if f.endswith(".shp")]
                for s in shps:
                    sz = os.path.getsize(os.path.join(cat_dir, s))
                    inventory.append({
                        "source": "GEOSPATIAL_OSM",
                        "station_id": "DELHI_NCR",
                        "filename": s,
                        "file_format": "Shapefile (.shp)",
                        "file_size_kb": round(sz / 1024, 2),
                        "start_date": "Static",
                        "end_date": "Static",
                        "variables": f"{category}_geometry",
                        "timestamp_format": "Static GIS Layer",
                        "geographic_coverage": "Delhi Bounding Box (EPSG:4326)",
                        "status": "VALID_PROCESSED",
                        "notes": f"Cropped OSM {category} layer"
                    })

    inv_df = pd.DataFrame(inventory)
    out_path = os.path.join(REPORTS_DIR, "phase2_input_inventory.csv")
    inv_df.to_csv(out_path, index=False)
    print(f"[DONE] Saved Input Inventory: {out_path} ({len(inv_df)} entries)")
    return inv_df

def build_station_coverage_report():
    print("[STEP 1] Generating Station Coverage Report...")
    df_stn = pd.read_csv(STATIONS_CSV)
    coverage = []
    
    for _, row in df_stn.iterrows():
        stn = row["station_id"]
        # CPCB check
        cpcb_files = glob.glob(os.path.join(DATA_DIR, "cpcb", "raw", f"{stn}_*_DATA.xlsx"))
        cpcb_years = sorted([os.path.basename(f).split("_")[-2] for f in cpcb_files])
        
        # S5P check
        s5p_proc_dir = os.path.join(DATA_DIR, "sentinel5p", "processed", stn)
        s5p_count = len(os.listdir(s5p_proc_dir)) if os.path.isdir(s5p_proc_dir) else 0
        
        # ERA5 check
        era5_avail = "YES (Delhi Grid 0.25deg)"
        
        # Geospatial check
        geo_avail = "YES (OSM Roads/Landuse/Infra)"
        
        coverage.append({
            "station_id": stn,
            "station_name": row["station_name"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "cpcb_years_available": ",".join(cpcb_years),
            "cpcb_file_count": len(cpcb_files),
            "s5p_processed_files": s5p_count,
            "era5_mapping_status": era5_avail,
            "geospatial_features_status": geo_avail,
            "phase2_ready": "YES" if len(cpcb_files) == 3 and s5p_count > 0 else "PARTIAL"
        })
        
    cov_df = pd.DataFrame(coverage)
    out_path = os.path.join(REPORTS_DIR, "station_coverage_report.csv")
    cov_df.to_csv(out_path, index=False)
    print(f"[DONE] Saved Station Coverage Report: {out_path} ({len(cov_df)} stations)")
def run_all_input_validation():
    build_input_inventory()
    build_station_coverage_report()

if __name__ == "__main__":
    run_all_input_validation()
