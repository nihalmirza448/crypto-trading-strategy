"use client";

import type { ForwardSnapshot, TrackStatus, TrendPoint } from "@/lib/types";
import { scoreTone } from "@/lib/score";

function MiniChart({ points, min }: { points: TrendPoint[]; min: number }) {
  const data = points.length
    ? points
    : Array.from({ length: 12 }, (_, i) => ({ bar: "", score: 0, direction: "" }));
  const max = Math.max(min, ...data.map((p) => p.score ?? 0), 1);
  return (
    <div className="mini-chart">
      {data.map((p, i) => {
        const s = p.score ?? 0;
        const h = Math.max(12, Math.round((s / max) * 100));
        const cls =
          s >= min ? "up" : s >= min - 1 && s > 0 ? "mid" : "";
        return (
          <span
            key={`${p.bar}-${i}`}
            className={cls}
            style={{ height: `${h}%` }}
            title={p.bar ? `${p.bar}: ${s}` : undefined}
          />
        );
      })}
    </div>
  );
}

export function TopMetricsStrip({
  track,
  allTracks,
  trends,
  minScore,
}: {
  track: TrackStatus;
  allTracks: TrackStatus[];
  trends?: Record<string, TrendPoint[]>;
  minScore: number;
}) {
  const totalEquity = allTracks.reduce((s, t) => s + (t.equity || 0), 0);
  const totalStart = allTracks.reduce((s, t) => s + (t.start_capital || 0), 0);
  const totalPnl = totalStart
    ? ((totalEquity - totalStart) / totalStart) * 100
    : 0;
  const score = track.confluence_score;
  const tone = scoreTone(score, minScore);
  const trend = trends?.[track.track_id] || [];

  return (
    <div className="metrics-row">
      <div className="panel hero-metric">
        <div className="panel-label">Portfolio equity (paper)</div>
        <div
          className={`hero-value ${totalPnl >= 0 ? "positive" : "negative"}`}
        >
          ${Math.round(totalEquity).toLocaleString()}
        </div>
        <div className="hero-sub">
          {totalPnl >= 0 ? "+" : ""}
          {totalPnl.toFixed(2)}% aggregate · {track.label} selected
        </div>
      </div>

      <div className="panel">
        <div className="panel-label">Confluence Core · now</div>
        <div className={`stat-value ${tone}`}>{score ?? "—"}</div>
        <div className="hero-sub">min {minScore} to enter</div>
        <MiniChart points={trend} min={minScore} />
      </div>

      <div className="panel">
        <div className="panel-label">Track PnL</div>
        <div
          className={`stat-value ${track.pnl_pct >= 0 ? "hit" : "negative"}`}
          style={track.pnl_pct < 0 ? { color: "var(--neon-red)" } : undefined}
        >
          {track.pnl_pct >= 0 ? "+" : ""}
          {track.pnl_pct}%
        </div>
        <div className="hero-sub">
          ${track.equity?.toLocaleString()} · {track.leverage}x
        </div>
      </div>

      <div className="panel">
        <div className="panel-label">Gates / enter</div>
        <div className="hero-sub" style={{ marginTop: "0.5rem" }}>
          <span
            className="pill"
            style={{
              color: track.gates_pass ? "var(--neon-green)" : "var(--neon-red)",
            }}
          >
            GATES {track.gates_pass ? "PASS" : "FAIL"}
          </span>
        </div>
        <div className="hero-sub">
          WILL ENTER:{" "}
          <span style={{ color: track.would_enter ? "var(--neon-green)" : "var(--muted)" }}>
            {track.would_enter ? "YES" : "NO"}
          </span>
        </div>
        {track.block_reason && (
          <div className="hero-sub" style={{ color: "var(--neon-orange)" }}>
            {track.block_reason}
          </div>
        )}
      </div>

      <div className="panel">
        <div className="panel-label">Position</div>
        <div
          className="stat-value"
          style={{
            fontSize: "1rem",
            color: track.position ? "var(--neon-green)" : "var(--muted)",
          }}
        >
          {track.position
            ? `${track.position.direction}`
            : "FLAT"}
        </div>
        {track.position && (
          <div className="hero-sub">@ {track.position.entry_price}</div>
        )}
      </div>
    </div>
  );
}
