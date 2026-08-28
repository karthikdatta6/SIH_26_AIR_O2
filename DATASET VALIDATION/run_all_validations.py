"""
run_all_validations.py - Master Dataset Validation Suite Runner.

Executes all core Phase 2 validation checks:
1. Source Stream Validity (CPCB, ERA5, Sentinel-5P, Geospatial)
2. Temporal Leakage & Target Contamination Audit
3. Missingness & Streak Analysis
4. Independent 10-Station Fused Parquet Audit (263,040 rows, 2023-2025)
"""

import os
import sys
import subprocess
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

VALIDATION_STEPS = [
    (
        "01. CPCB Ground Station Data Validator",
        os.path.join(SCRIPT_DIR, "01_SOURCE_STREAM_VALIDATORS", "validate_cpcb.py")
    ),
    (
        "02. ECMWF ERA5 Meteorology Physics Validator",
        os.path.join(SCRIPT_DIR, "01_SOURCE_STREAM_VALIDATORS", "validate_era5.py")
    ),
    (
        "03. Sentinel-5P TROPOMI L2 Spaceborne Validator",
        os.path.join(SCRIPT_DIR, "01_SOURCE_STREAM_VALIDATORS", "validate_sentinel5p.py")
    ),
    (
        "04. OpenStreetMap Geospatial Buffer Validator",
        os.path.join(SCRIPT_DIR, "01_SOURCE_STREAM_VALIDATORS", "validate_geospatial.py")
    ),
    (
        "05. Temporal Leakage & Cross-Contamination Check",
        os.path.join(SCRIPT_DIR, "02_FUSION_INTEGRITY_AND_LEAKAGE", "leakage_check.py")
    ),
    (
        "06. Missingness & Continuous Streak Analysis",
        os.path.join(SCRIPT_DIR, "02_FUSION_INTEGRITY_AND_LEAKAGE", "missingness_analysis.py")
    ),
    (
        "07. Independent 10-Station Row Count Audit",
        os.path.join(SCRIPT_DIR, "02_FUSION_INTEGRITY_AND_LEAKAGE", "independent_audit.py")
    ),
]


def run_suite():
    print("=" * 80, flush=True)
    print("   AIRO2 — DATASET VALIDATION & SCIENTIFIC AUDIT SUITE (SIH 25178)   ", flush=True)
    print("=" * 80, flush=True)
    print(f"Project Root: {PROJECT_ROOT}\n", flush=True)

    results = []
    t_start = time.time()

    for name, script_path in VALIDATION_STEPS:
        if not os.path.exists(script_path):
            print(f"[-] SKIPPED (File not found): {name}", flush=True)
            results.append((name, "SKIPPED", 0.0))
            continue

        print(f"[*] RUNNING: {name} ...", flush=True)
        t0 = time.time()
        try:
            res = subprocess.run(
                [sys.executable, script_path],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=120
            )
            elapsed = time.time() - t0
            status = "PASSED" if res.returncode == 0 else "FAILED"
            results.append((name, status, elapsed))
            
            if status == "PASSED":
                print(f"    [+] {name}: PASSED ({elapsed:.2f}s)", flush=True)
            else:
                print(f"    [!] {name}: FAILED (Exit Code {res.returncode})", flush=True)
                if res.stderr:
                    print(f"        Error output: {res.stderr.strip()[:200]}", flush=True)
        except Exception as exc:
            elapsed = time.time() - t0
            results.append((name, "ERROR", elapsed))
            print(f"    [!] {name}: ERROR ({exc})", flush=True)

    total_time = time.time() - t_start
    print("\n" + "=" * 80, flush=True)
    print("                      DATASET VALIDATION SUMMARY                      ", flush=True)
    print("=" * 80, flush=True)
    print(f"{'Validation Module':<55} {'Status':<12} {'Duration':<10}", flush=True)
    print("-" * 80, flush=True)
    for name, status, dur in results:
        status_str = f"[OK] {status}" if status == "PASSED" else f"[X] {status}"
        print(f"{name:<55} {status_str:<12} {dur:>6.2f}s", flush=True)
    print("-" * 80, flush=True)
    passed_count = sum(1 for _, s, _ in results if s == "PASSED")
    print(f"Total Checks: {len(results)} | Passed: {passed_count} | Total Time: {total_time:.2f}s", flush=True)
    print("=" * 80, flush=True)

    # Save summary CSV to RESULTS folder
    results_dir = os.path.join(SCRIPT_DIR, "RESULTS")
    os.makedirs(results_dir, exist_ok=True)
    summary_csv = os.path.join(results_dir, "master_validation_summary.csv")
    try:
        import csv
        with open(summary_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["module_name", "status", "duration_seconds"])
            for name, status, dur in results:
                writer.writerow([name, status, round(dur, 2)])
        print(f"\n[+] Master validation summary saved to: {summary_csv}", flush=True)
    except Exception as e:
        print(f"[-] Could not save summary CSV: {e}", flush=True)


if __name__ == "__main__":
    run_suite()
