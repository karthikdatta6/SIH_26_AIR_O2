import os, csv

base = r'C:\Users\saisu\OneDrive\Desktop\SIH 2026\PROJECT-AIRO2\data\cpcb'
raw_dir = os.path.join(base, 'raw')

print("=== STRICT README/DOC DELIVERABLES CHECK ===\n")

checks = [
    ('A. raw/ folder exists',            os.path.isdir(raw_dir)),
    ('A. metadata/ folder exists',       os.path.isdir(os.path.join(base, 'metadata'))),
    ('A. processed/ folder exists',      os.path.isdir(os.path.join(base, 'processed'))),
    ('A. documentation/ folder exists',  os.path.isdir(os.path.join(base, 'documentation'))),
    ('B. station_metadata.csv exists',   os.path.isfile(os.path.join(base, 'metadata', 'station_metadata.csv'))),
    ('C. download_log.csv exists',       os.path.isfile(os.path.join(base, 'download_log.csv'))),
    ('D. CPCB_collection_notes.md',      os.path.isfile(os.path.join(base, 'documentation', 'CPCB_collection_notes.md'))),
    ('D. CPCB_quality_report.md',        os.path.isfile(os.path.join(base, 'documentation', 'CPCB_quality_report.md'))),
]

all_pass = True
for label, result in checks:
    status = 'PASS' if result else 'FAIL'
    if not result:
        all_pass = False
    print(f"  [{status}] {label}")

# Count xlsx in raw
xlsx = sorted([f for f in os.listdir(raw_dir) if f.endswith('.xlsx')])
print(f"\n  Raw XLSX count: {len(xlsx)} (expected 30)")

# Check each station x year
STATIONS = [
    'ANAND_VIHAR', 'AYA_NAGAR', 'DHYAN_CHAND_STADIUM', 'DWARKA_SECTOR_8',
    'ITO', 'JAHANGIRPURI', 'MANDIR_MARG', 'OKHLA_PHASE_2', 'PUNJABI_BAGH', 'RK_PURAM'
]
expected = [f"{s}_{y}_DATA.xlsx" for s in STATIONS for y in ['2023', '2024', '2025']]
missing = [f for f in expected if f not in xlsx]
if missing:
    print("  MISSING FILES:")
    for f in missing:
        print("    -", f)
    all_pass = False
else:
    print("  All 30 expected files present: OK")

# Station metadata
with open(os.path.join(base, 'metadata', 'station_metadata.csv')) as f:
    rows = list(csv.DictReader(f))
print(f"\n  Stations in metadata: {len(rows)}")
for r in rows:
    print(f"    {r['station_id']:25s} {r['station_name']:42s} lat={r['latitude']}, lon={r['longitude']}")

# Download log
with open(os.path.join(base, 'download_log.csv')) as f:
    log_rows = list(csv.DictReader(f))
print(f"\n  Download log entries: {len(log_rows)} (expected 30)")
warnings = [r for r in log_rows if r['status'] == 'WARNING']
if warnings:
    print(f"  WARNING entries ({len(warnings)}):")
    for w in warnings:
        print(f"    - {w['file_name']}: {w['notes']}")
else:
    print("  No WARNING entries: OK")

print()
if all_pass and len(xlsx) == 30 and not missing and not warnings:
    print("RESULT: ALL CHECKS PASSED — CPCB Phase 1 is COMPLETE")
else:
    print("RESULT: SOME CHECKS FAILED — see above")
