"use client";

import { useMemo } from "react";
import type { TrackStatus } from "@/lib/types";
import { buildConfluenceFlow } from "@/lib/flow";

type LayoutNode = {
  id: string;
  x: number;
  y: number;
  label: string;
  kind: string;
  active: boolean;
  detail?: string;
  fail?: boolean;
};

export function ConfluenceFlowDiagram({
  track,
  minScore,
}: {
  track: TrackStatus;
  minScore: number;
}) {
  const { nodes, edges, side } = useMemo(
    () => buildConfluenceFlow(track, minScore),
    [track, minScore],
  );

  const layout = useMemo(() => {
    const inputs = nodes.filter((n) => n.kind === "input");
    const gates = nodes.filter((n) => n.kind === "gate");
    const conditions = nodes.filter(
      (n) => n.kind === "condition" && n.id !== "bias",
    );
    const bias = nodes.find((n) => n.id === "bias");
    const outcome = nodes.find((n) => n.kind === "outcome");

    const laid: LayoutNode[] = [];
    const w = 100;
    const h = 100;

    if (bias) {
      laid.push({
        id: bias.id,
        x: 8,
        y: 50,
        label: bias.label,
        kind: bias.kind,
        active: bias.active,
        detail: side,
      });
    }

    const inputCount = Math.max(inputs.length, 1);
    inputs.forEach((n, i) => {
      const y = 15 + (i * 70) / Math.max(inputCount - 1, 1);
      laid.push({
        id: n.id,
        x: 22,
        y: inputCount === 1 ? 50 : y,
        label: n.label,
        kind: n.kind,
        active: n.active,
        detail: n.detail,
      });
    });

    conditions.forEach((n) => {
      laid.push({
        id: n.id,
        x: 42,
        y: 50,
        label: n.label,
        kind: n.kind,
        active: n.active,
        detail: n.detail,
      });
    });

    gates.forEach((n, i) => {
      const y = 20 + (i * 60) / Math.max(gates.length - 1, 1);
      laid.push({
        id: n.id,
        x: 58,
        y: gates.length === 1 ? 50 : y,
        label: n.label,
        kind: n.kind,
        active: n.active,
        detail: n.detail,
        fail: n.detail === "FAIL",
      });
    });

    if (outcome) {
      laid.push({
        id: outcome.id,
        x: 88,
        y: 50,
        label: outcome.label,
        kind: outcome.kind,
        active: outcome.active,
        detail: undefined,
      });
    }

    return { laid, edges, w, h };
  }, [nodes, edges, side]);

  const posMap = new Map(layout.laid.map((n) => [n.id, n]));

  function pathD(fromId: string, toId: string) {
    const a = posMap.get(fromId);
    const b = posMap.get(toId);
    if (!a || !b) return "";
    const x1 = a.x;
    const y1 = a.y;
    const x2 = b.x;
    const y2 = b.y;
    const mx = (x1 + x2) / 2;
    return `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`;
  }

  const scoreNode = layout.laid.find((n) => n.id === "score");
  const scoreDetail = scoreNode?.detail || "";

  return (
    <div className="flow-panel panel">
      <div className="flow-title">CONFLUENCE CORE · DECISION FLOW</div>
      <div className="flow-canvas">
        <svg
          className="flow-svg"
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
        >
          {layout.edges.map((e, i) => {
            const d = pathD(e.from, e.to);
            if (!d) return null;
            return (
              <path
                key={`${e.from}-${e.to}-${i}`}
                d={d}
                className={`flow-path ${e.active ? "active" : ""}`}
                strokeDasharray={e.active ? "6 4" : undefined}
                vectorEffect="non-scaling-stroke"
              />
            );
          })}
        </svg>

        {scoreDetail && (
          <div
            className={`flow-box ${scoreNode?.active ? "active" : ""}`}
            style={{ left: "42%", top: "38%" }}
          >
            IF score ≥ {minScore}
          </div>
        )}

        {layout.laid.map((n) => (
          <div
            key={n.id}
            className={`flow-node kind-${n.kind} ${n.active ? "active" : ""} ${n.fail ? "fail" : ""}`}
            style={{ left: `${n.x}%`, top: `${n.y}%` }}
            title={n.detail}
          >
            <div className="flow-node-circle">{n.label.split(" ")[0]}</div>
            <div className="flow-node-detail">
              {n.label.length > 12 ? n.label.slice(0, 10) + "…" : n.label}
            </div>
            {n.detail && n.kind === "input" && (
              <div className="flow-node-detail">{String(n.detail).slice(0, 12)}</div>
            )}
          </div>
        ))}
      </div>

      <div className="rationale-banner">
        <span className="tag">{track.latest_decision || "HOLD"}</span>
        {track.latest_rationale || "Waiting for next agent cycle…"}
      </div>
    </div>
  );
}
