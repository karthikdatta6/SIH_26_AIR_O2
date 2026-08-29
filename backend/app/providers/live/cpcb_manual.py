"""
backend/app/providers/live/cpcb_manual.py
Manual CPCB CCR CSV ingestion client.
"""
import csv
import datetime
from typing import Optional
from backend.app.providers.base import Observation
from backend.app.providers.live.store import ObservationStore

_COLUMN_MAP = {
    "station_id": "station_id",
    "timestamp": "From Date",
    "pm25": "PM2.5",
    "pm10": "PM10",
    "no": "NO",
    "no2": "NO2",
    "nox": "NOx",
    "nh3": "NH3",
    "so2": "SO2",
    "co": "CO",
    "o3": "Ozone",
}


class ManualCPCBClient:
    def __init__(self, store: ObservationStore):
        self._store = store

    def ingest_csv(self, csv_path: str, station_id_lookup: dict[str, str]) -> int:
        count = 0
        with open(csv_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                raw_station = row.get(_COLUMN_MAP["station_id"], "").strip()
                station_id = station_id_lookup.get(raw_station)
                if station_id is None:
                    continue
                ts = self._parse_timestamp(row.get(_COLUMN_MAP["timestamp"]))
                if ts is None:
                    continue
                obs = Observation(
                    station_id=station_id,
                    source_timestamp=ts,
                    retrieved_at=datetime.datetime.now(datetime.timezone.utc),
                    source="CPCB_LIVE_MANUAL",
                    data_mode="live",
                    pm25=self._num(row, "pm25"),
                    pm10=self._num(row, "pm10"),
                    no=self._num(row, "no"),
                    no2=self._num(row, "no2"),
                    nox=self._num(row, "nox"),
                    nh3=self._num(row, "nh3"),
                    so2=self._num(row, "so2"),
                    co=self._num(row, "co"),
                    o3=self._num(row, "o3"),
                )
                self._store.record(obs)
                count += 1
        return count

    def _num(self, row: dict, key: str) -> Optional[float]:
        raw = row.get(_COLUMN_MAP.get(key, key))
        if raw in (None, "", "NA", "None", "null"):
            return None
        try:
            return float(raw)
        except ValueError:
            return None

    def _parse_timestamp(self, raw: Optional[str]) -> Optional[datetime.datetime]:
        if not raw:
            return None
        for fmt in ("%d-%m-%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M"):
            try:
                naive = datetime.datetime.strptime(raw, fmt)
                return naive.replace(
                    tzinfo=datetime.timezone(datetime.timedelta(hours=5, minutes=30))
                ).astimezone(datetime.timezone.utc)
            except ValueError:
                continue
        return None
