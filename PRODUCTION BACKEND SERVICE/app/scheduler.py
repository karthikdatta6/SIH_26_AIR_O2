"""
backend/app/scheduler.py
Background refresh loop — runs in live mode to keep live observations fresh in SQLite store.
"""
import os
import asyncio
import logging
from backend.app.api.deps import get_provider
from backend.app.schemas.station import STATIONS_LOOKUP

logger = logging.getLogger("airo2.scheduler")
REFRESH_MINUTES = int(os.getenv("LIVE_FETCH_CACHE_MINUTES", "15"))


async def run_forever():
    """Background loop refreshing all stations periodically."""
    provider = get_provider()
    while True:
        try:
            for station_id in STATIONS_LOOKUP:
                try:
                    await asyncio.to_thread(provider.get_latest, station_id)
                except Exception as exc:
                    logger.warning(f"[scheduler] refresh failed for {station_id}: {exc}")
            logger.info(f"[scheduler] refreshed {len(STATIONS_LOOKUP)} stations, sleeping {REFRESH_MINUTES}m")
        except Exception as exc:
            logger.exception(f"[scheduler] unexpected loop error: {exc}")
        await asyncio.sleep(REFRESH_MINUTES * 60)
