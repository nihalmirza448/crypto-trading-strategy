"use client";

import type { DecisionLogRow } from "@/lib/types";
import { decisionTone } from "@/lib/score";

export function ExecutionLog({
  rows,
  trackLabel,
}: {
  rows: DecisionLogRow[];
  trackLabel: string;
}) {
  return (
    <div className="panel">
      <div className="panel-label">Execution log · {trackLabel}</div>
      <div className="exec-table-wrap">
        <table className="exec-table">
          <thead>
            <tr>
              <th>TIME</th>
              <th>PRICE</th>
              <th>SCORE</th>
              <th>DIR</th>
              <th>ACT</th>
              <th>RATIONALE</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ color: "var(--muted)" }}>
                  No logged decisions yet
                </td>
              </tr>
            ) : (
              rows.map((r, i) => {
                const cls = decisionTone(r.decision);
                return (
                  <tr key={`${r.bar}-${i}`}>
                    <td>{r.bar}</td>
                    <td>{r.price ?? "—"}</td>
                    <td style={{ color: "var(--neon-green)" }}>{r.score}</td>
                    <td>{r.direction}</td>
                    <td>
                      <span className={`badge ${cls}`}>{r.decision}</span>
                    </td>
                    <td style={{ maxWidth: 280 }}>{r.rationale}</td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
