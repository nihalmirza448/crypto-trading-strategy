// Small presentation helpers shared across dashboard components.

// Map a decision string to a CSS badge tone (`.badge.enter|exit|skip`).
export function decisionTone(decision?: string | null): "enter" | "exit" | "skip" {
  const d = (decision || "").trim().toUpperCase();
  if (d === "ENTER" || d === "BUY" || d === "LONG" || d === "ADD") return "enter";
  if (d === "EXIT" || d === "SELL" || d === "CLOSE" || d === "TP" || d === "SL")
    return "exit";
  return "skip";
}

// Map a confluence score vs. the min-to-enter into a stat tone
// (`.stat-value.hit|near|low`).
export function scoreTone(
  score?: number | null,
  minScore = 3,
): "hit" | "near" | "low" {
  const s = score ?? 0;
  if (s >= minScore) return "hit";
  if (s >= minScore - 1) return "near";
  return "low";
}

// Human-readable "time since" for an ISO timestamp, e.g. "5m ago".
export function formatAge(iso?: string): string {
  if (!iso) return "—";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "—";
  const secs = Math.max(0, Math.round((Date.now() - then) / 1000));
  if (secs < 60) return `${secs}s ago`;
  const mins = Math.round(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  return `${days}d ago`;
}
