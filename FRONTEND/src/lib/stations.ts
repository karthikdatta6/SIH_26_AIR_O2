export interface Station {
  id: string;
  name: string;
  lat: number;
  lon: number;
  zone: string;
}

// UI station list — intentionally diverges from config/stations.csv
// (the real Phase 1 data-collection source of truth):
//  - Lodhi Road swapped for R K Puram per UI-only request.
//  - Punjabi Bagh's lat/lon corrected: the CSV value (28.563262,
//    77.186937) sits ~11km south of the real West Delhi locality, in
//    the same latitude band as R K Puram/INA, inconsistent with its own
//    zone:"WEST" tag. Replaced with an estimate near the actual
//    Punjabi Bagh area (Ring Road / Punjabi Bagh Metro).
// Both R K Puram's and Punjabi Bagh's coordinates here are best-effort
// estimates, not verified CPCB station coordinates — confirm against
// official records before this feeds real data collection, and flag
// the Punjabi Bagh discrepancy to whoever owns config/stations.csv.
export const STATIONS: Station[] = [
  { id: "ANAND_VIHAR", name: "Anand Vihar", lat: 28.646835, lon: 77.316032, zone: "EAST" },
  { id: "ITO", name: "ITO", lat: 28.628624, lon: 77.24106, zone: "CENTRAL" },
  { id: "OKHLA_PHASE_2", name: "Okhla Phase-II", lat: 28.530785, lon: 77.271255, zone: "SOUTH-EAST" },
  { id: "AYA_NAGAR", name: "Aya Nagar", lat: 28.4706914, lon: 77.1099364, zone: "SOUTH" },
  { id: "RK_PURAM", name: "R K Puram", lat: 28.5646, lon: 77.1822, zone: "SOUTH" },
  { id: "DHYAN_CHAND_STADIUM", name: "Dhyan Chand National Stadium", lat: 28.611281, lon: 77.237738, zone: "CENTRAL" },
  { id: "MANDIR_MARG", name: "Mandir Marg", lat: 28.636429, lon: 77.201067, zone: "CENTRAL" },
  { id: "PUNJABI_BAGH", name: "Punjabi Bagh", lat: 28.6626, lon: 77.1327, zone: "WEST" },
  { id: "JAHANGIRPURI", name: "Jahangirpuri", lat: 28.73282, lon: 77.170633, zone: "NORTH-WEST" },
  { id: "DWARKA_SECTOR_8", name: "Dwarka Sector-8", lat: 28.5710274, lon: 77.0719006, zone: "SOUTH-WEST" },
];

export function getStation(id: string): Station | undefined {
  return STATIONS.find((s) => s.id === id);
}
