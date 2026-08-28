import openpyxl
import os
from datetime import datetime

raw_path = r'C:\Users\saisu\OneDrive\Desktop\SIH 2026\PROJECT-AIRO2\data\cpcb\raw'
files = sorted([f for f in os.listdir(raw_path) if f.endswith('.xlsx')])

COLS = ['From Date', 'To Date', 'PM2.5', 'PM10', 'NO', 'NO2', 'NOX', 'NH3', 'SO2', 'CO', 'OZONE']
results = []

for fname in files:
    fpath = os.path.join(raw_path, fname)
    wb = openpyxl.load_workbook(fpath, read_only=True, data_only=True)
    ws = wb.active

    meta = {}
    data_rows = []
    header_found = False

    for i, row in enumerate(ws.iter_rows(values_only=True), start=1):
        rv = list(row)
        if rv[0] == 'State':
            meta['State'] = rv[2]
        if rv[0] == 'City':
            meta['City'] = rv[2]
        if rv[0] == 'Station':
            meta['Station'] = rv[2]
        if rv[0] == 'Parameter':
            meta['Parameter'] = rv[2]
        if rv[0] == 'AvgPeriod':
            meta['AvgPeriod'] = rv[2]
        if rv[0] == 'From' and rv[1] is None:
            meta['DateFrom'] = rv[2]
        if rv[0] == 'To' and rv[1] is None:
            meta['DateTo'] = rv[2]
        if rv[0] == 'From Date':
            header_found = True
            continue
        if header_found:
            data_rows.append(rv)

    total_rows = len(data_rows)

    col_stats = {}
    for ci, col in enumerate(COLS):
        vals = [r[ci] for r in data_rows]
        non_null = sum(1 for v in vals if v is not None)
        null_count = total_rows - non_null
        pct = round(null_count / total_rows * 100, 2) if total_rows else 0
        col_stats[col] = {'non_null': non_null, 'null': null_count, 'pct_missing': pct}

    ts_list = []
    for r in data_rows:
        try:
            if isinstance(r[0], str):
                ts = datetime.strptime(r[0], '%d-%m-%Y %H:%M')
            elif r[0] is not None:
                ts = r[0]
            else:
                ts = None
            ts_list.append(ts)
        except Exception:
            ts_list.append(None)

    valid_ts = [t for t in ts_list if t is not None]

    fsize_kb = round(os.path.getsize(fpath) / 1024, 1)

    print("=" * 60)
    print("FILE   :", fname)
    print("SIZE   :", fsize_kb, "KB")
    print("Station:", meta.get('Station'))
    print("State  :", meta.get('State'), "| City:", meta.get('City'))
    print("Period :", meta.get('AvgPeriod'))
    print("Declared:", meta.get('DateFrom'), "to", meta.get('DateTo'))
    print("Actual :", min(valid_ts) if valid_ts else "N/A", "to", max(valid_ts) if valid_ts else "N/A")
    print("Total data rows :", total_rows)
    print("Valid timestamps:", len(valid_ts))
    print("Parameters in file:", meta.get('Parameter'))
    print()
    print("COLUMN MISSINGNESS:")
    print(f"  {'Column':<12} {'Present':>7} {'Missing':>7} {'% Missing':>10}")
    print("  " + "-"*42)
    for col, s in col_stats.items():
        bar = '#' * int(s['pct_missing'] / 2)
        print(f"  {col:<12} {s['non_null']:>7} {s['null']:>7} {s['pct_missing']:>10.2f}%  {bar}")

    results.append({
        'fname': fname,
        'fsize_kb': fsize_kb,
        'meta': meta,
        'total_rows': total_rows,
        'valid_ts': len(valid_ts),
        'ts_start': min(valid_ts) if valid_ts else None,
        'ts_end': max(valid_ts) if valid_ts else None,
        'col_stats': col_stats
    })

    wb.close()

# Combined summary
print("\n" + "=" * 60)
print("COMBINED SUMMARY ACROSS ALL FILES")
print("=" * 60)
grand_total = sum(r['total_rows'] for r in results)
print(f"Total rows across all files: {grand_total}")
for col in COLS:
    total_present = sum(r['col_stats'][col]['non_null'] for r in results)
    total_missing = sum(r['col_stats'][col]['null'] for r in results)
    pct = round(total_missing / grand_total * 100, 2) if grand_total else 0
    print(f"  {col:<12}: {total_present:>6} present | {total_missing:>6} missing | {pct:.2f}% missing")

print("\nDONE")
