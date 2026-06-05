"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { ForwardSnapshot } from "@/lib/types";
import { formatAge } from "@/lib/score";
import { TopMetricsStrip } from "./TopMetricsStrip";
import { ConfluenceFlowDiagram } from "./ConfluenceFlowDiagram";
import { RulesSidebar } from "./RulesSidebar";
import { ExecutionLog } from "./ExecutionLog";
import { EquityChart } from "./EquityChart";
import { ActivityFeed } from "./ActivityFeed";
import { HireSection } from "./HireSection";

const POLL_MS = 15_000;

export function DashboardClient() {
  const [data, setData] = useState<ForwardSnapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [trackId, setTrackId] = useState<string>("");

  const load = useCallback(async () => {
    try {
      const res = await fetch("/api/status", { cache: "no-store" });
      if (!res.ok) {
        const j = await res.json().catch(() => ({}));
        throw new Error((j as { error?: string }).error || res.statusText);
      }
      const j = (await res.json()) as ForwardSnapshot;
      setData(j);
      setError(null);
      setTrackId((prev) => {
        if (prev && j.tracks.some((t) => t.track_id === prev)) return prev;
        return j.tracks[0]?.track_id || "";
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, POLL_MS);
    return () => clearInterval(id);
  }, [load]);

  const minScore =
    data?.confluence_metrics?.min_score ??
    data?.strategy_rules?.min_confluence_score ??
    3;

  const track = useMemo(
    () => data?.tracks.find((t) => t.track_id === trackId) || data?.tracks[0],
    [data, trackId],
  );

  const logRows = useMemo(
    () => data?.decision_logs?.[track?.track_id || ""]?.rows || [],
    [data, track],
  );

  const trend = data?.confluence_trend?.[track?.track_id || ""] || [];

  return (
    <div className="terminal-shell">
      <div className="disclaimer">
        <strong>PAPER FORWARD TEST</strong> · rule-based agent · not financial
        advice
      </div>

      <header className="topbar">
        <div>
          <div className="logo">PAYMYRENT.AI</div>
          <div className="logo-sub">Confluence Core · live agent cockpit</div>
        </div>
        <nav className="nav">
          <a href="/" className="active">
            Dashboard
          </a>
          <a href="/signals">Signals</a>
          <a href="/hire">Hire</a>
          <a href="/how-it-works">Docs</a>
        </nav>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.72rem" }}>
          {data ? (
            <>
              <span
                className={`pill live pill-status ${data.suite_running ? "" : ""}`}
                style={
                  data.suite_running
                    ? undefined
                    : { color: "var(--neon-orange)", borderColor: "var(--neon-orange)" }
                }
              >
                {data.suite_running ? "LIVE" : "IDLE"}
              </span>{" "}
              <span style={{ color: "var(--muted)" }}>
                Δ {formatAge(data.updated_at)}
                {data.published_from ? ` · ${data.published_from}` : ""}
              </span>
            </>
          ) : loading ? (
            <span style={{ color: "var(--muted)" }}>SYNC…</span>
          ) : null}
        </div>
      </header>

      <main className="main-cockpit">
        {error && (
          <p style={{ color: "var(--neon-red)", fontFamily: "var(--font-mono)", fontSize: "0.8rem" }}>
            {error}
          </p>
        )}

        {data && track && (
          <>
            <div className="track-tabs">
              {data.tracks.map((t) => (
                <button
                  key={t.track_id}
                  type="button"
                  className={`track-tab ${t.track_id === track.track_id ? "active" : ""}`}
                  onClick={() => setTrackId(t.track_id)}
                >
                  {t.label} · {t.confluence_score ?? "—"}
                </button>
              ))}
            </div>

            <TopMetricsStrip
              track={track}
              allTracks={data.tracks}
              trends={data.confluence_trend}
              minScore={minScore}
            />

            <div
              className="metrics-row"
              style={{ gridTemplateColumns: "1fr", marginTop: "-0.25rem" }}
            >
              <div className="panel">
                <div className="panel-label">Recent decisions · stream</div>
                <ActivityFeed rows={logRows} />
              </div>
            </div>

            <div className="cockpit-grid">
              <ConfluenceFlowDiagram track={track} minScore={minScore} />
              <RulesSidebar
                rules={data.strategy_rules}
                track={track}
                minScore={minScore}
              />
            </div>

            <div className="bottom-row">
              <ExecutionLog rows={logRows.slice(0, 25)} trackLabel={track.label} />
              <EquityChart track={track} trend={trend} />
            </div>

            <HireSection compact />
          </>
        )}
      </main>

      <footer className="footer">
        AGENT DECISION LOG · RULE-BASED CONFLUENCE CORE + GATES · NOT INVESTMENT
        ADVICE
      </footer>
    </div>
  );
}
