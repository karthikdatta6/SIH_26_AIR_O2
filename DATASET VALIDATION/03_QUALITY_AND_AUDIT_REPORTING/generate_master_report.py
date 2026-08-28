import glob
import re
from pathlib import Path
import pandas as pd

TIMESTAMP_HINTS = ["from date", "date", "timestamp", "datetime", "time"]
O3_HINTS = ["o3", "ozone"]
NO2_HINTS = ["no2", "nox2", "nitrogen dioxide"]


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def load_raw(path: Path, sheet=None):
    read_kwargs = {}
    if path.suffix.lower() in (".xlsx", ".xls"):
        reader = pd.read_excel
        if sheet:
            read_kwargs["sheet_name"] = sheet
    else:
        reader = pd.read_csv

    probe = reader(path, header=None, nrows=20, **read_kwargs)
    header_row = 0
    for i in range(len(probe)):
        row_values = [str(v).strip().lower() for v in probe.iloc[i].tolist()]
        if any(any(hint in cell for hint in TIMESTAMP_HINTS) for cell in row_values):
            header_row = i
            break

    df = reader(path, header=header_row, **read_kwargs)
    df.columns = [str(c).strip() for c in df.columns]
    return df, header_row


def guess_column(columns, hints):
    for col in columns:
        low = col.lower()
        if any(hint in low for hint in hints):
            return col
    return None


def inspect_file(path: Path):
    df, header = load_raw(path)
    cols = list(df.columns)
    ts_col = guess_column(cols, TIMESTAMP_HINTS)
    o3_col = guess_column(cols, O3_HINTS)
    no2_col = guess_column(cols, NO2_HINTS)

    ts = pd.to_datetime(df[ts_col], errors="coerce", dayfirst=True) if ts_col else pd.NaT
    n_bad_ts = int(ts.isna().sum()) if ts_col else None
    ts_valid = ts.dropna().sort_values() if ts_col else pd.Series([], dtype="datetime64[ns]")

    total_rows = len(df)
    start_date = ts_valid.min() if not ts_valid.empty else None
    end_date = ts_valid.max() if not ts_valid.empty else None

    modal_delta = None
    freq_label = "unknown"
    if len(ts_valid) > 1:
        deltas = ts_valid.diff().dropna()
        if not deltas.empty:
            modal_delta = deltas.mode().iloc[0]
            freq_label = str(modal_delta)

    # Per-column missing counts (numeric conversion)
    col_stats = {}
    for c in cols:
        if c == ts_col:
            col_stats[c] = {"missing": int(ts.isna().sum()) if ts_col else total_rows, "total": total_rows}
            continue
        series = pd.to_numeric(df[c], errors="coerce")
        missing = int(series.isna().sum())
        col_stats[c] = {"missing": missing, "total": total_rows, "non_missing": total_rows - missing}

    # Gaps
    gaps_report = []
    if len(ts_valid) > 1 and modal_delta is not None:
        deltas = ts_valid.diff().dropna()
        threshold = modal_delta * 2.0
        gap_mask = deltas > threshold
        gap_deltas = deltas[gap_mask].sort_values(ascending=False)
        for idx, dur in gap_deltas.items():
            gap_end = ts_valid.loc[idx]
            gap_start = ts_valid.shift(1).loc[idx]
            gaps_report.append({"start": gap_start, "end": gap_end, "duration": dur})

    return {
        "path": str(path),
        "name": path.stem,
        "rows": total_rows,
        "header_row": header,
        "columns": cols,
        "timestamp_col": ts_col,
        "o3_col": o3_col,
        "no2_col": no2_col,
        "n_bad_ts": n_bad_ts,
        "start_date": start_date,
        "end_date": end_date,
        "freq_label": freq_label,
        "col_stats": col_stats,
        "gaps": gaps_report,
    }


def aggregate(inspections):
    all_cols = set()
    total_rows = 0
    total_valid_ts = 0
    global_start = None
    global_end = None
    per_col = {}

    for info in inspections:
        total_rows += info["rows"]
        if info["start_date"] is not None:
            global_start = info["start_date"] if (global_start is None or info["start_date"] < global_start) else global_start
        if info["end_date"] is not None:
            global_end = info["end_date"] if (global_end is None or info["end_date"] > global_end) else global_end

        for c, stats in info["col_stats"].items():
            all_cols.add(c)
            if c not in per_col:
                per_col[c] = {"missing": 0, "total": 0, "files_present": 0, "non_missing": 0}
            per_col[c]["missing"] += stats.get("missing", 0)
            per_col[c]["total"] += stats.get("total", 0)
            per_col[c]["non_missing"] += stats.get("non_missing", 0) if stats.get("non_missing") is not None else stats.get("total", 0) - stats.get("missing", 0)
            per_col[c]["files_present"] += 1

    return {
        "all_columns": sorted(list(all_cols)),
        "total_rows": total_rows,
        "global_start": global_start,
        "global_end": global_end,
        "per_column": per_col,
        "files": len(inspections),
    }


def write_report(inspections, agg, out_path: Path):
    lines = []
    lines.append(f"# Master Data-Quality Report — Year Overview\n")
    lines.append(f"Files inspected: {len(inspections)}")
    lines.append(f"Total rows (sum of files): {agg['total_rows']}")
    lines.append(f"Global start: {agg['global_start']}")
    lines.append(f"Global end: {agg['global_end']}")
    lines.append("")

    lines.append("## Parameter Inventory\n")
    lines.append("- Columns found across files:")
    for c in agg["all_columns"]:
        info = agg["per_column"][c]
        missing = info["missing"]
        total = info["total"]
        nm = info["non_missing"]
        pct_missing = round(missing / total * 100, 2) if total else 0.0
        lines.append(f"  - `{c}`: present in {info['files_present']} files; non-missing values: {nm} / {total} ({100 - pct_missing}% present, {pct_missing}% missing)")

    lines.append("\n## Per-file summaries\n")
    for info in inspections:
        lines.append(f"### {info['name']}")
        lines.append(f"- Path: {info['path']}")
        lines.append(f"- Rows: {info['rows']}")
        lines.append(f"- Header row: {info['header_row']}")
        lines.append(f"- Timestamp column: {info['timestamp_col']}")
        lines.append(f"- Timestamp parse failures: {info['n_bad_ts']}")
        lines.append(f"- Start: {info['start_date']}")
        lines.append(f"- End: {info['end_date']}")
        lines.append(f"- Inferred frequency: {info['freq_label']}")
        lines.append(f"- Columns: {', '.join(info['columns'])}")
        lines.append("- Column missing stats:")
        for c, st in info["col_stats"].items():
            total = st.get('total', info['rows'])
            missing = st.get('missing', 0)
            nm = st.get('non_missing', total - missing)
            pct_missing = round(missing / total * 100, 2) if total else 0.0
            lines.append(f"  - `{c}`: {nm}/{total} present, {pct_missing}% missing")
        lines.append("")

    lines.append("\n## Data-quality highlights\n")
    # Complete / partial rows for O3/NO2 if available
    total_complete = 0
    total_partial = 0
    total_valid_ts = 0
    for info in inspections:
        path = Path(info['path'])
        df, _ = load_raw(path)
        ts_col = info['timestamp_col']
        ts = pd.to_datetime(df[ts_col], errors='coerce', dayfirst=True) if ts_col else pd.Series([pd.NaT]*len(df))
        valid_ts_mask = ts.notna()
        total_valid_ts += int(valid_ts_mask.sum())
        o3 = info['o3_col']
        no2 = info['no2_col']
        if o3 and no2:
            comp = valid_ts_mask & df[o3].notna() & df[no2].notna()
            part = valid_ts_mask & (df[o3].notna() | df[no2].notna())
        elif o3 or no2:
            col = o3 if o3 else no2
            comp = valid_ts_mask & df[col].notna()
            part = comp
        else:
            comp = pd.Series([False]*len(df))
            part = pd.Series([False]*len(df))
        total_complete += int(comp.sum())
        total_partial += int(part.sum())

    lines.append(f"Total rows with parseable timestamps: {total_valid_ts}")
    lines.append(f"Total rows with at least one pollutant present (and parseable timestamp): {total_partial}")
    lines.append(f"Total rows with all primary pollutants present (and parseable timestamp): {total_complete}")

    out_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    raw_dir = Path("data/cpcb/raw")
    files = sorted([Path(p) for p in glob.glob(str(raw_dir / "*.*")) if not p.endswith('.gitkeep')])
    inspections = []
    for f in files:
        try:
            info = inspect_file(f)
            inspections.append(info)
        except Exception as e:
            print(f"Skipping {f}: {e}")

    agg = aggregate(inspections)
    out = Path("data/cpcb/documentation/year_master_report.md")
    write_report(inspections, agg, out)
    print(f"Saved master report to: {out}")


if __name__ == '__main__':
    main()
