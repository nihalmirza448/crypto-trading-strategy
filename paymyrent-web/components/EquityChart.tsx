"use client";

import type { TrendPoint, TrackStatus } from "@/lib/types";

export function EquityChart({
  track,
  trend,
}: {
  track: TrackStatus;
  trend: TrendPoint[];
}) {
  const capital = track.start_capital || 1000;
  const points = trend.length
    ? trend.map((p, i) => {
        const drift = (p.score ?? 0) * 0.02;
        return capital * (1 + (i * drift) / 100 + (track.pnl_pct / 100) * (i / trend.length));
      })
    : [capital, track.equity];

  if (points.length < 2) {
    points.push(track.equity);
  }

  const min = Math.min(...points) * 0.98;
  const max = Math.max(...points) * 1.02;
  const range = max - min || 1;
  const w = 400;
  const h = 160;
  const pad = 8;

  const coords = points.map((v, i) => {
    const x = pad + (i / (points.length - 1)) * (w - pad * 2);
    const y = h - pad - ((v - min) / range) * (h - pad * 2);
    return `${x},${y}`;
  });

  const line = coords.join(" ");
  const area = `${coords[0]} L ${coords.slice(1).join(" L ")} L ${w - pad},${h} L ${pad},${h} Z`;
  const up = track.pnl_pct >= 0;

  return (
    <div className="panel">
      <div className="panel-label">Equity curve · {track.label}</div>
      <svg
        className="equity-chart-svg"
        viewBox={`0 0 ${w} ${h}`}
        preserveAspectRatio="none"
      >
        <defs>
          <linearGradient id="eqFill" x1="0" y1="0" x2="0" y2="1">
            <stop
              offset="0%"
              stopColor={up ? "#39ff14" : "#ff2d55"}
              stopOpacity="0.35"
            />
            <stop offset="100%" stopColor="#000" stopOpacity="0" />
          </linearGradient>
        </defs>
        <path d={area} fill="url(#eqFill)" />
        <polyline
          points={line}
          fill="none"
          stroke={up ? "#39ff14" : "#ff2d55"}
          strokeWidth="2"
          vectorEffect="non-scaling-stroke"
        />
      </svg>
      <div className="hero-sub">
        ${track.equity?.toLocaleString()} · {track.pnl_pct >= 0 ? "+" : ""}
        {track.pnl_pct}%
      </div>
    </div>
  );
}
