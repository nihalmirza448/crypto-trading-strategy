"use client";

import type {
  ConfluenceMetricRow,
  ForwardSnapshot,
  TrackStatus,
  TrendPoint,
} from "@/lib/types";
import { scoreTone } from "@/lib/score";

type Props = {
  tracks: TrackStatus[];
  metrics?: ForwardSnapshot["confluence_metrics"];
  trends?: Record<string, TrendPoint[]>;
  minScore: number;
};

function Sparkline({ points, min }: { points: TrendPoint[]; min: number }) {
  if (!points.length) {
    return (
      <div className="spark">
        {Array.from({ length: 12 }).map((_, i) => (
          <span key={i} />
        ))}
      </div>
    );
  }
  const max = Math.max(min, ...points.map((p) => p.score ?? 0), 7);
  return (
    <div className="spark" title="Score per bar (recent)">
      {points.map((p, i) => {
        const h = Math.max(8, Math.round(((p.score ?? 0) / max) * 100));
        const on = (p.score ?? 0) >= min;
        return (
          <span
            key={`${p.bar}-${i}`}
            className={on ? "on" : ""}
            style={{ height: `${h}%` }}
          />
        );
      })}
    </div>
  );
}

export function ConfluenceMetricsGrid({
  tracks,
  metrics,
  trends,
  minScore,
}: Props) {
  const rowById = new Map(
    (metrics?.rows || []).map((r) => [r.track_id, r] as const),
  );

  return (
    <div className="grid-metrics">
      {tracks.map((t) => {
        const row: ConfluenceMetricRow | undefined = rowById.get(t.track_id);
        const current = row?.current_score ?? t.confluence_score;
        const peak = row?.lookback_max ?? row?.max_score;
        const tone = scoreTone(current, minScore);
        const trend = trends?.[t.track_id] || [];

        return (
          <article key={t.track_id} className={`metric-card tone-${tone}`}>
            <h3>
              {t.label}{" "}
              <span className={`pill ${t.health === "ok" ? "ok" : "warn"}`}>
                {t.health}
              </span>
            </h3>
            <div className="score-big">{current ?? "—"}</div>
            <div className="meta">
              Min {minScore} · Peak {peak ?? "—"} (4d) ·{" "}
              {t.position
                ? `${t.position.direction} @ ${t.position.entry_price}`
                : "Flat"}
            </div>
            <div style={{ marginTop: "0.65rem", display: "flex", gap: "0.5rem" }}>
              <span
                className={`pill ${row?.gates_pass || t.gates_pass ? "ok" : "warn"}`}
              >
                Gates {row?.gates_pass || t.gates_pass ? "pass" : "fail"}
              </span>
              <span
                className={`pill ${row?.would_enter_now || t.would_enter ? "ok" : "warn"}`}
              >
                Will enter{" "}
                {row?.would_enter_now || t.would_enter ? "yes" : "no"}
              </span>
            </div>
            {(row?.block_reason || t.block_reason) && (
              <div className="meta" style={{ color: "var(--amber)" }}>
                Blocked: {row?.block_reason || t.block_reason}
              </div>
            )}
            <Sparkline points={trend} min={minScore} />
          </article>
        );
      })}
    </div>
  );
}
