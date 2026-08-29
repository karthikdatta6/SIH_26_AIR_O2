"""
backend/app/providers/live/cams.py
Wraps the already-calibrated CAMS fetch (real hour-of-day O3 diurnal
transfer, real NO2 mean-bias correction) and persists every fetch
into ObservationStore so trailing lag/roll features are computed from
real accumulated history, not fabricated.
"""
import datetime
from LIVE_DATA.live_weather_service import fetch_live_air_chemistry
from backend.app.providers.base import Observation
from backend.app.providers.live.store import ObservationStore


class CAMSClient:
    def __init__(self, store: ObservationStore):
        self._store = store

    def fetch(
        self,
        station_id: str,
        latitude: float,
        longitude: float,
        target_dt: datetime.datetime
    ) -> Observation:
        chem = fetch_live_air_chemistry(
            latitude=latitude,
            longitude=longitude,
            target_hour_utc=target_dt.hour
        )
        obs = Observation(
            station_id=station_id,
            source_timestamp=target_dt,
            retrieved_at=datetime.datetime.now(datetime.timezone.utc),
            source="OPEN_METEO_CAMS",
            data_mode="live",
            pm25=chem.get("PM2.5_ground"),
            pm10=chem.get("PM10_ground"),
            no=None,   # Genuinely unknown in CAMS live fetch — schema's native_nan handles it
            no2=chem.get("NO2_ground"),
            nox=None,  # Leave None until real NOx sensor exists
            nh3=None,  # Genuinely unknown
            so2=chem.get("SO2_ground"),
            co=chem.get("CO_ground"),
            o3=chem.get("O3_ground"),
        )
        self._store.record(obs)
        return obs
