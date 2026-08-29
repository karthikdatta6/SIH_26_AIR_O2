"""
backend/app/providers/live/store.py
Persists every fetched live observation (CAMS or manual-CPCB) so trailing
lag/rolling-window features can be computed from real history instead of
being fabricated per-request.
"""
import os
import sqlite3
import datetime
import statistics
from dataclasses import asdict
from typing import Optional

from backend.app.providers.base import Observation

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DATA_DIR = os.path.join(_BASE_DIR, "data")
_DB_PATH = os.path.join(_DATA_DIR, "live_observations.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS live_observations (
    station_id       TEXT NOT NULL,
    source_timestamp TEXT NOT NULL,   -- ISO8601 UTC
    retrieved_at     TEXT NOT NULL,
    source           TEXT NOT NULL,
    data_mode        TEXT NOT NULL,
    pm25 REAL, pm10 REAL, no REAL, no2 REAL, nox REAL, nh3 REAL, so2 REAL, co REAL, o3 REAL,
    PRIMARY KEY (station_id, source_timestamp, source)
);
CREATE INDEX IF NOT EXISTS idx_station_time ON live_observations(station_id, source_timestamp);
"""


class ObservationStore:
    def __init__(self, db_path: str = _DB_PATH):
        self._db_path = db_path
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        with self._conn() as conn:
            conn.executescript(_SCHEMA)

    def _conn(self):
        return sqlite3.connect(self._db_path)

    def record(self, obs: Observation) -> None:
        """Upsert one observation."""
        row = asdict(obs)
        with self._conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO live_observations
                   (station_id, source_timestamp, retrieved_at, source, data_mode,
                    pm25, pm10, no, no2, nox, nh3, so2, co, o3)
                   VALUES (:station_id, :source_timestamp, :retrieved_at, :source, :data_mode,
                           :pm25, :pm10, :no, :no2, :nox, :nh3, :so2, :co, :o3)""",
                {
                    **row,
                    "source_timestamp": obs.source_timestamp.isoformat(),
                    "retrieved_at": obs.retrieved_at.isoformat(),
                },
            )

    def query_trailing(self, station_id: str, target_dt: datetime.datetime, hours: int) -> list[Observation]:
        """Fetch observations within the trailing window [target_dt - hours, target_dt]."""
        window_start = (target_dt - datetime.timedelta(hours=hours)).isoformat()
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT * FROM live_observations
                   WHERE station_id = ? AND source_timestamp >= ? AND source_timestamp <= ?
                   ORDER BY source_timestamp ASC""",
                (station_id, window_start, target_dt.isoformat()),
            ).fetchall()
        return [
            Observation(
                station_id=r["station_id"],
                source_timestamp=datetime.datetime.fromisoformat(r["source_timestamp"]),
                retrieved_at=datetime.datetime.fromisoformat(r["retrieved_at"]),
                source=r["source"],
                data_mode=r["data_mode"],
                pm25=r["pm25"],
                pm10=r["pm10"],
                no=r["no"],
                no2=r["no2"],
                nox=r["nox"],
                nh3=r["nh3"],
                so2=r["so2"],
                co=r["co"],
                o3=r["o3"],
            )
            for r in rows
        ]

    def get_at_lag(self, station_id: str, target_dt: datetime.datetime, lag_hours: int, field: str) -> Optional[float]:
        """Nearest real reading to (target_dt - lag_hours), within a 30-min tolerance. None if nothing that close exists."""
        target = target_dt - datetime.timedelta(hours=lag_hours)
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                f"""SELECT {field}, source_timestamp FROM live_observations
                    WHERE station_id = ? AND {field} IS NOT NULL""",
                (station_id,),
            ).fetchall()
        if not rows:
            return None

        # Find closest timestamp
        best_val = None
        min_diff = float("inf")
        for r in rows:
            ts = datetime.datetime.fromisoformat(r["source_timestamp"])
            if ts.tzinfo is None and target.tzinfo is not None:
                ts = ts.replace(tzinfo=datetime.timezone.utc)
            elif ts.tzinfo is not None and target.tzinfo is None:
                target = target.replace(tzinfo=datetime.timezone.utc)
            diff = abs((ts - target).total_seconds())
            if diff < min_diff:
                min_diff = diff
                best_val = r[field]

        if min_diff > 30 * 60:
            return None
        return float(best_val) if best_val is not None else None

    @staticmethod
    def rolling_stats(observations: list[Observation], field: str) -> tuple[Optional[float], Optional[float]]:
        """(mean, stdev) of a real field across the given observations. None if fewer than 2 points."""
        values = [getattr(o, field) for o in observations if getattr(o, field) is not None]
        if not values:
            return None, None
        if len(values) < 2:
            return values[0], 0.0
        return round(float(statistics.fmean(values)), 2), round(float(statistics.stdev(values)), 2)
