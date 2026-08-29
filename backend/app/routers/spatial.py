"""
backend/app/routers/spatial.py
2D Continuous Spatial Pollution Heatmap for Delhi-NCR.

Generates a continuous spatial grid (GeoJSON FeatureCollection) using Inverse Distance
Weighting (IDW) interpolation across the 10 canonical stations.
"""

import numpy as np
from fastapi import APIRouter, Query
from backend.app.schemas.station import STATIONS_DATA
from backend.app.services.model_service import ModelService
from backend.app.utils.feature_builder import build_demo_feature_vector, get_ordered_feature_names

router = APIRouter(prefix="/api/v1/spatial", tags=["Spatial Analytics"])


@router.get("/heatmap")
def get_spatial_heatmap(
    horizon: int = Query(24, description="Forecast horizon in hours (1, 3, 6, 12, 24, 48)"),
    pollutant: str = Query("NO2", description="Target pollutant: NO2 or O3")
):
    """
    Returns a continuous 2D GeoJSON FeatureCollection across Delhi-NCR.
    Renders as an animated heat layer on Leaflet or Mapbox.
    """
    feature_names = get_ordered_feature_names()
    
    # 1. Get model predictions for all 10 stations at the requested horizon
    st_lats = []
    st_lons = []
    st_vals = []
    
    for st in STATIONS_DATA:
        st_id = st["station_id"]
        st_lats.append(st["latitude"])
        st_lons.append(st["longitude"])
        
        feats = build_demo_feature_vector(st_id, feature_names)
        preds = ModelService.predict(pollutant, st_id, feats)
        val = preds.get(horizon, 50.0)
        st_vals.append(val if val is not None else 50.0)
        
    st_lats = np.array(st_lats)
    st_lons = np.array(st_lons)
    st_vals = np.array(st_vals)
    
    # 2. Construct a 20x20 spatial grid over Delhi-NCR
    grid_lats = np.linspace(28.40, 28.85, 20)
    grid_lons = np.linspace(76.90, 77.40, 20)
    
    features = []
    for lat in grid_lats:
        for lon in grid_lons:
            # IDW Interpolation with p=2.0
            dists = np.sqrt((st_lats - lat)**2 + (st_lons - lon)**2)
            dists = np.maximum(dists, 0.005)
            weights = 1.0 / (dists ** 2)
            interpolated_val = float(np.sum(weights * st_vals) / np.sum(weights))
            
            # CPCB Color Ramp
            if interpolated_val < 40:
                color = "#00e400"
                category = "Good"
            elif interpolated_val < 80:
                color = "#92d050"
                category = "Satisfactory"
            elif interpolated_val < 180:
                color = "#ffff00"
                category = "Moderate"
            elif interpolated_val < 280:
                color = "#ff7e00"
                category = "Poor"
            elif interpolated_val < 400:
                color = "#ff0000"
                category = "Very Poor"
            else:
                color = "#7e0023"
                category = "Severe"
                
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [round(lon, 4), round(lat, 4)]
                },
                "properties": {
                    "concentration_ug_m3": round(interpolated_val, 2),
                    "pollutant": pollutant,
                    "horizon_hours": horizon,
                    "category": category,
                    "color": color,
                }
            })
            
    return {
        "type": "FeatureCollection",
        "pollutant": pollutant,
        "horizon_hours": horizon,
        "n_grid_points": len(features),
        "features": features
    }
