"use client";

import { useCallback, useEffect, useState } from "react";
import type { ForwardSnapshot } from "@/lib/types";
import { decisionTone } from "@/lib/score";
import { lookupByTrack } from "@/lib/track";
import Link from "next/link";

export default function SignalsPage() {
  const [data, setData] = useState<ForwardSnapshot | null>(null);
  const [trackId, setTrackId] = useState("");
  const [minScore, setMinScore] = useState(3);
  const [limit, setLimit] = useState(50);

  const load = useCallback(async () => {
    const res = await fetch("/api/status", { cache: "no-store" });
    if (res.ok) {
      const j = (await res.json()) as ForwardSnapshot;
      setData(j);
      if (!trackId && j.tracks[0]) setTrackId(j.tracks[0].track_id);
    }
  }, [trackId]);

  useEffect(() => {
    load();
    const id = setInterval(load, 15_000);
    return () => clearInterval(id);
  }, [load]);

  const log = trackId ? lookupByTrack(data?.decision_logs, trackId) : null;
  const rows = (log?.rows || []).filter(
    (r) => minScore <= 0 || r.score >= minScore || r.decision === "ENTER" || r.decision === "EXIT",
  ).slice(0, limit);

  return (
    <div className="terminal-shell">
      <div className="disclaimer">
        <strong>PAPER FORWARD TEST</strong> — full decision log
      </div>
      <header className="topbar">
        <Link href="/" className="logo">
          PAYMYRENT.AI
        </Link>
        <nav className="nav">
          <Link href="/">Dashboard</Link>
          <span style={{ color: "var(--neon-green)" }}>Signals</span>
          <Link href="/hire">Hire agent</Link>
        </nav>
      </header>
      <main className="main-cockpit section">
        <h2>Decision log</h2>
        <div className="panel" style={{ marginBottom: "1rem" }}>
          <label>
            Track{" "}
            <select
              value={trackId}
              onChange={(e) => setTrackId(e.target.value)}
              style={{ marginLeft: "0.5rem" }}
            >
              {(data?.tracks || []).map((t) => (
                <option key={t.track_id} value={t.track_id}>
                  {t.label}
                </option>
              ))}
            </select>
          </label>{" "}
          <label style={{ marginLeft: "1rem" }}>
            Min score{" "}
            <input
              type="number"
              min={0}
              max={10}
              value={minScore}
              onChange={(e) => setMinScore(Number(e.target.value))}
              style={{ width: "3rem", marginLeft: "0.35rem" }}
            />
          </label>{" "}
          <label style={{ marginLeft: "1rem" }}>
            Limit{" "}
            <input
              type="number"
              min={10}
              max={200}
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              style={{ width: "4rem", marginLeft: "0.35rem" }}
            />
          </label>
        </div>
        <div className="panel exec-table-wrap">
          <table className="exec-table">
            <thead>
              <tr>
                <th>Bar</th>
                <th>Price</th>
                <th>Score</th>
                <th>Dir</th>
                <th>Decision</th>
                <th>Rationale</th>
                <th>Signals</th>
                <th>Gates</th>
                <th>Enter?</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={`${r.bar}-${i}`}>
                  <td className="mono">{r.bar}</td>
                  <td className="mono">{r.price ?? "—"}</td>
                  <td>{r.score}</td>
                  <td>{r.direction}</td>
                  <td>
                    <span className={`badge ${decisionTone(r.decision)}`}>
                      {r.decision}
                    </span>
                  </td>
                  <td>{r.rationale}</td>
                  <td style={{ fontSize: "0.75rem" }}>{r.signals}</td>
                  <td>{r.gates_pass ? "Yes" : "No"}</td>
                  <td>{r.would_enter ? "Yes" : "No"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}
