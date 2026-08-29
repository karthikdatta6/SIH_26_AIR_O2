"""
model.py - Model metadata and health endpoints.

Endpoints:
  GET /health          - API and model health status
  GET /api/v1/model    - Phase 3 model information (real metadata, not fabricated)

Per handoff doc:
  - Section 22: expose real metadata — never invent it
  - Section 23: preserve the exact reported performance table
  - Section 24: do NOT collapse metrics into a single 'accuracy %'
  - Section 25: do NOT hide accuracy degradation at longer horizons
  - Section 40: health check must verify model loaded state
"""

import logging
from fastapi import APIRouter
from backend.app.services.model_service import ModelService
from backend.app.schemas.forecast import HealthResponse, ModelInfoFull

logger = logging.getLogger(__name__)
router = APIRouter()

# Held-out H2 2025 test performance — reported by Phase 3 evaluation pipeline
# Per handoff doc Section 23: DO NOT recalculate or alter these.
_PERFORMANCE_NO2 = {
    "evaluation_dataset": "Held-out H2 2025 (2025-07-01 to 2025-12-31)",
    "n_test_rows": 44160,
    "note": "R2 is NOT an accuracy percentage. 48h accuracy is lower than 1h accuracy by design.",
    "horizons": [
        {"horizon": "1h",  "R2": 0.9191, "RMSE_ug_m3": 10.64},
        {"horizon": "3h",  "R2": 0.8489, "RMSE_ug_m3": 14.55},
        {"horizon": "6h",  "R2": 0.8058, "RMSE_ug_m3": 16.50},
        {"horizon": "12h", "R2": 0.7908, "RMSE_ug_m3": 17.13},
        {"horizon": "24h", "R2": 0.7662, "RMSE_ug_m3": 18.12},
        {"horizon": "48h", "R2": 0.7155, "RMSE_ug_m3": 20.01},
    ],
}

_PERFORMANCE_O3 = {
    "evaluation_dataset": "Held-out H2 2025 (2025-07-01 to 2025-12-31)",
    "n_test_rows": 44160,
    "note": "R2 is NOT an accuracy percentage. 48h accuracy is lower than 1h accuracy by design.",
    "horizons": [
        {"horizon": "1h",  "R2": 0.8689, "RMSE_ug_m3": 13.01},
        {"horizon": "3h",  "R2": 0.7911, "RMSE_ug_m3": 16.43},
        {"horizon": "6h",  "R2": 0.7609, "RMSE_ug_m3": 17.58},
        {"horizon": "12h", "R2": 0.7600, "RMSE_ug_m3": 17.62},
        {"horizon": "24h", "R2": 0.7559, "RMSE_ug_m3": 17.78},
        {"horizon": "48h", "R2": 0.6975, "RMSE_ug_m3": 19.83},
    ],
}


@router.get("/health", response_model=HealthResponse)
def health_check():
    """
    Check API readiness and model load status.
    Returns degraded state if either model bundle is not loaded.
    Per handoff doc Section 40.
    """
    model_status = ModelService.health_check()
    all_loaded = all(v == "loaded" for v in model_status.values())
    return HealthResponse(
        status="ok" if all_loaded else "degraded",
        database="n/a",
        models=model_status,
    )


@router.get("/api/v1/model", response_model=ModelInfoFull)
def get_model_info():
    """
    Return real Phase 3 model metadata.
    Per handoff doc Section 22 and 55: use actual metadata, never invent it.
    Per handoff doc Section 24: never collapse per-horizon R2 into a single number.
    """
    no2_meta = ModelService.get_metadata("NO2")
    o3_meta  = ModelService.get_metadata("O3")

    return ModelInfoFull(
        model_name="air_quality_forecaster",
        pollutants=["NO2", "O3"],
        horizons_hours=[1, 3, 6, 12, 24, 48],
        feature_count=58,
        native_unit="ug/m3",
        architecture=["LightGBM", "BiLSTM+Attention", "NNLS Simplex Stacking"],
        model_version=no2_meta.get("model_version", ModelService.get_model_version("NO2")),
        training_period=no2_meta.get("training_period", "2023-01-01 to 2024-12-31"),
        validation_period=no2_meta.get("validation_period", "2025-01-01 to 2025-06-30"),
        test_period=no2_meta.get("test_period", "2025-07-01 to 2025-12-31"),
        performance_NO2=_PERFORMANCE_NO2,
        performance_O3=_PERFORMANCE_O3,
    )
