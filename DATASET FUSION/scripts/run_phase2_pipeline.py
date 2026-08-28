"""
SIH 25178 - Phase 2 Master Pipeline Orchestrator
Executes all Phase 2 processing, fusion, validation, and zero-leakage auditing.

Steps:
1. validate_inputs.py       -> Inventory & Station Coverage Check
2. validate_cpcb.py         -> CPCB Quality Control & 1-Hour Aggregation (WMO >= 75%)
3. validate_sentinel5p.py   -> Sentinel-5P Daily Quality Control & Extraction (QA >= 75 / 50)
4. validate_era5.py         -> ERA5 Meteorology Loading & Station Haversine Extraction
5. validate_geospatial.py   -> OpenStreetMap Roads, Railways & Landuse Metric Extraction
6. missingness_analysis.py  -> Comprehensive 140-Variable Missingness & Gap Audit
7. build_fused_dataset.py   -> Spatiotemporal Master Fusion & Pilot Dataset Generation
8. leakage_check.py         -> Zero-Leakage & Data Integrity Automated Audit
9. independent_audit.py     -> Comprehensive Statistical & Physical Sanity Verification
"""

import sys
import os
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts", "phase2"))

import validate_inputs
import validate_cpcb
import validate_sentinel5p
import validate_era5
import validate_geospatial
import missingness_analysis
import build_fused_dataset
import leakage_check
import independent_audit

def run_pipeline():
    start_total = time.time()
    print("=" * 70)
    print(" SIH 25178: PHASE 2 SPATIOTEMPORAL DATA FUSION & VALIDATION PIPELINE ")
    print("=" * 70)
    
    # Step 1: Inputs
    t0 = time.time()
    validate_inputs.run_all_input_validation()
    print(f"-> Step 1 Completed in {time.time() - t0:.1f}s\n")
    
    # Step 2: CPCB
    t0 = time.time()
    validate_cpcb.process_all_cpcb()
    print(f"-> Step 2 Completed in {time.time() - t0:.1f}s\n")
    
    # Step 3: Sentinel-5P
    t0 = time.time()
    validate_sentinel5p.process_all_sentinel5p()
    print(f"-> Step 3 Completed in {time.time() - t0:.1f}s\n")
    
    # Step 4: ERA5
    t0 = time.time()
    validate_era5.process_all_era5()
    print(f"-> Step 4 Completed in {time.time() - t0:.1f}s\n")
    
    # Step 5: Geospatial
    t0 = time.time()
    validate_geospatial.process_all_geospatial()
    print(f"-> Step 5 Completed in {time.time() - t0:.1f}s\n")
    
    # Step 6: Missingness Analysis
    t0 = time.time()
    missingness_analysis.run_missingness_audit()
    print(f"-> Step 6 Completed in {time.time() - t0:.1f}s\n")
    
    # Step 7: Master Spatiotemporal Fusion
    t0 = time.time()
    build_fused_dataset.build_master_fused_dataset()
    print(f"-> Step 7 Completed in {time.time() - t0:.1f}s\n")
    
    # Step 8: Zero-Leakage Audit
    t0 = time.time()
    leakage_check.run_leakage_audit()
    print(f"-> Step 8 Completed in {time.time() - t0:.1f}s\n")
    
    # Step 9: Independent Dataset Audit
    t0 = time.time()
    independent_audit.run_independent_audit()
    print(f"-> Step 9 Completed in {time.time() - t0:.1f}s\n")
    
    elapsed = time.time() - start_total
    print("=" * 70)
    print(f" [SUCCESS] Phase 2 Pipeline Finished Completely in {elapsed:.1f}s ")
    print(f" Master dataset ready at: data/fused/station_hourly_fused.parquet")
    print(f" Quality reports ready at: data/quality_reports/")
    print("=" * 70)

if __name__ == "__main__":
    run_pipeline()
