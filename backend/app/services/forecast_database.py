"""
backend/app/services/forecast_database.py
Persistent SQLite storage layer for AIRO2 Multi-Horizon Predictions and Weather Diagnostics.

Guarantees:
- 100% deterministic reproducibility across queries.
- Thread-safe WAL (Write-Ahead Logging) high-concurrency mode.
- Non-blocking fail-safes: inference never crashes even if disk writes are momentarily constrained.
"""

import os
import json
import sqlite3
import datetime
import logging
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger("airo2.database")

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "forecast_store.db")


def _get_connection() -> sqlite3.Connection:
    """Returns a SQLite connection configured with WAL mode and high busy-timeout."""
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA temp_store=MEMORY;")
    return conn


def init_database() -> None:
    """Initializes the SQLite database and creates the prediction store tables."""
    try:
        os.makedirs(DB_DIR, exist_ok=True)
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS forecast_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    station_id TEXT NOT NULL,
                    observation_date TEXT NOT NULL,
                    observation_hour INTEGER NOT NULL,
                    generated_at TEXT NOT NULL,
                    forecast_json TEXT NOT NULL,
                    weather_json TEXT NOT NULL,
                    features_json TEXT,
                    UNIQUE(station_id, observation_date, observation_hour)
                );
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_station_date_hour 
                ON forecast_records(station_id, observation_date, observation_hour);
            """)
            conn.commit()
            logger.info(f"[ForecastDB] SQLite database initialized in WAL mode at {DB_PATH}")
    except Exception as e:
        logger.error(f"[ForecastDB] Warning: SQLite database initialization failed: {e}", exc_info=True)


def get_cached_forecast(
    station_id: str,
    observation_date: str,
    observation_hour: int
) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """
    Retrieves stored forecast and weather record from SQLite DB.
    
    Returns:
        (forecast_dict, weather_dict) if found, else None
    """
    if not os.path.exists(DB_PATH):
        return None
        
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT forecast_json, weather_json 
                FROM forecast_records 
                WHERE station_id = ? AND observation_date = ? AND observation_hour = ?
                LIMIT 1;
            """, (station_id, observation_date, observation_hour))
            row = cursor.fetchone()
            if row and row[0] and row[1]:
                forecast_data = json.loads(row[0])
                weather_data = json.loads(row[1])
                logger.info(f"[ForecastDB] CACHE HIT for ({station_id}, {observation_date}, hour={observation_hour:02d}:00)")
                return forecast_data, weather_data
    except Exception as e:
        logger.warning(f"[ForecastDB] Read bypass on error for {station_id}: {e}")
    
    return None


def store_forecast(
    station_id: str,
    observation_date: str,
    observation_hour: int,
    forecast_data: Dict[str, Any],
    weather_data: Dict[str, Any],
    features_data: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Persists computed forecast and weather data to SQLite DB.
    Uses INSERT OR REPLACE to guarantee atomic updates.
    """
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
            cursor.execute("""
                INSERT OR REPLACE INTO forecast_records 
                (station_id, observation_date, observation_hour, generated_at, forecast_json, weather_json, features_json)
                VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (
                station_id,
                observation_date,
                observation_hour,
                now_iso,
                json.dumps(forecast_data),
                json.dumps(weather_data),
                json.dumps(features_data) if features_data else None
            ))
            conn.commit()
            logger.info(f"[ForecastDB] STORED new prediction for ({station_id}, {observation_date}, hour={observation_hour:02d}:00)")
            return True
    except Exception as e:
        logger.warning(f"[ForecastDB] Write bypass on error for {station_id}: {e}")
        return False
