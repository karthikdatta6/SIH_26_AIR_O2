import argparse
import re
import sys
from pathlib import Path

import pandas as pd

TIMESTAMP_HINTS = ["from date", "date", "timestamp", "datetime", "time"]
O3_HINTS = ["o3", "ozone"]
NO2_HINTS = ["no2", "nox2", "nitrogen dioxide"]


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def load_raw(path, sheet):
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--sheet", default=None)
    ap.add_argument("--station-name", default="Anand Vihar")
    ap.add_argument("--station-id", default="")
    ap.add_argument("--agency", default="")
    ap.add_argument("--latitude", default="")
    ap.add_argument("--longitude", default="")
    ap.add_argument("--timestamp-col", default=None)
    ap.add_argument("--o3-col", default=None)
    ap.add_argument("--no2-col", default=None)
    ap.add_argument("--gap-multiple", type=float, default=2.0)
    ap.add_argument("--top-gaps", type=int, default=15)
    args = ap.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"ERROR: file not found: {path}")
        sys.exit(1)

    df, header_row = load_raw(path, args.sheet)
    print(f"Loaded {path.name} (header at row {header_row}, {len(df)} rows, {len(df.columns)} columns)\n")
    print("Columns found:")
    for c in df.columns:
        print(f"  - {c}")
    print()

    ts_col = args.timestamp_col or guess_column(df.columns, TIMESTAMP_HINTS)
    o3_col = args.o3_col or guess_column(df.columns, O3_HINTS)
    no2_col = args.no2_col or guess_column(df.columns, NO2_HINTS)

    print(f"Timestamp column: {ts_col!r}")
    print(f"O3 column: {o3_col!r}")
    print(f"NO2 column: {no2_col!r}\n")

    if ts_col is None:
        print("Could not detect a timestamp column. Re-run with --timestamp-col \"<exact name>\"")
        sys.exit(1)

    ts = pd.to_datetime(df[ts_col], errors="coerce", dayfirst=True)
    n_bad_ts = ts.isna().sum()
    ts_valid = ts.dropna().sort_values()

    total_rows = len(df)
    start_date = ts_valid.min() if not ts_valid.empty else None
    end_date = ts_valid.max() if not ts_valid.empty else None

    freq_label = "unknown"
    modal_delta = None
    if len(ts_valid) > 1:
        deltas = ts_valid.diff().dropna()
        if not deltas.empty:
            modal_delta = deltas.mode().iloc[0]
            freq_label = str(modal_delta)

    def missing_pct(col):
        if col is None or col not in df.columns:
            return None
        series = pd.to_numeric(df[col], errors="coerce")
        return round(series.isna().mean() * 100, 2)

    o3_missing = missing_pct(o3_col)
    no2_missing = missing_pct(no2_col)

    gaps_report = []
    if len(ts_valid) > 1 and modal_delta is not None:
        deltas = ts_valid.diff().dropna()
        threshold = modal_delta * args.gap_multiple
        gap_mask = deltas > threshold
        gap_deltas = deltas[gap_mask].sort_values(ascending=False).head(args.top_gaps)
        for idx, dur in gap_deltas.items():
            gap_end = ts_valid.loc[idx]
            gap_start = ts_valid.shift(1).loc[idx]
            gaps_report.append((gap_start, gap_end, dur))

    lines = []
    lines.append(f"# Pilot Data-Quality Report — {args.station_name}\n")
    lines.append("| Field | Result |")
    lines.append("|---|---|")
    lines.append(f"| Station | {args.station_name} |")
    lines.append(f"| Station ID | {args.station_id or '(fill in)'} |")
    lines.append(f"| Agency | {args.agency or '(fill in)'} |")
    lines.append(f"| Coordinates | {args.latitude}, {args.longitude} |")
    lines.append(f"| Start date | {start_date} |")
    lines.append(f"| End date | {end_date} |")
    lines.append(f"| Frequency (inferred) | {freq_label} |")
    lines.append(f"| Rows | {total_rows} |")
    lines.append(f"| Unparseable timestamps | {n_bad_ts} |")
    lines.append(f"| O3 column detected | {o3_col if o3_col else 'NOT FOUND'} |")
    lines.append(f"| NO2 column detected | {no2_col if no2_col else 'NOT FOUND'} |")
    lines.append(f"| O3 available? | {'Yes' if o3_col else 'No'} |")
    lines.append(f"| NO2 available? | {'Yes' if no2_col else 'No'} |")
    lines.append(f"| O3 missing % | {o3_missing if o3_missing is not None else 'N/A'} |")
    lines.append(f"| NO2 missing % | {no2_missing if no2_missing is not None else 'N/A'} |")
    lines.append(f"| Number of gaps > {args.gap_multiple}x frequency | {len(gaps_report)} |")
    lines.append("")

    if gaps_report:
        lines.append(f"## Top {len(gaps_report)} longest gaps\n")
        lines.append("| Gap start | Gap end | Duration |")
        lines.append("|---|---|---|")
        for gs, ge, dur in gaps_report:
            lines.append(f"| {gs} | {ge} | {dur} |")
        lines.append("")

    lines.append("## Notes")
    lines.append("- Read-only: this script did not modify the raw file.")
    lines.append(f"- Source file: `{path}`")

    report_text = "\n".join(lines)
    print("\n" + "=" * 70 + "\n")
    print(report_text)

    out_dir = Path("data/cpcb/documentation")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{slugify(args.station_name)}_pilot_report.md"
    out_path.write_text(report_text, encoding="utf-8")
    print(f"\nSaved report to: {out_path}")


if __name__ == "__main__":
    main()