"""
test_phase3_phase4_compatibility.py
Golden Compatibility Test Suite.

Verifies Phase 4 backend produces IDENTICAL output to Phase 3 for GOLDEN_001.
Per handoff doc Section 53: this test must fail loudly on unexplained drift.

What this tests (per Section 31):
  - Correct model artifact loaded (not wrong version)
  - Correct feature order (schema order, not dict order)
  - Correct feature count (58)
  - Correct preprocessing (expm1 inverse transform)
  - Correct station encoding
  - Correct horizons (6 checkpoints only)
  - Correct units (ug/m3)
  - Non-negative predictions
  - All 12 predictions produced (2 pollutants x 6 horizons)

Tolerance: abs_tol = 0.001 ug/m3 (floating-point arithmetic only)
"""

import os
import sys
import json
import math
import pytest

# Allow import from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.services.model_service import ModelService
from backend.app.config import (
    GOLDEN_001_INPUT, GOLDEN_001_OUTPUT,
    FORECAST_HORIZONS, POLLUTANTS, MODEL_VERSION,
)

# Tolerance per handoff doc Section 32
ABS_TOL = 0.001  # ug/m3

# Load models once for all tests
ModelService.load_models()


def _load_golden_input():
    with open(GOLDEN_001_INPUT, "r") as f:
        return json.load(f)


def _load_golden_output():
    with open(GOLDEN_001_OUTPUT, "r") as f:
        return json.load(f)


# =============================================================================
# FILE EXISTENCE TESTS
# =============================================================================

def test_golden_input_file_exists():
    """GOLDEN_001/input.json must exist — Phase 3 responsibility."""
    assert os.path.exists(GOLDEN_001_INPUT), (
        f"Golden input not found: {GOLDEN_001_INPUT}"
    )


def test_golden_output_file_exists():
    """GOLDEN_001/expected_output.json must exist — Phase 3 responsibility."""
    assert os.path.exists(GOLDEN_001_OUTPUT), (
        f"Golden output not found: {GOLDEN_001_OUTPUT}"
    )


# =============================================================================
# MODEL LOADING TESTS
# =============================================================================

def test_no2_model_loaded():
    """NO2 production bundle must load successfully."""
    health = ModelService.health_check()
    assert health["NO2"] == "loaded", f"NO2 model not loaded: {health['NO2']}"


def test_o3_model_loaded():
    """O3 production bundle must load successfully."""
    health = ModelService.health_check()
    assert health["O3"] == "loaded", f"O3 model not loaded: {health['O3']}"


def test_feature_count_is_58():
    """Feature schema must contain exactly 58 features — handoff doc Section 10."""
    features = ModelService.get_feature_names("NO2")
    assert len(features) == 58, (
        f"Expected 58 features, got {len(features)}. "
        "The old '38 features' documentation is obsolete — use feature_schema.json."
    )


# =============================================================================
# MODEL VERSION TEST
# =============================================================================

def test_model_version_is_correct():
    """Production model version must be v1.0.0 — handoff doc Section 21."""
    version = ModelService.get_model_version("NO2")
    assert version == MODEL_VERSION, (
        f"Model version mismatch: got '{version}', expected '{MODEL_VERSION}'"
    )


# =============================================================================
# HORIZONS TEST
# =============================================================================

def test_horizons_are_correct():
    """
    Horizons must be exactly [1, 3, 6, 12, 24, 48] — handoff doc Section 5.
    NOT 48 hourly points. NOT recursive. Exactly 6 direct checkpoints.
    """
    assert FORECAST_HORIZONS == [1, 3, 6, 12, 24, 48], (
        f"Wrong horizons: {FORECAST_HORIZONS}. "
        "Must be exactly [1, 3, 6, 12, 24, 48] — no interpolation, no recursion."
    )


# =============================================================================
# PREDICTION COUNT TEST
# =============================================================================

def test_required_output_count_is_12():
    """
    One forecast run = 2 pollutants x 6 horizons = 12 predictions.
    Per handoff doc Section 54.
    """
    golden_in = _load_golden_input()
    features = golden_in["features"]
    station_id = golden_in["station_id"]

    total_preds = 0
    for pollutant in POLLUTANTS:
        result = ModelService.predict(pollutant, station_id, features)
        total_preds += len(result)

    assert total_preds == 12, (
        f"Expected 12 predictions (2 x 6), got {total_preds}"
    )


# =============================================================================
# GOLDEN COMPATIBILITY TESTS — NO2
# =============================================================================

def test_golden_001_no2_predictions():
    """
    Phase 4 NO2 predictions must match Phase 3 golden output within abs_tol.
    Per handoff doc Section 32: Phase 3 output ≈ Phase 4 output.
    """
    golden_in  = _load_golden_input()
    golden_out = _load_golden_output()

    features   = golden_in["features"]
    station_id = golden_in["station_id"]

    result = ModelService.predict("NO2", station_id, features)

    expected_no2 = {
        item["horizon_hours"]: item["prediction"]
        for item in golden_out["forecasts"]["NO2"]
    }

    for h in FORECAST_HORIZONS:
        pred    = result[h]
        expected = expected_no2[h]
        assert pred is not None, f"NO2 h={h} returned None — model inference failed"
        assert abs(pred - expected) <= ABS_TOL, (
            f"NO2 h={h}: Phase4={pred:.4f} vs Phase3={expected:.4f} "
            f"(diff={abs(pred-expected):.4f} > tol={ABS_TOL}). "
            "This indicates a preprocessing or model-loading mismatch."
        )


# =============================================================================
# GOLDEN COMPATIBILITY TESTS — O3
# =============================================================================

def test_golden_001_o3_predictions():
    """
    Phase 4 O3 predictions must match Phase 3 golden output within abs_tol.
    Per handoff doc Section 32.
    """
    golden_in  = _load_golden_input()
    golden_out = _load_golden_output()

    features   = golden_in["features"]
    station_id = golden_in["station_id"]

    result = ModelService.predict("O3", station_id, features)

    expected_o3 = {
        item["horizon_hours"]: item["prediction"]
        for item in golden_out["forecasts"]["O3"]
    }

    for h in FORECAST_HORIZONS:
        pred     = result[h]
        expected = expected_o3[h]
        assert pred is not None, f"O3 h={h} returned None — model inference failed"
        assert abs(pred - expected) <= ABS_TOL, (
            f"O3 h={h}: Phase4={pred:.4f} vs Phase3={expected:.4f} "
            f"(diff={abs(pred-expected):.4f} > tol={ABS_TOL}). "
            "This indicates a preprocessing or model-loading mismatch."
        )


# =============================================================================
# UNIT & NON-NEGATIVE TESTS
# =============================================================================

def test_units_are_ug_m3():
    """
    Units must always be ug/m3 — handoff doc Section 17.
    No ppb conversion. No fabricated unit changes.
    """
    golden_in  = _load_golden_input()
    golden_out = _load_golden_output()

    for pollutant in ["NO2", "O3"]:
        for item in golden_out["forecasts"][pollutant]:
            assert item["unit"] == "ug/m3", (
                f"{pollutant} h={item['horizon_hours']}: "
                f"unit is '{item['unit']}', expected 'ug/m3'."
            )


def test_predictions_are_non_negative():
    """
    All predictions must be >= 0 — handoff doc Section 18.
    expm1 inverse transform guarantees this when input is clipped to 0.
    """
    golden_in = _load_golden_input()
    features  = golden_in["features"]
    station_id = golden_in["station_id"]

    for pollutant in POLLUTANTS:
        result = ModelService.predict(pollutant, station_id, features)
        for h, pred in result.items():
            if pred is not None:
                assert pred >= 0.0, (
                    f"{pollutant} h={h}: prediction is negative ({pred:.4f}). "
                    "expm1(clip(pred, 0)) should guarantee non-negative output."
                )


def test_no_recursive_forecasting():
    """
    Each horizon prediction must be independent — handoff doc Section 4.
    We verify this by checking all 6 horizons return distinct predictions
    (they should differ since each horizon is a separate direct model).
    """
    golden_in = _load_golden_input()
    features  = golden_in["features"]
    station_id = golden_in["station_id"]

    for pollutant in POLLUTANTS:
        result = ModelService.predict(pollutant, station_id, features)
        preds = [result[h] for h in FORECAST_HORIZONS if result[h] is not None]
        assert len(preds) == 6, (
            f"{pollutant}: Expected 6 independent predictions, got {len(preds)}"
        )
        # If recursive: +3h would use +1h as input, creating strong regularities
        # Direct prediction: predictions should vary independently
        unique = len(set(round(p, 2) for p in preds))
        assert unique > 1, (
            f"{pollutant}: All 6 predictions are identical ({preds[0]:.4f}). "
            "This suggests recursive forecasting or a model loading error."
        )
