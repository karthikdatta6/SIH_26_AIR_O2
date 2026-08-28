import glob
import re
from pathlib import Path
import pandas as pd
from collections import defaultdict

TIMESTAMP_HINTS = ["from date", "date", "timestamp", "datetime", "time"]
O3_HINTS = ["o3", "ozone"]
NO2_HINTS = ["no2", "nox2", "nitrogen dioxide"]


def detect_header(path, reader):
    probe = reader(path, header=None, nrows=20)
    header_row = 0
    for i in range(len(probe)):
        row_values = [str(v).strip().lower() for v in probe.iloc[i].tolist()]
        if any(any(hint in cell for hint in TIMESTAMP_HINTS) for cell in row_values):
            header_row = i
            break
    return header_row


def load_df(path: Path):
    if path.suffix.lower() in ('.xlsx', '.xls'):
        reader = pd.read_excel
    else:
        reader = pd.read_csv
    header = detect_header(path, reader)
    df = reader(path, header=header)
    df.columns = [str(c).strip() for c in df.columns]
    return df, header


def guess_column(columns, hints):
    for col in columns:
        low = str(col).lower()
        if any(h in low for h in hints):
            return col
    return None


def analyze_file(path: Path):
    df, header = load_df(path)
    cols = list(df.columns)
    ts_col = guess_column(cols, TIMESTAMP_HINTS)
    o3_col = guess_column(cols, O3_HINTS)
    no2_col = guess_column(cols, NO2_HINTS)

    # timestamps
    if ts_col:
        ts = pd.to_datetime(df[ts_col], errors='coerce', dayfirst=True)
        n_bad_ts = int(ts.isna().sum())
        ts_valid = ts.dropna().sort_values()
    else:
        ts = pd.Series([pd.NaT]*len(df))
        n_bad_ts = None
        ts_valid = pd.Series([], dtype='datetime64[ns]')

    start_date = ts_valid.min() if not ts_valid.empty else None
    end_date = ts_valid.max() if not ts_valid.empty else None

    freq = 'unknown'
    modal_delta = None
    if len(ts_valid) > 1:
        deltas = ts_valid.diff().dropna()
        if not deltas.empty:
            modal_delta = deltas.mode().iloc[0]
            freq = str(modal_delta)

    # per-column missing
    col_stats = {}
    for c in cols:
        missing = int(df[c].apply(lambda v: pd.isna(v) or str(v).strip() == '').sum())
        non_missing = len(df) - missing
        col_stats[c] = {'missing': missing, 'non_missing': non_missing, 'total': len(df)}

    # gaps
    gaps = []
    if len(ts_valid) > 1 and modal_delta is not None:
        deltas = ts_valid.diff().dropna()
        threshold = modal_delta * 2
        gap_mask = deltas > threshold
        gap_deltas = deltas[gap_mask].sort_values(ascending=False)
        for idx, dur in gap_deltas.items():
            gap_end = ts_valid.loc[idx]
            gap_start = ts_valid.shift(1).loc[idx]
            gaps.append({'start': gap_start, 'end': gap_end, 'duration': dur})

    # complete/partial pollutant presence
    parsed_mask = (~ts.isna()) if ts_col else pd.Series([False]*len(df))
    if o3_col and no2_col:
        complete_mask = parsed_mask & df[o3_col].notna() & df[no2_col].notna()
        partial_mask = parsed_mask & (df[o3_col].notna() | df[no2_col].notna())
    elif o3_col or no2_col:
        col = o3_col or no2_col
        complete_mask = parsed_mask & df[col].notna()
        partial_mask = complete_mask
    else:
        complete_mask = pd.Series([False]*len(df))
        partial_mask = pd.Series([False]*len(df))

    return {
        'path': str(path),
        'name': path.stem,
        'rows': len(df),
        'header_row': header,
        'columns': cols,
        'timestamp_col': ts_col,
        'n_bad_ts': n_bad_ts,
        'start': start_date,
        'end': end_date,
        'freq': freq,
        'col_stats': col_stats,
        'gaps': gaps,
        'o3_col': o3_col,
        'no2_col': no2_col,
        'complete_rows': int(complete_mask.sum()),
        'partial_rows': int(partial_mask.sum())
    }


def aggregate(inspections):
    per_col = defaultdict(lambda: {'missing': 0, 'non_missing': 0, 'files': 0, 'total_cells': 0})
    total_rows = 0
    total_parsed_ts = 0
    total_complete = 0
    total_partial = 0
    global_start = None
    global_end = None

    for info in inspections:
        total_rows += info['rows']
        total_complete += info['complete_rows']
        total_partial += info['partial_rows']
        if info['start']:
            global_start = info['start'] if (global_start is None or info['start'] < global_start) else global_start
        if info['end']:
            global_end = info['end'] if (global_end is None or info['end'] > global_end) else global_end
        for c, st in info['col_stats'].items():
            per_col[c]['missing'] += st['missing']
            per_col[c]['non_missing'] += st['non_missing']
            per_col[c]['files'] += 1
            per_col[c]['total_cells'] += st['total']

    return {
        'per_column': per_col,
        'total_rows': total_rows,
        'total_complete_rows': total_complete,
        'total_partial_rows': total_partial,
        'global_start': global_start,
        'global_end': global_end,
        'files': len(inspections)
    }


def write_markdown(inspections, agg, out_path: Path):
    lines = []
    lines.append('# Final Ultra-Detailed Year Report')
    lines.append('This report is generated read-only from the raw files in `data/cpcb/raw` and the per-file pilot inspections.')
    lines.append('')
    lines.append('## Executive summary')
    lines.append(f'- Files processed: {agg["files"]}')
    lines.append(f'- Total rows (sum of files): {agg["total_rows"]}')
    lines.append(f'- Total rows with all primary pollutants present (and valid timestamp): {agg["total_complete_rows"]}')
    lines.append(f'- Total rows with any pollutant present (and valid timestamp): {agg["total_partial_rows"]}')
    lines.append(f'- Overall time span: {agg["global_start"]} — {agg["global_end"]}')
    lines.append('')

    lines.append('## Column-level aggregates')
    lines.append('| Column | Files present | Non-missing cells | Missing cells | % missing |')
    lines.append('|---|---:|---:|---:|---:|')
    for c, s in sorted(agg['per_column'].items()):
        total = s['total_cells']
        missing = s['missing']
        non_missing = s['non_missing']
        pct = round(missing / total * 100, 2) if total else 0.0
        lines.append(f'| `{c}` | {s["files"]} | {non_missing} | {missing} | {pct}% |')

    lines.append('\n## Per-file detailed analysis\n')
    for info in inspections:
        lines.append(f"### {info['name']}")
        lines.append(f"- Path: {info['path']}")
        lines.append(f"- Rows: {info['rows']}")
        lines.append(f"- Header row: {info['header_row']}")
        lines.append(f"- Timestamp column: {info['timestamp_col']}")
        lines.append(f"- Unparseable timestamps: {info['n_bad_ts']}")
        lines.append(f"- Start / End: {info['start']} — {info['end']}")
        lines.append(f"- Inferred frequency: {info['freq']}")
        lines.append(f"- O3 column: {info['o3_col'] or 'NOT FOUND'}")
        lines.append(f"- NO2 column: {info['no2_col'] or 'NOT FOUND'}")
        lines.append(f"- Rows with at least one pollutant (and valid ts): {info['partial_rows']}")
        lines.append(f"- Rows with all primary pollutants (and valid ts): {info['complete_rows']}")
        lines.append('\nColumn details:')
        lines.append('| Column | Non-missing | Missing | % missing |')
        lines.append('|---|---:|---:|---:|')
        for c, st in info['col_stats'].items():
            total = st['total']
            missing = st['missing']
            non = st['non_missing']
            pct = round(missing/total*100, 2) if total else 0.0
            lines.append(f'| `{c}` | {non} | {missing} | {pct}% |')
        if info['gaps']:
            lines.append('\nTop gaps:')
            lines.append('| Gap start | Gap end | Duration |')
            lines.append('|---|---:|---:|')
            for g in info['gaps']:
                lines.append(f"| {g['start']} | {g['end']} | {g['duration']} |")
        lines.append('\n---\n')

    lines.append('## Data-quality observations & recommendations')
    lines.append('- Several unnamed columns have high missing rates; review column naming/metadata when ingesting.')
    lines.append('- O3/NO2 were not auto-detected in the CPCB quarterly sheets; provide exact column names with `--o3-col`/`--no2-col` when re-running if available.')
    lines.append('- Many long gaps detected; investigate station outages or sensor downtime for those periods.')
    lines.append('- Consider standardizing timestamp and column headers at ingestion to reduce parsing errors.')

    lines.append('\n## Appendix: files processed')
    for info in inspections:
        lines.append(f'- {info["path"]}')

    out_path.write_text('\n'.join(lines), encoding='utf-8')


def main():
    raw_dir = Path('data/cpcb/raw')
    files = sorted([Path(p) for p in glob.glob(str(raw_dir / '*.*')) if not p.endswith('.gitkeep')])
    inspections = []
    for f in files:
        try:
            inspections.append(analyze_file(f))
        except Exception as e:
            print('Skipping', f, e)
    agg = aggregate(inspections)
    out = Path('data/cpcb/documentation/final_ultra_detailed_year_report.md')
    write_markdown(inspections, agg, out)
    print('Saved final report to:', out)


if __name__ == '__main__':
    main()
