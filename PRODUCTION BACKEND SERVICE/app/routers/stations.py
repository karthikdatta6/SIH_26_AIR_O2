"""
stations.py - Station API endpoints.

Endpoints:
  GET /api/v1/stations                          - All 10 canonical stations
  GET /api/v1/stations/current                  - All stations with latest reading (stub)
  GET /api/v1/stations/{station_id}             - Single station metadata
  GET /api/v1/stations/{station_id}/current     - Latest observation (stub)
  GET /api/v1/stations/{station_id}/forecast    - Phase 3 model forecasts (12 predictions)

Per handoff doc:
  - Section 5:  6 horizons only: 1h, 3h, 6h, 12h, 24h, 48h
  - Section 6:  never generate intermediate hourly points
  - Section 17: always ug/m3, no unit conversion
  - Section 34: recommended endpoint structure
  - Section 35: strict observed vs predicted distinction
  - Section 36: forecast_generated_at + target_timestamp on every prediction
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from backend.app.config import (
    FORECAST_HORIZONS, POLLUTANTS, MODEL_VERSION, STATION_ENCODING
)
from backend.app.services.model_service import ModelService
from backend.app.schemas.station import (
    StationResponse, STATIONS_DATA, STATIONS_LOOKUP
)
from backend.app.schemas.forecast import (
    ForecastResponse, HorizonPrediction, ModelInfo
)
from backend.app.utils.aqi import calculate_aqi
from backend.app.utils.feature_builder import (
    build_demo_feature_vector, get_ordered_feature_names
)

from backend.app.api.deps import get_provider
from backend.app.services.feature_service import FeatureService
from backend.app.providers.live.live_provider import LiveObservationProvider

logger = logging.getLogger(__name__)
router = APIRouter()


def _make_forecast_response(
    station_id: str,
    feature_dict: dict,
    generated_at: datetime,
    data_mode: str = "historical",
    is_live: bool = False,
    ground_chem_source: str = "HISTORICAL_FUSED",
) -> ForecastResponse:
    """Core inference logic shared by forecast endpoints."""

    forecasts: dict[str, list[HorizonPrediction]] = {}

    for pollutant in POLLUTANTS:
        horizon_preds = ModelService.predict(
            pollutant=pollutant,
            station_id=station_id,
            features=feature_dict,
        )

        horizon_list = []
        for h in FORECAST_HORIZONS:
            target_ts = generated_at + timedelta(hours=h)
            pred_val = horizon_preds.get(h)

            # AQI derived from model prediction (deterministic — not ML)
            aqi_info = calculate_aqi(pollutant, pred_val) if pred_val is not None else None

            horizon_list.append(HorizonPrediction(
                horizon_hours=h,
                target_timestamp=target_ts.isoformat(),
                prediction=pred_val,
                unit="ug/m3",
                aqi=aqi_info["aqi"] if aqi_info else None,
                aqi_category=aqi_info["category"] if aqi_info else None,
                aqi_color=aqi_info["color"] if aqi_info else None,
            ))

        forecasts[pollutant] = horizon_list

    model_info = ModelInfo(
        name="air_quality_forecaster",
        version=ModelService.get_model_version("NO2"),
        feature_schema_version=MODEL_VERSION,
        feature_count=58,
        native_unit="ug/m3",
        architecture=["LightGBM", "BiLSTM+Attention", "NNLS"],
    )

    return ForecastResponse(
        station_id=station_id,
        generated_at=generated_at.isoformat(),
        model=model_info,
        forecasts=forecasts,
        data_mode=data_mode,
        is_live=is_live,
        ground_chem_source=ground_chem_source,
    )


@router.get("/api/v1/stations", response_model=list[StationResponse])
def list_stations():
    """
    Return all 10 canonical CPCB monitoring stations.
    """
    return [StationResponse(**s) for s in STATIONS_DATA]


@router.get("/api/v1/stations/current", response_model=list[StationResponse])
def list_stations_current():
    """
    All stations with their latest observed readings from active provider.
    """
    provider = get_provider()
    results = []
    for s in STATIONS_DATA:
        st_id = s["station_id"]
        try:
            obs = provider.get_latest(st_id)
            curr_aqi_no2 = calculate_aqi("NO2", obs.no2)["aqi"] if obs.no2 is not None else None
            curr_aqi_o3 = calculate_aqi("O3", obs.o3)["aqi"] if obs.o3 is not None else None
            aqi_val = max(curr_aqi_no2 or 0, curr_aqi_o3 or 0) or None
            aqi_cat = calculate_aqi("NO2", obs.no2)["category"] if curr_aqi_no2 else None
            aqi_col = calculate_aqi("NO2", obs.no2)["color"] if curr_aqi_no2 else None
            results.append(StationResponse(
                **s,
                current_aqi=aqi_val,
                current_category=aqi_cat,
                color=aqi_col
            ))
        except Exception:
            results.append(StationResponse(**s))
    return results


@router.get("/api/v1/stations/{station_id}", response_model=StationResponse)
def get_station(station_id: str):
    """Single station metadata. Returns 404 for unknown station IDs."""
    if station_id not in STATIONS_LOOKUP:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Station '{station_id}' not found. "
                f"Valid IDs: {list(STATIONS_LOOKUP.keys())}"
            )
        )
    return StationResponse(**STATIONS_LOOKUP[station_id])


@router.get("/api/v1/stations/{station_id}/current", response_model=StationResponse)
def get_station_current(station_id: str):
    """
    Latest observed values for one station.
    """
    if station_id not in STATIONS_LOOKUP:
        raise HTTPException(status_code=404, detail=f"Station '{station_id}' not found.")
    
    st = STATIONS_LOOKUP[station_id]
    provider = get_provider()
    try:
        obs = provider.get_latest(station_id)
        aqi_info = calculate_aqi("NO2", obs.no2) if obs.no2 is not None else None
        return StationResponse(
            **st,
            current_aqi=aqi_info["aqi"] if aqi_info else None,
            current_category=aqi_info["category"] if aqi_info else None,
            color=aqi_info["color"] if aqi_info else None,
        )
    except Exception:
        return StationResponse(**st)


@router.get("/api/v1/stations/{station_id}/forecast", response_model=ForecastResponse)
def get_station_forecast(
    station_id: str,
    use_demo: bool = Query(
        default=False,
        description=(
            "Set to true to force demo feature vector from GOLDEN_001 reference. "
            "Defaults to false to use active provider (live/historical)."
        )
    ),
):
    """
    Generate Phase 3 model forecasts for one station.
    Returns 12 predictions: 6 horizons (1h, 3h, 6h, 12h, 24h, 48h) x 2 pollutants (NO2, O3).
    """
    if station_id not in STATIONS_LOOKUP:
        raise HTTPException(
            status_code=404,
            detail=f"Station '{station_id}' not found. Valid IDs: {list(STATIONS_LOOKUP.keys())}"
        )

    if station_id not in STATION_ENCODING:
        raise HTTPException(status_code=400, detail=f"Station '{station_id}' has no model encoding.")

    generated_at = datetime.now(timezone.utc)
    provider = get_provider()

    if use_demo:
        feature_names = get_ordered_feature_names()
        feature_dict = build_demo_feature_vector(station_id, feature_names)
        data_mode = "historical"
        is_live = False
        ground_chem_source = "HISTORICAL_FUSED"
        logger.info(f"[forecast] Demo mode for {station_id} — using GOLDEN_001 feature reference")
    else:
        feature_service = FeatureService(provider)
        feature_dict, latest_obs = feature_service.build(station_id, generated_at)
        data_mode = latest_obs.data_mode
        is_live = isinstance(provider, LiveObservationProvider)
        ground_chem_source = latest_obs.source
        logger.info(
            f"[forecast] Provider mode '{data_mode}' for {station_id} (source={ground_chem_source})"
        )

    try:
        response = _make_forecast_response(
            station_id=station_id,
            feature_dict=feature_dict,
            generated_at=generated_at,
            data_mode=data_mode,
            is_live=is_live,
            ground_chem_source=ground_chem_source,
        )
    except ValueError as exc:
        logger.error(f"[forecast] Feature validation error: {exc}")
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.error(f"[forecast] Inference error for {station_id}: {exc}")
        raise HTTPException(status_code=500, detail="Model inference failed. Check server logs.")

    return response
