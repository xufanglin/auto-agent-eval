export function formatTimestamp(ts: string): string {
  if (!ts || ts.length < 15) return ts;
  // "20260318_020133" → "2026-03-18 02:01:33"
  return `${ts.slice(0, 4)}-${ts.slice(4, 6)}-${ts.slice(6, 8)} ${ts.slice(9, 11)}:${ts.slice(11, 13)}:${ts.slice(13, 15)}`;
}
