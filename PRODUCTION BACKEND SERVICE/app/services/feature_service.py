"""
backend/app/services/feature_service.py
Assembles the strict 58-feature vector for ModelService inference.
Provider-agnostic: works seamlessly with both LiveObservationProvider and HistoricalObservationProvider.
"""
import math
import datetime
from typing import Tuple

from backend.app.providers.base import ObservationProvider, Observation
from backend.app.utils.feature_builder import STATION_STATIC, get_ordered_feature_names
from backend.app.config import STATION_ENCODING
from backend.app.schemas.station import STATIONS_LOOKUP


def _cyclical(value: float, period: float) -> tuple:
    angle = 2.0 * math.pi * value / period
    return math.sin(angle), math.cos(angle)


class FeatureService:
    def __init__(self, provider: ObservationProvider):
        self._provider = provider

    def build(self, station_id: str, target_dt: datetime.datetime) -> Tuple[dict, Observation]:
        feature_names = get_ordered_feature_names()
        static = STATION_STATIC.get(station_id, {})
        station = STATIONS_LOOKUP.get(station_id, {"latitude": 28.6469, "longitude": 77.3152})

        latest = self._provider.get_latest(station_id, target_dt)
        weather = self._provider.get_weather(station_id) if hasattr(self._provider, "get_weather") else {}
        satellite = self._provider.get_satellite(station_id) if hasattr(self._provider, "get_satellite") else {}
        history_24h = self._provider.get_history(station_id, target_dt, hours=24)
        history_6h = [
            o for o in history_24h
            if abs((target_dt - o.source_timestamp).total_seconds()) <= 6 * 3600
        ]

        hour = target_dt.hour + target_dt.minute / 60.0
        doy = target_dt.timetuple().tm_yday
        hour_sin, hour_cos = _cyclical(hour, 24.0)
        doy_sin, doy_cos = _cyclical(doy, 365.25)

        u10 = weather.get("wind_u10") or 0.0
        v10 = weather.get("wind_v10") or 0.0
        wind_dir_rad = math.atan2(v10, u10)
        wind_sin, wind_cos = math.sin(wind_dir_rad), math.cos(wind_dir_rad)

        blh = weather.get("blh_m") or 300.0
        wind_spd = weather.get("wind_speed_ms") or 2.5
        solar = weather.get("solar_radiation_wm2") or 0.0

        raw = {
            "PM2.5_ground": latest.pm25,
            "PM10_ground": latest.pm10,
            "NO_ground": latest.no,
            "NOx_ground": latest.nox,
            "NH3_ground": latest.nh3,
            "SO2_ground": latest.so2,
            "CO_ground": latest.co,
            "era5_temperature_c": weather.get("temperature_c", 28.0),
            "era5_dewpoint_c": weather.get("dewpoint_c", 18.0),
            "era5_u10": u10,
            "era5_v10": v10,
            "era5_wind_speed": wind_spd,
            "era5_relative_humidity": weather.get("relative_humidity_pct", 55.0),
            "era5_surface_pressure_hpa": weather.get("surface_pressure_hpa", 985.0),
            "era5_boundary_layer_height": blh,
            "era5_solar_radiation_w_m2": solar,
            "era5_total_precipitation_mm": weather.get("precipitation_mm", 0.0),
            "sat_NO2": satellite.get("sat_NO2"),
            "sat_CO": satellite.get("sat_CO"),
            "sat_HCHO": satellite.get("sat_HCHO"),
            "satellite_age_hours": satellite.get("satellite_age_hours"),
            "sat_NO2_available": satellite.get("sat_NO2_available", 0.0),
            "sat_CO_available": satellite.get("sat_CO_available", 0.0),
            "hour_sin": hour_sin,
            "hour_cos": hour_cos,
            "doy_sin": doy_sin,
            "doy_cos": doy_cos,
            "wind_sin": wind_sin,
            "wind_cos": wind_cos,
            "ventilation_coeff": blh * wind_spd,
            "photo_index": solar / 1024.0,
            "station_enc": float(STATION_ENCODING.get(station_id, 0)),
        }

        # Compute lag and rolling features from ObservationStore
        store = getattr(self._provider, "_store", None)
        for pollutant, field in [("NO2", "no2"), ("OZONE", "o3")]:
            for lag_h in (1, 3, 6, 12, 24):
                raw[f"{pollutant}_ground_lag_{lag_h}h"] = (
                    store.get_at_lag(station_id, target_dt, lag_h, field)
                    if store else None
                )
            mean_6h, std_6h = store.rolling_stats(history_6h, field) if store else (None, None)
            mean_24h, std_24h = store.rolling_stats(history_24h, field) if store else (None, None)
            raw[f"{pollutant}_ground_roll_mean_6h"] = mean_6h
            raw[f"{pollutant}_ground_roll_std_6h"] = std_6h
            raw[f"{pollutant}_ground_roll_mean_24h"] = mean_24h
            raw[f"{pollutant}_ground_roll_std_24h"] = std_24h

        # Final 58-feature ordering and missingness compliance
        result = {}
        for name in feature_names:
            if name in static:
                result[name] = float(static[name])
            elif name in raw and raw[name] is not None:
                result[name] = float(raw[name])
            else:
                result[name] = float("nan")

        return result, latest
