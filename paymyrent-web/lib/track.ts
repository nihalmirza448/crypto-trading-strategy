// Resilient lookup of per-track data (decision logs, trend) from a snapshot.
//
// The dashboard keys these maps by a track's `track_id`, but the external
// publisher does not always key them identically (e.g. `eth` vs `ETH` vs
// `eth_usd` vs an `ETH-USD-3x` label). An exact-key miss would silently render
// that track's execution log as empty while another track works. This helper
// falls back to case-insensitive and normalized matching so every track that
// has data renders it.

function normalize(s: string): string {
  return s.toLowerCase().replace(/[^a-z0-9]/g, "");
}

export function lookupByTrack<T>(
  map: Record<string, T> | undefined,
  trackId: string | undefined,
): T | undefined {
  if (!map || !trackId) return undefined;

  // 1. Exact key.
  if (Object.prototype.hasOwnProperty.call(map, trackId)) return map[trackId];

  const target = normalize(trackId);
  if (!target) return undefined;

  const keys = Object.keys(map);

  // 2. Case-insensitive / punctuation-insensitive exact match.
  for (const k of keys) {
    if (normalize(k) === target) return map[k];
  }

  // 3. Containment (e.g. "eth" vs "eth_usd", "eth-usd-3x" vs "eth").
  for (const k of keys) {
    const nk = normalize(k);
    if (nk && (nk.includes(target) || target.includes(nk))) return map[k];
  }

  return undefined;
}
