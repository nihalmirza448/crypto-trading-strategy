// Builds the node/edge model for the Confluence Core decision-flow diagram
// from a track's live status. Pure function — no rendering concerns here.

import type { TrackStatus } from "@/lib/types";

export type FlowNode = {
  id: string;
  label: string;
  kind: "input" | "condition" | "gate" | "outcome";
  active: boolean;
  detail?: string;
};

export type FlowEdge = {
  from: string;
  to: string;
  active: boolean;
};

export type ConfluenceFlow = {
  nodes: FlowNode[];
  edges: FlowEdge[];
  side: string;
};

const GATE_LABELS: Record<string, string> = {
  flat: "FLAT",
  new_bar: "NEW BAR",
  score_ok: "SCORE",
  spacing_ok: "SPACING",
  equity_ok: "EQUITY",
};

function splitSignals(raw?: string): string[] {
  if (!raw) return [];
  return raw
    .split(/[;,]/)
    .map((s) => s.trim())
    .filter(Boolean);
}

function biasSide(track: TrackStatus): string {
  if (track.position?.direction) return track.position.direction.toUpperCase();
  const dec = (track.latest_decision || "").toUpperCase();
  if (dec.includes("LONG") || dec.includes("BUY")) return "LONG";
  if (dec.includes("SHORT") || dec.includes("SELL")) return "SHORT";
  const sig = (track.latest_signals || "").toLowerCase();
  if (sig.includes("long") || sig.includes("bull")) return "LONG";
  if (sig.includes("short") || sig.includes("bear")) return "SHORT";
  return "NEUTRAL";
}

export function buildConfluenceFlow(
  track: TrackStatus,
  minScore: number,
): ConfluenceFlow {
  const score = track.confluence_score ?? 0;
  const scoreOk = score >= minScore;
  const side = biasSide(track);
  const biasActive = side !== "NEUTRAL";

  const nodes: FlowNode[] = [];
  const edges: FlowEdge[] = [];

  // Bias / regime node.
  nodes.push({
    id: "bias",
    label: side === "NEUTRAL" ? "Bias" : `${side} bias`,
    kind: "condition",
    active: biasActive,
    detail: side,
  });

  // Input signals (confluence pool hits).
  const signals = splitSignals(track.latest_signals).slice(0, 5);
  if (signals.length === 0) {
    nodes.push({
      id: "in0",
      label: "No signals",
      kind: "input",
      active: false,
      detail: "—",
    });
  } else {
    signals.forEach((sig, i) => {
      const id = `in${i}`;
      nodes.push({
        id,
        label: sig,
        kind: "input",
        active: true,
        detail: sig,
      });
    });
  }

  // Confluence score condition.
  nodes.push({
    id: "score",
    label: `Score ${score}`,
    kind: "condition",
    active: scoreOk,
    detail: `${score}`,
  });

  // Entry gates.
  const gc = track.gate_checks;
  const gateEntries: { id: string; label: string; pass: boolean }[] = [];
  if (gc) {
    for (const [key, label] of Object.entries(GATE_LABELS)) {
      const v = gc[key as keyof typeof gc];
      if (v === undefined) continue;
      gateEntries.push({ id: `gate_${key}`, label, pass: !!v });
    }
  }
  if (gateEntries.length === 0) {
    gateEntries.push({
      id: "gate_all",
      label: "GATES",
      pass: !!track.gates_pass,
    });
  }
  gateEntries.forEach((g) => {
    nodes.push({
      id: g.id,
      label: g.label,
      kind: "gate",
      active: g.pass,
      detail: g.pass ? "PASS" : "FAIL",
    });
  });

  // Outcome.
  const willEnter = !!track.would_enter;
  nodes.push({
    id: "outcome",
    label: willEnter ? "ENTER" : "HOLD",
    kind: "outcome",
    active: willEnter,
  });

  // Edges: bias → inputs → score → gates → outcome.
  const inputNodes = nodes.filter((n) => n.kind === "input");
  inputNodes.forEach((n) => {
    edges.push({ from: "bias", to: n.id, active: biasActive && n.active });
    edges.push({ from: n.id, to: "score", active: n.active && scoreOk });
  });

  gateEntries.forEach((g) => {
    edges.push({ from: "score", to: g.id, active: scoreOk });
    edges.push({ from: g.id, to: "outcome", active: scoreOk && g.pass });
  });

  return { nodes, edges, side };
}
