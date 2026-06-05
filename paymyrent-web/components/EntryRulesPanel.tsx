"use client";

import type { GateCheck, StrategyRules, TrackStatus } from "@/lib/types";

type Props = {
  rules?: StrategyRules;
  tracks: TrackStatus[];
  minScore: number;
};

const GATE_KEYS: { key: keyof GateCheck; label: string }[] = [
  { key: "flat", label: "Flat" },
  { key: "new_bar", label: "New bar" },
  { key: "score_ok", label: "Score OK" },
  { key: "spacing_ok", label: "Entry spacing" },
  { key: "equity_ok", label: "Equity OK" },
];

function GateStatus({ gc }: { gc?: GateCheck }) {
  if (!gc) return <span style={{ color: "var(--muted)" }}>—</span>;
  return (
    <>
      {GATE_KEYS.map(({ key, label }) => {
        const v = gc[key];
        if (v === undefined) return null;
        const icon = v ? "✓" : "✗";
        const color = v ? "var(--green)" : "var(--red)";
        return (
          <div key={key} className="gate-row">
            <span className="gate-icon" style={{ color }}>
              {icon}
            </span>
            <span>
              <strong>{label}</strong>
            </span>
          </div>
        );
      })}
    </>
  );
}

export function EntryRulesPanel({ rules, tracks, minScore }: Props) {
  if (!rules) {
    return <p style={{ color: "var(--muted)" }}>Strategy rules not in snapshot.</p>;
  }

  const sample = tracks.find((t) => t.gate_checks) || tracks[0];

  return (
    <div className="rules-grid">
      <div className="panel">
        <h3 style={{ marginTop: 0, color: "var(--lime)" }}>
          Gates (must all pass)
        </h3>
        <ul>
          {rules.entry_gates.map((g) => (
            <li key={g.label}>
              <strong>{g.label}</strong> — {g.detail}
            </li>
          ))}
        </ul>
        {sample && (
          <>
            <h4 style={{ fontSize: "0.85rem", color: "var(--accent)" }}>
              Live gate check — {sample.label}
            </h4>
            <GateStatus gc={sample.gate_checks} />
          </>
        )}
      </div>

      <div className="panel">
        <h3 style={{ marginTop: 0, color: "var(--accent)" }}>
          Confluence Core signals (+1 each)
        </h3>
        <ul>
          {rules.confluence_signals.map((s) => (
            <li key={s.id}>
              <strong>{s.id}</strong> ({s.points}pt) — {s.long}
            </li>
          ))}
        </ul>
        <p style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
          Minimum score to enter: <strong>{minScore}</strong>
          {rules.score_guide?.length ? (
            <>
              <br />
              {rules.score_guide.join(" · ")}
            </>
          ) : null}
        </p>
      </div>

      <div className="panel">
        <h3 style={{ marginTop: 0, color: "var(--amber)" }}>Exit rules</h3>
        <p style={{ fontSize: "0.9rem" }}>{rules.exit_rules.description}</p>
        <ul>
          {rules.exit_rules.bullets.map((b, i) => (
            <li key={i}>{b}</li>
          ))}
        </ul>
        {rules.exit_rules.no_stop_loss && (
          <p className="pill warn" style={{ display: "inline-block" }}>
            No stop-loss
          </p>
        )}
      </div>
    </div>
  );
}
