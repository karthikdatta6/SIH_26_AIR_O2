import re
from pathlib import Path
import glob

doc_dir = Path(r"C:\Users\saisu\OneDrive\Desktop\SIH 2026\data\cpcb\documentation")
out_path = doc_dir / "master_year_from_reports.md"

files = sorted(glob.glob(str(doc_dir / "*_pilot_report.md")))

reports = []
for f in files:
    text = Path(f).read_text(encoding="utf-8")
    rep = {"file": f}
    # Simple regex extractions
    def extract(pattern):
        m = re.search(pattern, text)
        return m.group(1).strip() if m else None

    rep['station'] = extract(r"\| Station \| (.*?) \|")
    rep['rows'] = int(extract(r"\| Rows \| (\d+) \|") or 0)
    rep['start'] = extract(r"\| Start date \| (.*?) \|")
    rep['end'] = extract(r"\| End date \| (.*?) \|")
    rep['freq'] = extract(r"\| Frequency \(inferred\) \| (.*?) \|")
    rep['unparseable'] = int(extract(r"\| Unparseable timestamps \| (\d+) \|") or 0)
    o3det = extract(r"\| O3 column detected \| (.*?) \|")
    rep['o3_col'] = None if o3det and o3det.strip() == 'NOT FOUND' else o3det
    no2det = extract(r"\| NO2 column detected \| (.*?) \|")
    rep['no2_col'] = None if no2det and no2det.strip() == 'NOT FOUND' else no2det
    o3miss = extract(r"\| O3 missing % \| (.*?) \|")
    rep['o3_missing_pct'] = float(o3miss) if o3miss and o3miss != 'N/A' else None
    no2miss = extract(r"\| NO2 missing % \| (.*?) \|")
    rep['no2_missing_pct'] = float(no2miss) if no2miss and no2miss != 'N/A' else None
    gaps = extract(r"\| Number of gaps > .* \| (\d+) \|")
    rep['gaps_count'] = int(gaps) if gaps else 0

    reports.append(rep)

# Aggregate
total_rows = sum(r['rows'] for r in reports)
total_unparseable = sum(r['unparseable'] for r in reports)
global_start = min([r['start'] for r in reports if r['start']], default=None)
global_end = max([r['end'] for r in reports if r['end']], default=None)

params = set()
for r in reports:
    if r['o3_col']:
        params.add(r['o3_col'])
    if r['no2_col']:
        params.add(r['no2_col'])

lines = []
lines.append('# Master Year Report (from per-file pilot reports)')
lines.append('')
lines.append(f'- Files analyzed: {len(reports)}')
lines.append(f'- Total rows (sum of files): {total_rows}')
lines.append(f'- Total unparseable timestamps (sum): {total_unparseable}')
lines.append(f'- Global start: {global_start}')
lines.append(f'- Global end: {global_end}')
lines.append('')
lines.append('## Parameter presence summary')
if params:
    for p in sorted(params):
        lines.append(f'- `{p}` detected in reports')
else:
    lines.append('- No pollutant columns auto-detected across reports')

lines.append('')
lines.append('## Per-file extracted metrics')
for r in reports:
    lines.append(f"### {r.get('station') or Path(r['file']).stem}")
    lines.append(f"- Path: {r['file']}")
    lines.append(f"- Rows: {r['rows']}")
    lines.append(f"- Start / End: {r['start']} — {r['end']}")
    lines.append(f"- Inferred frequency: {r['freq']}")
    lines.append(f"- Unparseable timestamps: {r['unparseable']}")
    lines.append(f"- O3 column: {r['o3_col'] or 'NOT FOUND'}")
    lines.append(f"- NO2 column: {r['no2_col'] or 'NOT FOUND'}")
    lines.append(f"- O3 missing % (approx): {r['o3_missing_pct'] if r['o3_missing_pct'] is not None else 'N/A'}")
    lines.append(f"- NO2 missing % (approx): {r['no2_missing_pct'] if r['no2_missing_pct'] is not None else 'N/A'}")
    lines.append(f"- Gaps reported: {r['gaps_count']}")
    lines.append('')

lines.append('## Aggregated estimates')
est_o3_missing = sum((r['o3_missing_pct'] or 0.0) * r['rows'] / 100.0 for r in reports)
est_no2_missing = sum((r['no2_missing_pct'] or 0.0) * r['rows'] / 100.0 for r in reports)
lines.append(f'- Estimated O3 missing cells (approx): {int(est_o3_missing)}')
lines.append(f'- Estimated NO2 missing cells (approx): {int(est_no2_missing)}')
lines.append('')
lines.append('## Notes and next steps')
lines.append('- These aggregates are computed from the per-file pilot reports (estimates where percentages were used).')
lines.append('- For exact cell-level counts across all columns, I can re-run a read-only aggregation over the raw files and compute precise counts per column (no raw files will be modified).')

out_path.write_text('\n'.join(lines), encoding='utf-8')
print(f'Wrote master report to: {out_path}')
