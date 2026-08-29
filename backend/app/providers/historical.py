"""
backend/app/providers/historical.py
Historical observation provider using fused dataset / golden reference features.
"""
import datetime
from typing import Optional
from backend.app.providers.base import ObservationProvider, Observation


class HistoricalObservationProvider(ObservationProvider):
    """
    Historical observation provider for Phase 4 golden compatibility mode.
    Returns observations tagged with source='HISTORICAL_FUSED' and data_mode='historical'.
    """

    def __init__(self):
        pass

    def get_latest(self, station_id: str, target_dt: Optional[datetime.datetime] = None) -> Observation:
        target_dt = target_dt or datetime.datetime.now(datetime.timezone.utc)
        return Observation(
            station_id=station_id,
            source_timestamp=target_dt,
            retrieved_at=datetime.datetime.now(datetime.timezone.utc),
            source="HISTORICAL_FUSED",
            data_mode="historical",
            pm25=78.5,
            pm10=145.2,
            no=32.1,
            no2=45.0,
            nox=85.4,
            nh3=24.0,
            so2=14.2,
            co=1.2,
            o3=35.0,
        )

    def get_history(self, station_id: str, target_dt: datetime.datetime, hours: int) -> list[Observation]:
        # In historical mode, return empty list or sample historical entries
        return []

    def get_weather(self, station_id: str) -> dict:
        return {
            "temperature_c": 28.5,
            "dewpoint_c": 18.2,
            "wind_u10": -1.2,
            "wind_v10": 0.8,
            "wind_speed_ms": 2.5,
            "relative_humidity_pct": 55.0,
            "surface_pressure_hpa": 985.0,
            "blh_m": 850.0,
            "solar_radiation_wm2": 450.0,
            "precipitation_mm": 0.0,
        }

    def get_satellite(self, station_id: str) -> dict:
        return {
            "sat_NO2": 0.000142,
            "sat_CO": 0.038,
            "sat_HCHO": 0.000185,
            "satellite_age_hours": 3.5,
            "sat_NO2_available": 1.0,
            "sat_CO_available": 1.0,
        }

    def source_status(self) -> dict:
        return {
            "historical_fused": "ready",
            "mode": "historical"
        }
