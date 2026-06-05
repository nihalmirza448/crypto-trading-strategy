"use client";

import type { DecisionLogRow, TrackStatus } from "@/lib/types";
import { decisionTone } from "@/lib/score";

type Props = {
  tracks: TrackStatus[];
  decisionLogs?: Record<string, { rows: DecisionLogRow[] }>;
  minScore: number;
};

function signalsToChips(signals: string) {
  if (!signals || signals === "—") return null;
  return signals.split(";").map((s) => {
    const t = s.trim();
    if (!t) return null;
    return (
      <span key={t} className="chip">
        {t}
      </span>
    );
  });
}

export function DecisionFeed({ tracks, decisionLogs, minScore }: Props) {
  const primaryTrack = tracks[0]?.track_id;
  const allRows: { track: string; row: DecisionLogRow }[] = [];

  for (const t of tracks) {
    const log = decisionLogs?.[t.track_id];
    for (const row of (log?.rows || []).slice(0, 8)) {
      allRows.push({ track: t.label, row });
    }
  }

  allRows.sort((a, b) => (a.row.bar < b.row.bar ? 1 : -1));

  return (
    <>
      <div className="decision-hero">
        {tracks.map((t) => {
          const dec = t.latest_decision || "HOLD";
          const cls = decisionTone(dec);
          return (
            <div key={t.track_id} className={`decision-card ${cls}`}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <strong>{t.label}</strong>
                <span className={`decision-badge ${cls}`}>{dec}</span>
              </div>
              <p className="rationale">{t.latest_rationale || "—"}</p>
              <div className="signals-chips">
                {signalsToChips(t.latest_signals || "")}
              </div>
              {t.latest_bar && (
                <div className="meta mono" style={{ marginTop: "0.5rem" }}>
                  Bar {t.latest_bar}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="panel timeline">
        <h3 style={{ marginTop: 0 }}>Decision timeline</h3>
        <p className="sub" style={{ margin: "0 0 0.75rem" }}>
          Recent bars across tracks (score ≥ {minScore} or enter/exit events)
        </p>
        <table>
          <thead>
            <tr>
              <th>Track</th>
              <th>Bar</th>
              <th>Score</th>
              <th>Dir</th>
              <th>Decision</th>
              <th>Rationale</th>
              <th>Signals</th>
            </tr>
          </thead>
          <tbody>
            {allRows.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ color: "var(--muted)" }}>
                  No decision log rows yet — forward suite needs to run and
                  publish.
                </td>
              </tr>
            ) : (
              allRows.slice(0, 40).map(({ track, row }, i) => {
                const cls = decisionTone(row.decision);
                return (
                  <tr key={`${track}-${row.bar}-${i}`}>
                    <td>{track}</td>
                    <td className="mono">{row.bar}</td>
                    <td>{row.score}</td>
                    <td>{row.direction}</td>
                    <td>
                      <span className={`decision-badge ${cls}`}>
                        {row.decision}
                      </span>
                    </td>
                    <td>{row.rationale}</td>
                    <td>
                      <div className="signals-chips">
                        {signalsToChips(row.signals)}
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
        {primaryTrack && (
          <p style={{ marginTop: "0.75rem", fontSize: "0.85rem" }}>
            <a href="/signals">Full filterable log →</a>
          </p>
        )}
      </div>
    </>
  );
}
