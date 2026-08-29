// IST is a fixed UTC+5:30 offset (India doesn't observe DST), so this is a
// plain arithmetic shift, not a full timezone library. Reads the shifted
// instant back out via UTC getters (not local getters) so the result is
// correct regardless of the viewing browser's own local timezone.
const IST_OFFSET_MINUTES = 5 * 60 + 30;

export function formatIst(isoUtc: string): string {
  const utcDate = new Date(isoUtc);
  const ist = new Date(utcDate.getTime() + IST_OFFSET_MINUTES * 60 * 1000);
  const yyyy = ist.getUTCFullYear();
  const mm = String(ist.getUTCMonth() + 1).padStart(2, "0");
  const dd = String(ist.getUTCDate()).padStart(2, "0");
  const hh = String(ist.getUTCHours()).padStart(2, "0");
  const min = String(ist.getUTCMinutes()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd} ${hh}:${min} IST`;
}
