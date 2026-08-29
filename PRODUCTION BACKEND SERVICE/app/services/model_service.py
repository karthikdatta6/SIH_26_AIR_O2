"""
model_service.py
Loads the frozen Phase 3 production model bundles (NO2, O3) once at startup.
Performs 58-feature validation, direct multi-horizon inference, and expm1 inverse transform.

Per handoff document (PHASE_3_TO_PHASE_4_MODEL_HANDOFF_REQUIREMENTS_UPDATED.md):
  - Section 7:  canonical model path is models/NO2/ and models/O3/
  - Section 8:  backend treats bundles as production inference objects only
  - Section 10: feature count is 58 (authoritative from feature_schema.json)
  - Section 13: feature order MUST match schema exactly
  - Section 16: preprocessing — expm1(clip(pred, 0, None)) inverse transform
  - Section 17: units are always ug/m3 — no conversions
  - Section 18: validate every prediction for finite, non-negative value
  - Section 39: load models once at startup, keep in memory
"""

import os
import json
import pickle
import logging
import numpy as np
from dataclasses import dataclass, field
from typing import Optional

from backend.app.config import (
    MODEL_NO2_PATH, MODEL_O3_PATH,
    MODEL_NO2_SCHEMA_PATH, MODEL_O3_SCHEMA_PATH,
    MODEL_NO2_METADATA_PATH, MODEL_O3_METADATA_PATH,
    FORECAST_HORIZONS, STATION_ENCODING,
)

logger = logging.getLogger(__name__)


@dataclass
class ModelBundle:
    """Wraps a loaded Phase 3 production bundle for a single pollutant."""
    bundle: dict
    feature_names: list       # Ordered list of 58 feature names from schema
    metadata: dict
    horizons: list = field(default_factory=lambda: [1, 3, 6, 12, 24, 48])
    model_version: str = "1.0.0"
    loaded: bool = False
    error: Optional[str] = None


class ModelService:
    """
    Singleton service that loads and serves both production model bundles.
    Load once via load_models() at application startup.
    """

    _no2_bundle: Optional[ModelBundle] = None
    _o3_bundle:  Optional[ModelBundle] = None

    @classmethod
    def load_models(cls) -> None:
        """
        Load both production bundles from the canonical models/ path.
        Called once during FastAPI startup event.
        """
        for pollutant, pkl_path, schema_path, meta_path in [
            ("NO2", MODEL_NO2_PATH, MODEL_NO2_SCHEMA_PATH, MODEL_NO2_METADATA_PATH),
            ("O3",  MODEL_O3_PATH,  MODEL_O3_SCHEMA_PATH,  MODEL_O3_METADATA_PATH),
        ]:
            try:
                logger.info(f"[ModelService] Loading {pollutant} bundle from {pkl_path}")
                with open(pkl_path, "rb") as f:
                    bundle = pickle.load(f)

                with open(schema_path, "r") as f:
                    schema = json.load(f)

                with open(meta_path, "r") as f:
                    metadata = json.load(f)

                # Extract ordered feature names from schema
                raw_features = schema.get("features", [])
                if raw_features and isinstance(raw_features[0], dict):
                    feature_names = [feat["name"] for feat in raw_features]
                else:
                    feature_names = list(raw_features)

                mb = ModelBundle(
                    bundle=bundle,
                    feature_names=feature_names,
                    metadata=metadata,
                    horizons=metadata.get("forecast_horizons_hours", FORECAST_HORIZONS),
                    model_version=schema.get("model_version", "1.0.0"),
                    loaded=True,
                )
                logger.info(
                    f"[ModelService] {pollutant} loaded. "
                    f"Features={len(feature_names)}, Horizons={mb.horizons}"
                )

                if pollutant == "NO2":
                    cls._no2_bundle = mb
                else:
                    cls._o3_bundle = mb

            except Exception as exc:
                logger.error(f"[ModelService] Failed to load {pollutant}: {exc}")
                err_bundle = ModelBundle(
                    bundle={}, feature_names=[], metadata={},
                    loaded=False, error=str(exc)
                )
                if pollutant == "NO2":
                    cls._no2_bundle = err_bundle
                else:
                    cls._o3_bundle = err_bundle

    @classmethod
    def _get_bundle(cls, pollutant: str) -> ModelBundle:
        if pollutant == "NO2":
            return cls._no2_bundle
        elif pollutant == "O3":
            return cls._o3_bundle
        else:
            raise ValueError(f"Unknown pollutant: {pollutant}. Must be 'NO2' or 'O3'.")

    @classmethod
    def predict(
        cls,
        pollutant: str,
        station_id: str,
        features: dict,
    ) -> dict:
        """
        Run direct multi-horizon inference for one pollutant at one station.

        Args:
            pollutant:  'NO2' or 'O3'
            station_id: Canonical station ID string (e.g. 'ANAND_VIHAR')
            features:   Dict of {feature_name: value} for all 58 features

        Returns:
            Dict of {horizon_hours: prediction_ug_m3 or None}
            None means inference failed for that horizon — never silently zero.

        Constraints (from handoff doc):
          - Section 4:  NO recursive forecasting
          - Section 13: Feature order from schema, never from dict key order
          - Section 16: expm1(clip(pred, 0, None)) inverse transform
          - Section 18: validate finite and non-negative
        """
        bundle = cls._get_bundle(pollutant)
        if bundle is None or not bundle.loaded:
            cls.load_models()
            bundle = cls._get_bundle(pollutant)

        if bundle is None or not bundle.loaded:
            logger.error(f"[ModelService] {pollutant} bundle not loaded: {bundle.error if bundle else 'Uninitialized'}")
            return {h: None for h in FORECAST_HORIZONS}

        # --- Feature validation (handoff doc Section 12) ---
        if len(features) != len(bundle.feature_names):
            raise ValueError(
                f"Feature count mismatch: got {len(features)}, "
                f"expected {len(bundle.feature_names)}"
            )

        missing = [f for f in bundle.feature_names if f not in features]
        if missing:
            raise ValueError(f"Missing features: {missing[:5]}...")

        # --- Build numpy array in EXACT schema order (handoff doc Section 13) ---
        X = np.array(
            [features.get(fname, np.nan) for fname in bundle.feature_names],
            dtype=np.float64
        ).reshape(1, -1)

        # --- Direct multi-step inference (handoff doc Section 4) ---
        results = {}
        horizon_models = bundle.bundle.get("horizon_models", {})

        for h in FORECAST_HORIZONS:
            try:
                hm = horizon_models.get(h)
                if hm is None:
                    logger.warning(f"[ModelService] No model for {pollutant} h={h}")
                    results[h] = None
                    continue

                lgb_model = hm["model"]
                pred_log = float(lgb_model.predict(X)[0])

                # Inverse transform: expm1(clip(pred, 0, None))
                pred_physical = float(np.expm1(np.clip(pred_log, 0.0, None)))

                # Validate output (handoff doc Section 18)
                if not np.isfinite(pred_physical):
                    logger.error(f"[ModelService] {pollutant} h={h} non-finite prediction")
                    results[h] = None
                    continue
                if pred_physical < 0:
                    logger.error(f"[ModelService] {pollutant} h={h} negative prediction {pred_physical}")
                    results[h] = None
                    continue

                results[h] = round(pred_physical, 4)

            except Exception as exc:
                logger.error(f"[ModelService] Inference error {pollutant} h={h}: {exc}")
                results[h] = None

        return results

    @classmethod
    def get_metadata(cls, pollutant: str) -> dict:
        """Return real Phase 3 metadata from the loaded bundle."""
        bundle = cls._get_bundle(pollutant)
        if not bundle.loaded:
            return {"error": bundle.error}
        return bundle.metadata

    @classmethod
    def get_feature_names(cls, pollutant: str = "NO2") -> list:
        """Return the 58 ordered feature names from the production schema."""
        bundle = cls._get_bundle(pollutant)
        return bundle.feature_names

    @classmethod
    def get_model_version(cls, pollutant: str = "NO2") -> str:
        bundle = cls._get_bundle(pollutant)
        return bundle.model_version

    @classmethod
    def health_check(cls) -> dict:
        """Return model load status for the /health endpoint."""
        def _status(bundle: Optional[ModelBundle]) -> str:
            if bundle is None:
                return "not_loaded"
            return "loaded" if bundle.loaded else f"error: {bundle.error}"

        return {
            "NO2": _status(cls._no2_bundle),
            "O3":  _status(cls._o3_bundle),
        }
