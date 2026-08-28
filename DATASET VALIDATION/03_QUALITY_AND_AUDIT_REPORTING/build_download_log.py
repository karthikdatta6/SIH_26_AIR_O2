import os, csv

raw = r'C:\Users\saisu\OneDrive\Desktop\SIH 2026\PROJECT-AIRO2\data\cpcb\raw'

names = {
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

year_range = {
    '2023': '2023-01-01 to 2023-12-31',
    '2024': '2024-01-01 to 2024-12-31',
    '2025': '2025-01-01 to 2025-12-31',
}

notes_map = {
    'MANDIR_MARG_2024': 'Re-downloaded 2026-08-15 (original was corrupt at 8.8 KB). Replacement file: Mandir_marg_2_2024_Data.xlsx — 1496 KB. Now valid.',
}

rows = []
for fname in sorted(os.listdir(raw)):
    if not fname.endswith('.xlsx'):
        continue
    stem = fname.replace('_DATA.xlsx', '')
    parts = stem.rsplit('_', 1)
    year = parts[-1]
    station_id = stem.replace('_' + year, '')
    station_name = names.get(station_id, station_id)
    fpath = os.path.join(raw, fname)
    size_kb = round(os.path.getsize(fpath) / 1024, 1)
    key = station_id + '_' + year
    note = notes_map.get(key, 'Raw file preserved as downloaded. No modifications.')
    status = 'WARNING' if 'WARNING' in note else 'SUCCESS'
    rows.append({
        'download_date': '2026-08-15',
        'source': 'CPCB CCR Portal (https://airquality.cpcb.gov.in/ccr/)',
        'dataset': 'CPCB CAAQMS 15-min Ambient AQ',
        'station': station_name,
        'station_id': station_id,
        'file_name': fname,
        'date_range': year_range.get(year, ''),
        'variables': 'PM2.5,PM10,NO,NO2,NOX,NH3,SO2,CO,OZONE',
        'file_size_kb': size_kb,
        'status': status,
        'notes': note,
    })

out = r'C:\Users\saisu\OneDrive\Desktop\SIH 2026\PROJECT-AIRO2\data\cpcb\download_log.csv'
with open(out, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)

print('Written', len(rows), 'rows to download_log.csv')
for r in rows:
    flag = 'WARN' if r['status'] == 'WARNING' else 'OK  '
    print(flag, r['file_name'], ' ', r['file_size_kb'], 'KB')
