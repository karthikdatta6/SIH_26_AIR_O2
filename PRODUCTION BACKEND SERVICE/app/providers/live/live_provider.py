"""
backend/app/providers/live/live_provider.py
LiveObservationProvider composing CAMS, Weather, Sentinel, and Manual CPCB sources.
"""
import datetime
from typing import Optional
from backend.app.providers.base import ObservationProvider, Observation
from backend.app.providers.live.store import ObservationStore
from backend.app.providers.live.cams import CAMSClient
from backend.app.providers.live.weather import WeatherClient
from backend.app.providers.live.sentinel import SentinelClient


class LiveObservationProvider(ObservationProvider):
    def __init__(self, station_lookup: dict):
        self._store = ObservationStore()
        self._cams = CAMSClient(self._store)
        self._weather = WeatherClient()
        self._sentinel = SentinelClient()
        self._station_lookup = station_lookup

    def get_latest(self, station_id: str, target_dt: Optional[datetime.datetime] = None) -> Observation:
        target_dt = target_dt or datetime.datetime.now(datetime.timezone.utc)
        station = self._station_lookup.get(station_id, {"latitude": 28.6469, "longitude": 77.3152})

        # Check if a recent manual CPCB entry exists in the store (within the trailing hour)
        recent_manual_rows = [
            o for o in self._store.query_trailing(station_id, target_dt, hours=1)
            if o.source == "CPCB_LIVE_MANUAL"
        ]
        if recent_manual_rows:
            return recent_manual_rows[-1]

        # Otherwise fetch calibrated CAMS live observation
        return self._cams.fetch(
            station_id=station_id,
            latitude=station["latitude"],
            longitude=station["longitude"],
            target_dt=target_dt
        )

    def get_history(self, station_id: str, target_dt: datetime.datetime, hours: int) -> list[Observation]:
        # Real stored history only — never fabricated
        return self._store.query_trailing(station_id, target_dt, hours)

    def get_weather(self, station_id: str) -> dict:
        station = self._station_lookup.get(station_id, {"latitude": 28.6469, "longitude": 77.3152})
        return self._weather.fetch(station["latitude"], station["longitude"])

    def get_satellite(self, station_id: str) -> dict:
        station = self._station_lookup.get(station_id, {"latitude": 28.6469, "longitude": 77.3152})
        return self._sentinel.fetch(station["latitude"], station["longitude"])

    def source_status(self) -> dict:
        return {
            "cams": "configured",
            "weather": "configured",
            "sentinel": "configured",
            "manual_cpcb": "configured",
            "mode": "live"
        }
