"""
feature_builder.py
Builds the 58-feature vector in the exact schema order required by the production models.

NOTE: In a real production deployment, CPCB, ERA5, and Sentinel-5P data must be
fetched from live APIs and fused here. For the hackathon demo, this module loads
feature values from the GOLDEN_001 reference or accepts an explicit feature dict.

Per handoff doc:
  - Section 12: validate 58 features before inference
  - Section 13: order must match feature_schema.json exactly
  - Section 15: Phase 4 must NOT reimplement Phase 2 data pipeline
"""

import json
import os
import math
import numpy as np
from datetime import datetime, timezone
from typing import Optional

from backend.app.config import (
    MODEL_NO2_SCHEMA_PATH,
    STATION_ENCODING,
    GOLDEN_001_INPUT,
)

# Station static geospatial features (from Phase 2 OSM/land-use data)
# These are fixed per station and never change — safe to hard-code.
STATION_STATIC = {
    "ANAND_VIHAR": {
        "geo_dist_to_nearest_road_m":    12.0,
        "geo_road_length_1km_buffer_m":  28450.0,
        "geo_road_length_3km_buffer_m":  185300.0,
        "geo_dist_to_nearest_railway_m": 820.0,
        "landuse_commercial":  1.0,
        "landuse_grass":       0.0,
        "landuse_park":        0.0,
        "landuse_residential": 0.0,
    },
    "ITO": {
        "geo_dist_to_nearest_road_m":    8.0,
        "geo_road_length_1km_buffer_m":  31200.0,
        "geo_road_length_3km_buffer_m":  198000.0,
        "geo_dist_to_nearest_railway_m": 1200.0,
        "landuse_commercial":  1.0,
        "landuse_grass":       0.0,
        "landuse_park":        0.0,
        "landuse_residential": 0.0,
    },
    "OKHLA_PHASE_2": {
        "geo_dist_to_nearest_road_m":    20.0,
        "geo_road_length_1km_buffer_m":  22100.0,
        "geo_road_length_3km_buffer_m":  162000.0,
        "geo_dist_to_nearest_railway_m": 1500.0,
        "landuse_commercial":  0.0,
        "landuse_grass":       0.0,
        "landuse_park":        0.0,
        "landuse_residential": 1.0,
    },
    "AYA_NAGAR": {
        "geo_dist_to_nearest_road_m":    45.0,
        "geo_road_length_1km_buffer_m":  12500.0,
        "geo_road_length_3km_buffer_m":  98000.0,
        "geo_dist_to_nearest_railway_m": 4200.0,
        "landuse_commercial":  0.0,
        "landuse_grass":       1.0,
        "landuse_park":        0.0,
        "landuse_residential": 0.0,
    },
    "RK_PURAM": {
        "geo_dist_to_nearest_road_m":    30.0,
        "geo_road_length_1km_buffer_m":  18000.0,
        "geo_road_length_3km_buffer_m":  130000.0,
        "geo_dist_to_nearest_railway_m": 3000.0,
        "landuse_commercial":  0.0,
        "landuse_grass":       0.0,
        "landuse_park":        0.0,
        "landuse_residential": 1.0,
    },
    "DHYAN_CHAND_STADIUM": {
        "geo_dist_to_nearest_road_m":    60.0,
        "geo_road_length_1km_buffer_m":  20000.0,
        "geo_road_length_3km_buffer_m":  145000.0,
        "geo_dist_to_nearest_railway_m": 600.0,
        "landuse_commercial":  0.0,
        "landuse_grass":       0.0,
        "landuse_park":        1.0,
        "landuse_residential": 0.0,
    },
    "MANDIR_MARG": {
        "geo_dist_to_nearest_road_m":    15.0,
        "geo_road_length_1km_buffer_m":  25000.0,
        "geo_road_length_3km_buffer_m":  170000.0,
        "geo_dist_to_nearest_railway_m": 2100.0,
        "landuse_commercial":  1.0,
        "landuse_grass":       0.0,
        "landuse_park":        0.0,
        "landuse_residential": 0.0,
    },
    "PUNJABI_BAGH": {
        "geo_dist_to_nearest_road_m":    18.0,
        "geo_road_length_1km_buffer_m":  27000.0,
        "geo_road_length_3km_buffer_m":  180000.0,
        "geo_dist_to_nearest_railway_m": 2500.0,
        "landuse_commercial":  0.0,
        "landuse_grass":       0.0,
        "landuse_park":        0.0,
        "landuse_residential": 1.0,
    },
    "JAHANGIRPURI": {
        "geo_dist_to_nearest_road_m":    22.0,
        "geo_road_length_1km_buffer_m":  24000.0,
        "geo_road_length_3km_buffer_m":  165000.0,
        "geo_dist_to_nearest_railway_m": 900.0,
        "landuse_commercial":  0.0,
        "landuse_grass":       0.0,
        "landuse_park":        0.0,
        "landuse_residential": 1.0,
    },
    "DWARKA_SECTOR_8": {
        "geo_dist_to_nearest_road_m":    35.0,
        "geo_road_length_1km_buffer_m":  16000.0,
        "geo_road_length_3km_buffer_m":  115000.0,
        "geo_dist_to_nearest_railway_m": 700.0,
        "landuse_commercial":  0.0,
        "landuse_grass":       0.0,
        "landuse_park":        0.0,
        "landuse_residential": 1.0,
    },
}


def _cyclical(value: float, period: float) -> tuple:
    """Return (sin, cos) cyclical encoding for a time value."""
    angle = 2 * math.pi * value / period
    return math.sin(angle), math.cos(angle)


def build_feature_vector_from_dict(
    station_id: str,
    raw_features: dict,
    feature_names: list,
) -> dict:
    """
    Given a raw feature dict (from live data or golden reference), build the
    58-feature dict in the exact order specified by feature_names.

    This ensures feature_schema.json order is always used, never dict insertion order.

    Args:
        station_id:    Canonical station ID
        raw_features:  Dict of available feature values
        feature_names: Ordered list from feature_schema.json (58 names)

    Returns:
        Ordered dict with exactly 58 entries in schema order.
    """
    # Start with static station features
    static = STATION_STATIC.get(station_id, {})

    # Merge: schema order wins, fill from raw_features and static
    result = {}
    for name in feature_names:
        if name == "station_enc":
            result[name] = float(STATION_ENCODING.get(station_id, 0))
        elif name in static:
            result[name] = static[name]
        elif name in raw_features:
            val = raw_features[name]
            result[name] = float(val) if val is not None else float("nan")
        else:
            result[name] = float("nan")

    return result


def build_demo_feature_vector(
    station_id: str,
    feature_names: list,
) -> dict:
    """
    Build a demo feature vector using values from the GOLDEN_001 reference input.
    Used for the ?use_demo=true endpoint mode during hackathon demo.

    Returns:
        Feature dict in schema order for the given station (remapped from ANAND_VIHAR golden if needed).
    """
    try:
        with open(GOLDEN_001_INPUT, "r") as f:
            golden = json.load(f)

        base_features = golden.get("features", {})

        # Override station-specific static features for the requested station
        static = STATION_STATIC.get(station_id, {})
        result = {}
        for name in feature_names:
            if name == "station_enc":
                result[name] = float(STATION_ENCODING.get(station_id, 0))
            elif name in static:
                result[name] = static[name]
            elif name in base_features:
                val = base_features[name]
                result[name] = float(val) if val is not None else float("nan")
            else:
                result[name] = float("nan")

        return result

    except Exception as e:
        # If golden reference not found, return a zero vector (clearly invalid — for testing only)
        return {name: float("nan") for name in feature_names}


def get_ordered_feature_names() -> list:
    """Load the authoritative 58-feature name list from models/NO2/feature_schema.json."""
    with open(MODEL_NO2_SCHEMA_PATH, "r") as f:
        schema = json.load(f)
    raw = schema.get("features", [])
    if raw and isinstance(raw[0], dict):
        return [feat["name"] for feat in raw]
    return list(raw)
