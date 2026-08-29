"""
explain.py - Model explainability endpoint.

Endpoint:
  GET /api/v1/stations/{station_id}/forecast/explanation

Per handoff doc Section 26:
  - Use terminology 'Model Drivers' or 'Features Contributing to Prediction'
  - DO NOT use 'Cause', 'Root Cause', or 'Pollution Cause'
  - SHAP importance is not causal proof

Per handoff doc Section 27:
  - DO NOT invent uncertainty / confidence intervals
"""

import os
import logging
from fastapi import APIRouter, HTTPException

from backend.app.config import SHAP_NO2_CSV, SHAP_O3_CSV
from backend.app.schemas.station import STATIONS_LOOKUP

logger = logging.getLogger(__name__)
router = APIRouter()


def _load_shap_csv(csv_path: str) -> list:
    """Parse a SHAP top-10 CSV file if it exists."""
    if not os.path.exists(csv_path):
        return []
    try:
        drivers = []
        with open(csv_path, "r") as f:
            lines = f.readlines()
        header = [h.strip().lower() for h in lines[0].split(",")]
        for line in lines[1:]:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 2:
                continue
            row = dict(zip(header, parts))
            importance = float(row.get("mean_shap", row.get("importance", 0.0)))
            drivers.append({
                "feature":    row.get("feature", "unknown"),
                "importance": round(abs(importance), 6),
                "direction":  "positive" if importance >= 0 else "negative",
            })
        return drivers[:10]
    except Exception as exc:
        logger.warning(f"Failed to parse SHAP CSV {csv_path}: {exc}")
        return []


@router.get("/api/v1/stations/{station_id}/forecast/explanation")
def get_forecast_explanation(station_id: str):
    """
    Return Phase 3 SHAP top-10 'Model Drivers' for NO2 and O3.

    IMPORTANT: These are model driver importances — NOT causal explanations.
    Per handoff doc Section 26: SHAP importance is not causal proof.

    If SHAP CSVs are not found, returns placeholder indicating data unavailable.
    """
    if station_id not in STATIONS_LOOKUP:
        raise HTTPException(status_code=404, detail=f"Station '{station_id}' not found.")

    no2_drivers = _load_shap_csv(SHAP_NO2_CSV)
    o3_drivers  = _load_shap_csv(SHAP_O3_CSV)

    return {
        "station_id":      station_id,
        "note": (
            "These are Model Drivers from SHAP analysis — "
            "they indicate which features the model weighted most heavily. "
            "SHAP importance is NOT a causal explanation of pollution."
        ),
        "drivers_NO2": no2_drivers if no2_drivers else [
            {"feature": "SHAP data not yet available", "importance": None, "direction": None}
        ],
        "drivers_O3": o3_drivers if o3_drivers else [
            {"feature": "SHAP data not yet available", "importance": None, "direction": None}
        ],
    }
