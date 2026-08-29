"""
backend/app/providers/base.py
Common interface both HistoricalObservationProvider (Phase 4) and
LiveObservationProvider (Phase Final) implement. FeatureService only ever
talks to this interface — it is provider-agnostic.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import datetime


@dataclass
class Observation:
    """One normalized ground-chemistry + metadata reading for one station/hour."""
    station_id: str
    source_timestamp: datetime.datetime   # when the reading was actually taken
    retrieved_at: datetime.datetime       # when this backend fetched it
    source: str                           # "CPCB_LIVE_MANUAL" | "OPEN_METEO_CAMS" | "HISTORICAL_FUSED"
    data_mode: str                        # "live" | "historical"

    pm25: Optional[float] = None
    pm10: Optional[float] = None
    no: Optional[float] = None
    no2: Optional[float] = None
    nox: Optional[float] = None
    nh3: Optional[float] = None
    so2: Optional[float] = None
    co: Optional[float] = None
    o3: Optional[float] = None


class ObservationProvider(ABC):
    @abstractmethod
    def get_latest(self, station_id: str, target_dt: Optional[datetime.datetime] = None) -> Observation:
        """Return the best available observation at/near target_dt (default: now, UTC)."""
        raise NotImplementedError

    @abstractmethod
    def get_history(self, station_id: str, target_dt: datetime.datetime, hours: int) -> list[Observation]:
        """
        Return real observations for the `hours` before target_dt, oldest first.
        MUST return [] rather than fabricate data when history isn't available —
        FeatureService turns gaps into NaN, which the model was trained to handle.
        """
        raise NotImplementedError

    @abstractmethod
    def source_status(self) -> dict:
        """{"cams": "configured"|"unavailable", "weather": ..., "sentinel": ..., "manual_cpcb": ...}"""
        raise NotImplementedError
