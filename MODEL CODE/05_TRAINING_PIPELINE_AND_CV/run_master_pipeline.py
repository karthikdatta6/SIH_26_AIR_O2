"""
scripts/phase3/run_phase3_pipeline.py
SIH 25178 — Phase 3 Master Orchestrator
Runs all 8 steps in order with error handling.
Usage:
  python scripts/phase3/run_phase3_pipeline.py                  # Run all steps
  python scripts/phase3/run_phase3_pipeline.py --start-from 3   # Resume from step 3
  python scripts/phase3/run_phase3_pipeline.py --only 1         # Run only step 1
"""

import os
import sys
import time
import argparse
import subprocess
from datetime import datetime

# ─── PATHS ────────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

STEPS = [
    (0, "00_eda_analysis.py",           "EDA Analysis & Reports"),
    (1, "01_feature_engineering.py",    "Feature Engineering (38 features)"),
    (2, "02_cross_validation.py",       "CV Setup & Leakage Audit"),
    (3, "03_train_lightgbm.py",         "LightGBM Training (all horizons)"),
    (4, "04_train_deep_learning.py",    "BiLSTM+Attention Training"),
    (5, "05_ensemble_stacking.py",      "NNLS Simplex Stacking"),
    (6, "06_evaluate_and_benchmark.py", "Evaluation & Persistence Benchmark"),
    (7, "07_shap_and_visualizations.py","SHAP + Visualizations + Phase 4 Export"),
]

SCRIPT_DIR = os.path.join(ROOT, "scripts", "phase3")


def run_step(step_num: int, script: str, description: str) -> bool:
    """Run a pipeline step and return True on success, False on failure."""
    script_path = os.path.join(SCRIPT_DIR, script)
    print()
    print("=" * 70)
    print(f"  STEP {step_num}: {description}")
    print(f"  Script: {script_path}")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    if not os.path.exists(script_path):
        print(f"  [ERROR] Script not found: {script_path}")
        return False

    t0 = time.time()
    result = subprocess.run(
        [sys.executable, script_path],
        cwd=ROOT,
        text=True,
    )
    elapsed = time.time() - t0

    if result.returncode == 0:
        print(f"\n  ✅ STEP {step_num} COMPLETE — {elapsed:.1f}s")
        return True
    else:
        print(f"\n  ❌ STEP {step_num} FAILED (exit code {result.returncode})")
        print(f"  See error output above.")
        return False


def main():
    parser = argparse.ArgumentParser(description="Phase 3 Pipeline Orchestrator")
    parser.add_argument("--start-from", type=int, default=0,
                        help="Start from this step number (0–7)")
    parser.add_argument("--only", type=int, default=None,
                        help="Run only this specific step number")
    parser.add_argument("--stop-on-error", action="store_true", default=True,
                        help="Stop pipeline if any step fails (default: True)")
    args = parser.parse_args()

    print()
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║          SIH 25178 — AIRO2 PHASE 3 ML PIPELINE ORCHESTRATOR         ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Working directory: {ROOT}")

    to_run = STEPS if args.only is None else [(s, n, d) for s, n, d in STEPS if s == args.only]
    if args.only is None:
        to_run = [(s, n, d) for s, n, d in STEPS if s >= args.start_from]

    failed_steps = []
    t_start = time.time()

    for step_num, script, description in to_run:
        success = run_step(step_num, script, description)
        if not success:
            failed_steps.append(step_num)
            if args.stop_on_error:
                print(f"\n  Pipeline stopped at step {step_num}.")
                print("  Fix the error above and rerun with:")
                print(f"  python scripts/phase3/run_phase3_pipeline.py --start-from {step_num}")
                break

    total_elapsed = time.time() - t_start
    print()
    print("═" * 70)
    print(f"  PIPELINE SUMMARY — Total time: {total_elapsed/60:.1f} minutes")
    if failed_steps:
        print(f"  ❌ FAILED STEPS: {failed_steps}")
    else:
        print("  ✅ ALL STEPS COMPLETED SUCCESSFULLY")
    print("═" * 70)


if __name__ == "__main__":
    main()
