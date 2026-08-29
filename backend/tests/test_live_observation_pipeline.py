"""
backend/tests/test_live_observation_pipeline.py
Unit and integration tests for the live observation pipeline, ObservationStore,
FeatureService, and provider mode switching.
"""
import os
import sys
import uuid
import datetime
import pytest

# Allow import from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.providers.base import Observation
from backend.app.providers.historical import HistoricalObservationProvider
from backend.app.providers.live.store import ObservationStore
from backend.app.providers.live.live_provider import LiveObservationProvider
from backend.app.services.feature_service import FeatureService
from backend.app.api.deps import get_provider, clear_provider_cache
from backend.app.schemas.station import STATIONS_LOOKUP


@pytest.fixture
def temp_store():
    db_name = f"test_{uuid.uuid4().hex}.db"
    db_path = os.path.join(os.path.dirname(__file__), db_name)
    store = ObservationStore(db_path=db_path)
    yield store
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except OSError:
            pass


def test_observation_store_roundtrip(temp_store):
    now = datetime.datetime.now(datetime.timezone.utc)
    obs = Observation(
        station_id="ANAND_VIHAR",
        source_timestamp=now,
        retrieved_at=now,
        source="OPEN_METEO_CAMS",
        data_mode="live",
        pm25=55.0,
        pm10=110.0,
        no2=42.0,
        o3=28.0,
    )
    temp_store.record(obs)

    trailing = temp_store.query_trailing("ANAND_VIHAR", now, hours=1)
    assert len(trailing) == 1
    assert trailing[0].no2 == 42.0
    assert trailing[0].source == "OPEN_METEO_CAMS"

    lag_val = temp_store.get_at_lag("ANAND_VIHAR", now, lag_hours=0, field="no2")
    assert lag_val == 42.0


def test_feature_service_nan_when_no_history(temp_store):
    now = datetime.datetime.now(datetime.timezone.utc)
    provider = LiveObservationProvider(station_lookup=STATIONS_LOOKUP)
    provider._store = temp_store

    service = FeatureService(provider)
    features, latest = service.build("ANAND_VIHAR", now)

    assert len(features) == 58
    # All lag fields must be NaN (not fabricated multipliers) when no history exists
    assert str(features["NO2_ground_lag_1h"]) == "nan"
    assert str(features["NO2_ground_lag_6h"]) == "nan"
    assert str(features["OZONE_ground_lag_1h"]) == "nan"
    assert latest.source in ["OPEN_METEO_CAMS", "CPCB_LIVE_MANUAL"]


def test_feature_service_real_lag_when_history_exists(temp_store):
    now = datetime.datetime.now(datetime.timezone.utc)
    one_h_ago = now - datetime.timedelta(hours=1)

    obs_past = Observation(
        station_id="ITO",
        source_timestamp=one_h_ago,
        retrieved_at=now,
        source="OPEN_METEO_CAMS",
        data_mode="live",
        no2=58.5,
        o3=34.2,
    )
    temp_store.record(obs_past)

    provider = LiveObservationProvider(station_lookup=STATIONS_LOOKUP)
    provider._store = temp_store

    service = FeatureService(provider)
    features, latest = service.build("ITO", now)

    # 1h lag should precisely equal 58.5
    assert features["NO2_ground_lag_1h"] == 58.5
    assert features["OZONE_ground_lag_1h"] == 34.2


def test_manual_cpcb_preferred_over_cams(temp_store):
    now = datetime.datetime.now(datetime.timezone.utc)
    obs_cams = Observation(
        station_id="ANAND_VIHAR",
        source_timestamp=now,
        retrieved_at=now,
        source="OPEN_METEO_CAMS",
        data_mode="live",
        no2=45.0,
    )
    obs_manual = Observation(
        station_id="ANAND_VIHAR",
        source_timestamp=now,
        retrieved_at=now,
        source="CPCB_LIVE_MANUAL",
        data_mode="live",
        no2=62.0,
    )
    temp_store.record(obs_cams)
    temp_store.record(obs_manual)

    provider = LiveObservationProvider(station_lookup=STATIONS_LOOKUP)
    provider._store = temp_store

    latest = provider.get_latest("ANAND_VIHAR", now)
    assert latest.source == "CPCB_LIVE_MANUAL"
    assert latest.no2 == 62.0


def test_provider_mode_switch():
    clear_provider_cache()
    os.environ["PROVIDER_MODE"] = "historical"
    p_hist = get_provider()
    assert isinstance(p_hist, HistoricalObservationProvider)

    clear_provider_cache()
    os.environ["PROVIDER_MODE"] = "live"
    p_live = get_provider()
    assert isinstance(p_live, LiveObservationProvider)

    clear_provider_cache()
    os.environ["PROVIDER_MODE"] = "historical"
