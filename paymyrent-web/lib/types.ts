// Shared types for the Confluence Core forward-test dashboard.
// The snapshot is produced by the external forward-test publisher
// (`forward_test.publish_snapshot`) and POSTed to /api/ingest hourly.

export type GateCheck = {
  flat?: boolean;
  new_bar?: boolean;
  score_ok?: boolean;
  spacing_ok?: boolean;
  equity_ok?: boolean;
};

export type Position = {
  direction: string;
  entry_price: number | string;
};

export type TrackStatus = {
  track_id: string;
  label: string;
  confluence_score?: number | null;
  equity: number;
  start_capital?: number;
  pnl_pct: number;
  leverage?: number;
  gates_pass?: boolean;
  would_enter?: boolean;
  block_reason?: string;
  health?: string;
  position?: Position | null;
  gate_checks?: GateCheck;
  latest_decision?: string;
  latest_rationale?: string;
  latest_signals?: string;
  latest_bar?: string;
};

export type DecisionLogRow = {
  bar: string;
  price?: number | string | null;
  score: number;
  direction: string;
  decision: string;
  rationale: string;
  signals: string;
  gates_pass?: boolean;
  would_enter?: boolean;
};

export type TrendPoint = {
  bar: string;
  score: number | null;
  direction: string;
};

export type ConfluenceSignal = {
  id: string;
  points: number;
  long: string;
  short?: string;
};

export type EntryGate = {
  label: string;
  detail: string;
};

export type ExitRules = {
  description: string;
  bullets: string[];
  no_stop_loss?: boolean;
};

export type StrategyRules = {
  min_confluence_score?: number;
  confluence_signals: ConfluenceSignal[];
  entry_gates: EntryGate[];
  exit_rules: ExitRules;
  score_guide?: string[];
};

export type ConfluenceMetricRow = {
  track_id: string;
  current_score?: number;
  lookback_max?: number;
  max_score?: number;
  gates_pass?: boolean;
  would_enter_now?: boolean;
  block_reason?: string;
};

export type ConfluenceMetrics = {
  min_score?: number;
  rows?: ConfluenceMetricRow[];
};

export type ForwardSnapshot = {
  updated_at: string;
  published_from?: string;
  suite_running?: boolean;
  tracks: TrackStatus[];
  strategy_rules?: StrategyRules;
  confluence_metrics?: ConfluenceMetrics;
  decision_logs?: Record<string, { rows: DecisionLogRow[] }>;
  confluence_trend?: Record<string, TrendPoint[]>;
};
