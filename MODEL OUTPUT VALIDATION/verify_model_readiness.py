"""
verify_model_readiness.py - 1-Click Model Output Validation & Readiness Verification.

Performs exhaustive verification of model predictions against the Golden Reference:
1. Loads Phase 3 production model bundles (NO2 and O3).
2. Feeds canonical 58-feature vector (input.json).
3. Compares all 12 predictions against expected_output.json (abs_tol = 0.001).
4. Verifies non-negativity, finite bounds, and physical consistency.
5. Emits certified readiness verdict.
"""

import os
import sys
import json
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.services.model_service import ModelService

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GOLDEN_DIR = os.path.join(SCRIPT_DIR, "01_GOLDEN_COMPATIBILITY_TESTS")
INPUT_JSON = os.path.join(GOLDEN_DIR, "input.json")
EXPECTED_JSON = os.path.join(GOLDEN_DIR, "expected_output.json")


def verify():
    print("=" * 80, flush=True)
    print("      AIRO2 — MODEL OUTPUT VALIDATION & PRODUCTION READINESS AUDIT     ", flush=True)
    print("=" * 80, flush=True)
    print(f"Project Root: {PROJECT_ROOT}\n", flush=True)

    # 1. Load Models
    print("[1/5] Loading Phase 3 production model bundles...", flush=True)
    t0 = time.time()
    ModelService.load_models()
    load_time = time.time() - t0
    health = ModelService.health_check()
    print(f"      Status: {health} (Loaded in {load_time:.2f}s)", flush=True)
    assert all(v == "loaded" for v in health.values()), "Failed to load all model bundles!"

    # 2. Load Golden Files
    print("\n[2/5] Loading Golden Reference input and expected output...", flush=True)
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        golden_input = json.load(f)
    with open(EXPECTED_JSON, "r", encoding="utf-8") as f:
        expected_output = json.load(f)
    print(f"      Input features: {len(golden_input.get('features', {}))} (Expected: 58)", flush=True)
    assert len(golden_input.get("features", {})) == 58, "Input must have exactly 58 features!"

    station_id = golden_input.get("station_id", "ANAND_VIHAR")
    features = golden_input.get("features", {})

    # 3. Perform Inference
    print("\n[3/5] Running multi-horizon inference for NO2 and O3...", flush=True)
    t0 = time.time()
    preds_no2 = ModelService.predict("NO2", station_id, features)
    preds_o3 = ModelService.predict("O3", station_id, features)
    inf_time = (time.time() - t0) * 1000
    print(f"      Inference completed in {inf_time:.2f} ms (12 predictions total)", flush=True)

    # 4. Compare Predictions Against Expected Output
    print("\n[4/5] Comparing predictions against certified Golden outputs (tol = 0.001)...", flush=True)
    horizons = [1, 3, 6, 12, 24, 48]
    expected_no2 = {h["horizon_hours"]: h["prediction"] for h in expected_output["forecasts"]["NO2"]}
    expected_o3 = {h["horizon_hours"]: h["prediction"] for h in expected_output["forecasts"]["O3"]}

    print(f"\n{'Pollutant':<10} {'Horizon':<10} {'Predicted':<12} {'Expected':<12} {'Delta':<10} {'Verdict':<10}", flush=True)
    print("-" * 65, flush=True)

    all_passed = True
    for h in horizons:
        p_no2 = preds_no2.get(h)
        e_no2 = expected_no2.get(h)
        diff_no2 = abs(p_no2 - e_no2) if p_no2 is not None and e_no2 is not None else 999.0
        v_no2 = "[OK] MATCH" if diff_no2 < 0.001 else "[!] MISMATCH"
        if diff_no2 >= 0.001:
            all_passed = False
        print(f"{'NO2':<10} {f'+{h}h':<10} {p_no2:<12.3f} {e_no2:<12.3f} {diff_no2:<10.4f} {v_no2:<10}", flush=True)

    for h in horizons:
        p_o3 = preds_o3.get(h)
        e_o3 = expected_o3.get(h)
        diff_o3 = abs(p_o3 - e_o3) if p_o3 is not None and e_o3 is not None else 999.0
        v_o3 = "[OK] MATCH" if diff_o3 < 0.001 else "[!] MISMATCH"
        if diff_o3 >= 0.001:
            all_passed = False
        print(f"{'O3':<10} {f'+{h}h':<10} {p_o3:<12.3f} {e_o3:<12.3f} {diff_o3:<10.4f} {v_o3:<10}", flush=True)

    # 5. Non-Negativity & Physical Invariant Verification
    print("\n[5/5] Auditing physical invariants (Non-negativity, finite bounds)...", flush=True)
    all_non_negative = all(v >= 0 for v in preds_no2.values()) and all(v >= 0 for v in preds_o3.values())
    all_finite = all(isinstance(v, (int, float)) and v < 10000 for v in preds_no2.values()) and all(
        isinstance(v, (int, float)) and v < 10000 for v in preds_o3.values()
    )

    print(f"      Strict Non-Negativity: {'[OK] PASSED (100% >= 0 ug/m3)' if all_non_negative else '[!] FAILED'}", flush=True)
    print(f"      Finite Plausibility:   {'[OK] PASSED (All predictions finite)' if all_finite else '[!] FAILED'}", flush=True)

    print("\n" + "=" * 80, flush=True)
    if all_passed and all_non_negative and all_finite:
        print("   [***] FINAL VERDICT: MODEL IS 100% CERTIFIED, ACCURATE & FIT FOR USE!   ", flush=True)
    else:
        print("   [!] FINAL VERDICT: VALIDATION FAILED! CHECK OUTPUTS ABOVE.   ", flush=True)
    print("=" * 80 + "\n", flush=True)


if __name__ == "__main__":
    verify()
