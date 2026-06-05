"use client";

import type { DecisionLogRow } from "@/lib/types";
import { decisionTone } from "@/lib/score";

export function ActivityFeed({ rows }: { rows: DecisionLogRow[] }) {
  const lines = rows.slice(0, 6);
  return (
    <div className="activity-feed">
      {lines.length === 0 ? (
        <div className="activity-line skip">awaiting cycles…</div>
      ) : (
        lines.map((r, i) => {
          const tone = decisionTone(r.decision);
          const cls =
            tone === "enter" ? "buy" : tone === "exit" ? "sell" : "skip";
          return (
            <div key={`${r.bar}-${i}`} className={`activity-line ${cls}`}>
              <span>{r.bar?.slice(5, 16) || "—"}</span>
              <span>
                {r.decision} · {r.score}
              </span>
            </div>
          );
        })
      )}
    </div>
  );
}
