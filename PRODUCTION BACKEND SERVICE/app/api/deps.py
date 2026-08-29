"""
backend/app/api/deps.py
Dependency injection providers for FastAPI routers.
"""
import os
from functools import lru_cache
from backend.app.providers.base import ObservationProvider
from backend.app.providers.historical import HistoricalObservationProvider
from backend.app.providers.live.live_provider import LiveObservationProvider
from backend.app.schemas.station import STATIONS_LOOKUP


@lru_cache(maxsize=1)
def get_provider() -> ObservationProvider:
    mode = os.getenv("PROVIDER_MODE", "historical").lower().strip()
    if mode == "live":
        return LiveObservationProvider(station_lookup=STATIONS_LOOKUP)
    return HistoricalObservationProvider()


def clear_provider_cache():
    """Helper for testing to reset provider cache."""
    get_provider.cache_clear()
