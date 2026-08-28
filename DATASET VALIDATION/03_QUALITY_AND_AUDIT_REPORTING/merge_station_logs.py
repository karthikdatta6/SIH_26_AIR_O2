"""
SIH 25178 - Team B (Sentinel-5P)
Merge every per-station download log (data/sentinel5p/_station_logs/*.csv,
one per station, written by run_sentinel5p_range.py so parallel station runs
never race on a shared file) into the single master
data/sentinel5p/download_log.csv.

Safe to run repeatedly - de-dupes on (product, date_range, geographic_area)
so re-running after more stations finish, or after pulling in another
laptop's _station_logs files via git, won't create duplicate rows.

Usage:
    python scripts/merge_station_logs.py
"""

import csv

import s5p_common as common


def _product_and_station(row):
    # product field looks like "S5P_OFFL_L2__NO2___"; geographic_area starts
    # with the station name, e.g. "ITO AOI bbox (...)". date_range is the
    # pilot date. Together these uniquely identify one (station, product, date).
    product = row["product"].split("_L2__")[-1].rstrip("_")
    return (row["geographic_area"], product, row["date_range"])


def main():
    log_dir = common.S5P_DIR / "_station_logs"
    station_logs = sorted(log_dir.glob("*_download_log.csv"))
    if not station_logs:
        print(f"No per-station logs found in {log_dir}")
        return

    existing_rows = []
    if common.DOWNLOAD_LOG.exists():
        with open(common.DOWNLOAD_LOG, newline="", encoding="utf-8") as f:
            existing_rows = list(csv.DictReader(f))

    seen = {_product_and_station(r) for r in existing_rows}
    merged_rows = list(existing_rows)
    added = 0
    skipped_dupe = 0

    for log_path in station_logs:
        with open(log_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                key = _product_and_station(row)
                if key in seen:
                    skipped_dupe += 1
                    continue
                seen.add(key)
                merged_rows.append(row)
                added += 1
        print(f"{log_path.name}: merged")

    with open(common.DOWNLOAD_LOG, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=common.DOWNLOAD_LOG_HEADER)
        writer.writeheader()
        writer.writerows(merged_rows)

    print(f"\nMaster log: {common.DOWNLOAD_LOG}")
    print(f"Rows before: {len(existing_rows)}  Added: {added}  Skipped (already present): {skipped_dupe}")
    print(f"Rows after: {len(merged_rows)}")


if __name__ == "__main__":
    main()
