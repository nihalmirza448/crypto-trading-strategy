"use client";

import type { GateCheck, StrategyRules, TrackStatus } from "@/lib/types";

const GATE_KEYS: { key: keyof GateCheck; label: string }[] = [
  { key: "flat", label: "FLAT" },
  { key: "new_bar", label: "NEW BAR" },
  { key: "score_ok", label: "SCORE" },
  { key: "spacing_ok", label: "SPACING" },
  { key: "equity_ok", label: "EQUITY" },
];

export function RulesSidebar({
  rules,
  track,
  minScore,
}: {
  rules?: StrategyRules;
  track: TrackStatus;
  minScore: number;
}) {
  const gc = track.gate_checks;

  return (
    <div className="rules-sidebar">
      <div className="panel">
        <h3>Entry gates · live</h3>
        <ul>
          {GATE_KEYS.map(({ key, label }) => {
            const v = gc?.[key];
            return (
              <li key={key}>
                <span className={v === true ? "gate-pass" : v === false ? "gate-fail" : ""}>
                  {v === true ? "✓" : v === false ? "✗" : "·"}
                </span>
                <span>{label}</span>
              </li>
            );
          })}
        </ul>
      </div>

      {rules && (
        <>
          <div className="panel">
            <h3>Confluence signals</h3>
            <ul>
              {rules.confluence_signals.slice(0, 8).map((s) => (
                <li key={s.id}>
                  <span className="gate-pass">+{s.points}</span>
                  <span>{s.id.replace(/_/g, " ")}</span>
                </li>
              ))}
            </ul>
            <p style={{ fontSize: "0.65rem", color: "var(--muted)", margin: "0.5rem 0 0" }}>
              Min score: {minScore}
            </p>
          </div>

          <div className="panel">
            <h3>Exit rules</h3>
            <ul>
              {rules.exit_rules.bullets.slice(0, 4).map((b, i) => (
                <li key={i}>{b}</li>
              ))}
            </ul>
          </div>
        </>
      )}
    </div>
  );
}
