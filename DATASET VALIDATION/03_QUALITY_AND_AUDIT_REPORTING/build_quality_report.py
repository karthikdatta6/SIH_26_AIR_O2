import openpyxl
import os
from datetime import datetime

raw = r'C:\Users\saisu\OneDrive\Desktop\SIH 2026\PROJECT-AIRO2\data\cpcb\raw'
COLS = ['From Date', 'To Date', 'PM2.5', 'PM10', 'NO', 'NO2', 'NOX', 'NH3', 'SO2', 'CO', 'OZONE']

station_names = {
    'ANAND_VIHAR':         'Anand Vihar',
    'AYA_NAGAR':           'Aya Nagar',
    'DHYAN_CHAND_STADIUM': 'Major Dhyan Chand National Stadium',
    'DWARKA_SECTOR_8':     'Dwarka-Sector 8',
    'ITO':                 'ITO',
    'JAHANGIRPURI':        'Jahangirpuri',
    'MANDIR_MARG':         'Mandir Marg',
    'OKHLA_PHASE_2':       'Okhla Phase-II',
    'PUNJABI_BAGH':        'Punjabi Bagh',
    'RK_PURAM':            'R.K. Puram',
}

def assess(pct):
    if pct == 0:        return 'COMPLETE'
    elif pct < 5:       return 'EXCELLENT'
    elif pct < 10:      return 'GOOD'
    elif pct < 20:      return 'ACCEPTABLE'
    elif pct < 35:      return 'HIGH'
    else:               return 'VERY HIGH'

def parse_file(fpath):
    wb = openpyxl.load_workbook(fpath, read_only=True, data_only=True)
    ws = wb.active
    meta = {}
    data_rows = []
    header_found = False
    for row in ws.iter_rows(values_only=True):
        rv = list(row)
        if rv[0] == 'State':      meta['State']     = rv[2]
        if rv[0] == 'City':       meta['City']      = rv[2]
        if rv[0] == 'Station':    meta['Station']   = rv[2]
        if rv[0] == 'Parameter':  meta['Parameter'] = rv[2]
        if rv[0] == 'AvgPeriod':  meta['AvgPeriod'] = rv[2]
        if rv[0] == 'From' and rv[1] is None: meta['DateFrom'] = rv[2]
        if rv[0] == 'To'   and rv[1] is None: meta['DateTo']   = rv[2]
        if rv[0] == 'From Date':
            header_found = True
            continue
        if header_found:
            data_rows.append(rv)
    wb.close()

    total = len(data_rows)
    col_stats = {}
    for ci, col in enumerate(COLS):
        vals = [r[ci] for r in data_rows]
        non_null = sum(1 for v in vals if v is not None)
        null_count = total - non_null
        pct = round(null_count / total * 100, 2) if total else 0
        col_stats[col] = {'present': non_null, 'missing': null_count, 'pct': pct}

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
    ts_start = min(valid_ts) if valid_ts else None
    ts_end   = max(valid_ts) if valid_ts else None
    fsize_kb = round(os.path.getsize(fpath) / 1024, 1)

    return {
        'meta': meta,
        'total': total,
        'valid_ts': len(valid_ts),
        'ts_start': ts_start,
        'ts_end': ts_end,
        'fsize_kb': fsize_kb,
        'col_stats': col_stats,
    }

# Group files by station
stations = {}
for fname in sorted(os.listdir(raw)):
    if not fname.endswith('.xlsx'):
        continue
    stem = fname.replace('_DATA.xlsx', '')
    parts = stem.rsplit('_', 1)
    year = parts[-1]
    if not year.isdigit():
        continue
    sid = stem.replace('_' + year, '')
    if sid not in stations:
        stations[sid] = {}
    stations[sid][year] = fname

all_results = {}
print("Parsing all 30 files...")
for sid in sorted(stations.keys()):
    all_results[sid] = {}
    for year in sorted(stations[sid].keys()):
        fname = stations[sid][year]
        fpath = os.path.join(raw, fname)
        print(f"  {fname}")
        all_results[sid][year] = parse_file(fpath)

print("Done parsing. Building report...")

# ─── BUILD MARKDOWN REPORT ───────────────────────────────────────────────────
lines = []
lines.append("# CPCB Ground Stations — Ultra-Detailed Data Quality Report")
lines.append("## 10 Stations × 3 Years (2023–2025) | Anand Vihar Pilot + Full Dataset")
lines.append("")
lines.append("> **Generated:** 2026-08-15  ")
lines.append("> **Team:** Team A — CPCB Ground Stations  ")
lines.append("> **Author:** Sudhith  ")
lines.append("> **Project:** SIH 25178 — Short-Term Forecasting of Ground-Level O₃ and NO₂  ")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## Table of Contents")
lines.append("")
for sid in sorted(all_results.keys()):
    sname = station_names.get(sid, sid)
    anchor = sid.lower().replace('_', '-')
    lines.append(f"- [{sname}](#{anchor})")
lines.append("- [Cross-Station Summary](#cross-station-summary)")
lines.append("- [Critical Flags](#critical-flags)")
lines.append("")
lines.append("---")
lines.append("")

# Per-station sections
all_col_totals = {c: {'present': 0, 'missing': 0} for c in COLS}
grand_total_rows = 0

for sid in sorted(all_results.keys()):
    sname = station_names.get(sid, sid)
    anchor = sid.lower().replace('_', '-')
    lines.append(f"## {sname}")
    lines.append(f"**Station ID:** `{sid}`")
    lines.append("")

    # Station-level 3-year aggregate
    station_total = sum(all_results[sid][y]['total'] for y in all_results[sid])
    grand_total_rows += station_total

    # Per-year detail
    for year in sorted(all_results[sid].keys()):
        r = all_results[sid][year]
        fname = stations[sid][year]
        lines.append(f"### {year} — `{fname}`")
        lines.append("")
        lines.append("| Field | Value |")
        lines.append("|---|---|")
        lines.append(f"| **Station (from file)** | {r['meta'].get('Station', 'N/A')} |")
        lines.append(f"| **File size** | {r['fsize_kb']} KB |")
        lines.append(f"| **Total data rows** | {r['total']:,} |")
        lines.append(f"| **Valid timestamps** | {r['valid_ts']:,} |")
        lines.append(f"| **Actual start** | {r['ts_start']} |")
        lines.append(f"| **Actual end** | {r['ts_end']} |")
        lines.append(f"| **Averaging period** | {r['meta'].get('AvgPeriod', 'N/A')} |")
        lines.append(f"| **Parameters in file** | {r['meta'].get('Parameter', 'N/A')} |")
        lines.append("")

        lines.append("**Column-level missingness:**")
        lines.append("")
        lines.append("| Column | Present | Missing | % Missing | Status |")
        lines.append("|---|---|---|---|---|")
        for col in COLS:
            s = r['col_stats'][col]
            status = assess(s['pct'])
            flag = ''
            if col in ('NO2', 'OZONE'):
                flag = ' ⭐'
            if s['pct'] >= 35:
                flag += ' 🔴'
            elif s['pct'] >= 20:
                flag += ' ⚠️'
            lines.append(f"| `{col}`{flag} | {s['present']:,} | {s['missing']:,} | {s['pct']:.2f}% | {status} |")

            # accumulate totals
            all_col_totals[col]['present'] += s['present']
            all_col_totals[col]['missing'] += s['missing']

        o3_pct  = r['col_stats']['OZONE']['pct']
        no2_pct = r['col_stats']['NO2']['pct']
        lines.append("")
        lines.append(f"> **Primary targets — OZONE: {o3_pct:.2f}% missing | NO2: {no2_pct:.2f}% missing**")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Station 3-year summary table
    lines.append(f"### {sname} — 3-Year Summary")
    lines.append("")
    lines.append("| Column | 2023 Missing% | 2024 Missing% | 2025 Missing% | 3-Year Avg% |")
    lines.append("|---|---|---|---|---|")
    for col in COLS:
        vals = []
        for y in ['2023', '2024', '2025']:
            if y in all_results[sid]:
                vals.append(all_results[sid][y]['col_stats'][col]['pct'])
            else:
                vals.append(None)
        avg = round(sum(v for v in vals if v is not None) / len([v for v in vals if v is not None]), 2)
        row_parts = [f"`{col}`"]
        for v in vals:
            row_parts.append(f"{v:.2f}%" if v is not None else "N/A")
        row_parts.append(f"**{avg:.2f}%**")
        lines.append("| " + " | ".join(row_parts) + " |")
    lines.append("")
    lines.append("---")
    lines.append("")

# ─── CROSS-STATION SUMMARY ────────────────────────────────────────────────────
lines.append("## Cross-Station Summary")
lines.append("")
lines.append(f"**Total rows across all 30 files: {grand_total_rows:,}**")
lines.append("")
lines.append("### OZONE and NO2 Coverage Per Station (All Years)")
lines.append("")
lines.append("| Station | 2023 OZONE% | 2024 OZONE% | 2025 OZONE% | 2023 NO2% | 2024 NO2% | 2025 NO2% |")
lines.append("|---|---|---|---|---|---|---|")
for sid in sorted(all_results.keys()):
    sname = station_names.get(sid, sid)
    row_parts = [sname]
    for col in ['OZONE', 'NO2']:
        for y in ['2023', '2024', '2025']:
            if y in all_results[sid]:
                pct = all_results[sid][y]['col_stats'][col]['pct']
                flag = ' 🔴' if pct >= 35 else (' ⚠️' if pct >= 20 else '')
                row_parts.append(f"{pct:.2f}%{flag}")
            else:
                row_parts.append("N/A")
    lines.append("| " + " | ".join(row_parts) + " |")

lines.append("")
lines.append("### All-Variable Annual Totals (Across All 10 Stations)")
lines.append("")
lines.append("| Column | Total Present | Total Missing | % Missing (all 30 files) |")
lines.append("|---|---|---|---|")
for col in COLS:
    tp = all_col_totals[col]['present']
    tm = all_col_totals[col]['missing']
    total = tp + tm
    pct = round(tm / total * 100, 2) if total else 0
    flag = ' 🔴' if pct >= 35 else (' ⚠️' if pct >= 20 else (' ⭐' if col in ('NO2','OZONE') else ''))
    lines.append(f"| `{col}`{flag} | {tp:,} | {tm:,} | **{pct:.2f}%** |")

lines.append("")
lines.append("---")
lines.append("")

# ─── CRITICAL FLAGS ───────────────────────────────────────────────────────────
lines.append("## Critical Flags")
lines.append("")
lines.append("Files or columns requiring attention before Phase 2:")
lines.append("")

flags = []
for sid in sorted(all_results.keys()):
    sname = station_names.get(sid, sid)
    for year in sorted(all_results[sid].keys()):
        r = all_results[sid][year]
        for col in COLS:
            pct = r['col_stats'][col]['pct']
            if pct >= 35:
                flags.append(f"| 🔴 VERY HIGH | `{stations[sid][year]}` | `{col}` | {pct:.2f}% missing |")
            elif pct >= 20 and col in ('NO2', 'OZONE'):
                flags.append(f"| ⚠️ PRIMARY CONCERN | `{stations[sid][year]}` | `{col}` | {pct:.2f}% missing |")

if flags:
    lines.append("| Severity | File | Column | Missing% |")
    lines.append("|---|---|---|---|")
    for f in flags:
        lines.append(f)
else:
    lines.append("No critical flags — all primary targets (OZONE, NO2) are within acceptable range across all files.")

lines.append("")
lines.append("---")
lines.append("")
lines.append("## Notes for Phase 2")
lines.append("")
lines.append("1. **Column naming:** `OZONE` in raw files = O₃. Do NOT search for `O3`.")
lines.append("2. **Timestamp format:** `DD-MM-YYYY HH:MM` — must be standardised to ISO 8601 in Phase 2.")
lines.append("3. **No meteorological variables** in any CPCB file — source from ERA5.")
lines.append("4. **MANDIR_MARG_2024** was re-downloaded (original was 8.8 KB corrupt file).")
lines.append("5. **Processed folder is empty** — Phase 2 will write cleaned files there.")
lines.append("")
lines.append("---")
lines.append("")
lines.append("*Auto-generated by `scripts/build_quality_report.py` — SIH 25178 Team A (Sudhith)*")
lines.append(f"*Generated: 2026-08-15*")

report_path = r'C:\Users\saisu\OneDrive\Desktop\SIH 2026\PROJECT-AIRO2\data\cpcb\documentation\CPCB_quality_report.md'
with open(report_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print(f"\nReport written: {report_path}")
print(f"Lines: {len(lines)}")
print(f"Grand total rows across all 30 files: {grand_total_rows:,}")
