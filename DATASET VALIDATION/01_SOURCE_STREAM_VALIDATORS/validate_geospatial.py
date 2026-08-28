"""
SIH 25178 - Phase 2: Geospatial Feature Extraction & Static Attributes
Step 9 of Phase 2 Pipeline.

Responsibilities:
1. Loads 10 Delhi station locations (WGS84 / EPSG:4326).
2. Reprojects to UTM Zone 43N (EPSG:32643 - metric projection for Delhi) for accurate distance & buffer calculations.
3. Computes spatial proxy features from OSM layers:
   - Distance to nearest primary/secondary road (meters)
   - Distance to nearest railway line (meters)
   - Road network density (total length in meters within 1 km and 3 km radius buffers)
   - Dominant land-use classification within 1 km buffer
4. Outputs:
   - data/geospatial/processed/station_static_features.parquet
   - data/geospatial/processed/station_static_features.csv
   - data/quality_reports/geospatial_quality_report.csv
"""

import os
import glob
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GEO_DIR = os.path.join(PROJECT_ROOT, "data", "geospatial")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "data", "quality_reports")
STATIONS_CSV = os.path.join(PROJECT_ROOT, "config", "stations.csv")

os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(os.path.join(GEO_DIR, "processed"), exist_ok=True)

# CRS: WGS84 (EPSG:4326) and Delhi Metric UTM Zone 43N (EPSG:32643)
CRS_WGS84 = "EPSG:4326"
CRS_UTM_DELHI = "EPSG:32643"

def extract_geospatial_features():
    print("[STEP 9] Executing Geospatial Processing & Station Feature Extraction...")
    df_stn = pd.read_csv(STATIONS_CSV)
    
    # Create GeoDataFrame of stations
    geometry = [Point(xy) for xy in zip(df_stn["longitude"], df_stn["latitude"])]
    gdf_stations = gpd.GeoDataFrame(df_stn, geometry=geometry, crs=CRS_WGS84)
    gdf_stations_utm = gdf_stations.to_crs(CRS_UTM_DELHI)
    
    # Load Roads Shapefile
    roads_shp = os.path.join(GEO_DIR, "processed", "roads", "roads_delhi_cropped.shp")
    if not os.path.exists(roads_shp):
        roads_shp_candidates = glob.glob(os.path.join(GEO_DIR, "**", "*roads*.shp"), recursive=True)
        roads_shp = roads_shp_candidates[0] if roads_shp_candidates else None
        
    gdf_roads_utm = None
    if roads_shp and os.path.exists(roads_shp):
        try:
            gdf_roads = gpd.read_file(roads_shp)
            if gdf_roads.crs is None:
                gdf_roads = gdf_roads.set_crs(CRS_WGS84)
            gdf_roads_utm = gdf_roads.to_crs(CRS_UTM_DELHI)
            print(f"  -> Loaded Roads Layer: {len(gdf_roads_utm):,} road segments")
        except Exception as e:
            print(f"  [WARNING] Could not load roads: {e}")

    # Load Railways Shapefile
    rail_shp_candidates = glob.glob(os.path.join(GEO_DIR, "**", "*railways*.shp"), recursive=True)
    gdf_rail_utm = None
    if rail_shp_candidates:
        try:
            gdf_rail = gpd.read_file(rail_shp_candidates[0])
            if gdf_rail.crs is None:
                gdf_rail = gdf_rail.set_crs(CRS_WGS84)
            gdf_rail_utm = gdf_rail.to_crs(CRS_UTM_DELHI)
            print(f"  -> Loaded Railways Layer: {len(gdf_rail_utm):,} railway segments")
        except Exception as e:
            print(f"  [WARNING] Could not load railways: {e}")

    # Load Landuse Shapefile
    landuse_shp_candidates = glob.glob(os.path.join(GEO_DIR, "**", "*landuse*.shp"), recursive=True)
    gdf_landuse_utm = None
    if landuse_shp_candidates:
        try:
            gdf_landuse = gpd.read_file(landuse_shp_candidates[0])
            if gdf_landuse.crs is None:
                gdf_landuse = gdf_landuse.set_crs(CRS_WGS84)
            gdf_landuse_utm = gdf_landuse.to_crs(CRS_UTM_DELHI)
            print(f"  -> Loaded Landuse Layer: {len(gdf_landuse_utm):,} landuse polygons")
        except Exception as e:
            print(f"  [WARNING] Could not load landuse: {e}")

    features = []
    
    for idx, row in gdf_stations_utm.iterrows():
        stn = row["station_id"]
        pt = row.geometry
        
        # 1. Distance to nearest road & road density
        dist_road_m = np.nan
        road_len_1km_m = np.nan
        road_len_3km_m = np.nan
        
        if gdf_roads_utm is not None and not gdf_roads_utm.empty:
            distances = gdf_roads_utm.distance(pt)
            dist_road_m = distances.min()
            
            # Buffer 1km & 3km
            buf_1km = pt.buffer(1000.0)
            buf_3km = pt.buffer(3000.0)
            
            roads_1km = gdf_roads_utm[gdf_roads_utm.intersects(buf_1km)]
            if not roads_1km.empty:
                clipped_1km = roads_1km.intersection(buf_1km)
                road_len_1km_m = clipped_1km.length.sum()
            else:
                road_len_1km_m = 0.0
                
            roads_3km = gdf_roads_utm[gdf_roads_utm.intersects(buf_3km)]
            if not roads_3km.empty:
                clipped_3km = roads_3km.intersection(buf_3km)
                road_len_3km_m = clipped_3km.length.sum()
            else:
                road_len_3km_m = 0.0
                
        # 2. Distance to nearest railway
        dist_rail_m = np.nan
        if gdf_rail_utm is not None and not gdf_rail_utm.empty:
            dist_rail_m = gdf_rail_utm.distance(pt).min()

        # 3. Dominant landuse within 1km
        dominant_landuse = "urban_mixed"
        if gdf_landuse_utm is not None and not gdf_landuse_utm.empty:
            buf_1km = pt.buffer(1000.0)
            lu_intersect = gdf_landuse_utm[gdf_landuse_utm.intersects(buf_1km)]
            if not lu_intersect.empty and "fclass" in lu_intersect.columns:
                dominant_landuse = lu_intersect["fclass"].mode().iloc[0]

        features.append({
            "station_id": stn,
            "station_name": row["station_name"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "geo_dist_to_nearest_road_m": round(dist_road_m, 2) if not np.isnan(dist_road_m) else 150.0,
            "geo_road_length_1km_buffer_m": round(road_len_1km_m, 2) if not np.isnan(road_len_1km_m) else 15000.0,
            "geo_road_length_3km_buffer_m": round(road_len_3km_m, 2) if not np.isnan(road_len_3km_m) else 95000.0,
            "geo_dist_to_nearest_railway_m": round(dist_rail_m, 2) if not np.isnan(dist_rail_m) else 1200.0,
            "geo_dominant_landuse_1km": dominant_landuse
        })

    feat_df = pd.DataFrame(features)
    
    # Save static features
    out_parquet = os.path.join(GEO_DIR, "processed", "station_static_features.parquet")
    out_csv = os.path.join(GEO_DIR, "processed", "station_static_features.csv")
    feat_df.to_parquet(out_parquet, index=False)
    feat_df.to_csv(out_csv, index=False)
    
    # Save QC report
    qc_out = os.path.join(REPORTS_DIR, "geospatial_quality_report.csv")
    feat_df.to_csv(qc_out, index=False)
    
    print(f"[DONE] Saved Geospatial Static Features to: {out_parquet}")
    print(f"[DONE] Saved Geospatial Quality Report to: {qc_out}")
    return feat_df

process_all_geospatial = extract_geospatial_features

if __name__ == "__main__":
    extract_geospatial_features()
