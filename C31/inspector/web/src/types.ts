// The shapes of the inspector's JSON API (see the README, "The API").

export type FlagName = "loop" | "hidden_tool_error" | "duplicate_write" | "no_action" | "followed_injection";

export interface Dataset {
  id: string;
  mode: "saved" | "live";
  about: string;
  audit: boolean;
  error: string;
}

export interface Info {
  version: string;
  mode: "saved" | "live";
  default: string;
  datasets: Dataset[];
  flags: FlagName[];
  budget_per_resolved: number;
  tz_hours: number;
  links: { grafana: boolean; langfuse: boolean };
}

export interface RunRow {
  run_id: string;
  ticket: string;
  start: number;
  end: number;
  outcome: string;
  proposal: string;
  stop_reason: string;
  model_calls: number;
  reads: number;
  tool_calls: number;
  writes: number;
  replies: number;
  approvals: number;
  cost: number;
  tokens_in: number;
  tokens_out: number;
  duration_s: number;
  wait_s: number | null;
  approver: string;
  model: string;
  design: string;
  language: string;
  release: string;
  flags: FlagName[];
  traces: number;
  constructed: boolean;
}

export interface RunsAnswer {
  runs: RunRow[];
  total: number;
  shown: number;
  flagged: number;
  flag_counts: Partial<Record<FlagName, number>>;
  facets: { outcomes: string[]; models: string[]; languages: string[]; releases: string[]; flags: FlagName[] };
  dataset: string;
  error: string;
}

export type Attrs = Record<string, string | number | boolean | null | string[] | number[]>;

export interface SpanView {
  span_id: string;
  parent_id: string;
  trace_id: string;
  name: string;
  kind: "model" | "read" | "write" | "agent" | "approval" | "check" | "other";
  op: string;
  tool: string;
  depth: number;
  offset_s: number;
  duration_s: number;
  start: number;
  error: boolean;
  error_type: string;
  status: string;
  tokens_in: number | null;
  tokens_out: number | null;
  cost: number | null;
  attempt: number | null;
  retry: boolean;
  links: { trace_id: string; span_id: string }[];
  attrs: Attrs;
}

export interface TraceView {
  trace_id: string;
  number: number;
  start: number;
  duration_s: number;
  root: string;
  links: { grafana?: string; langfuse?: string };
  spans: SpanView[];
}

export interface Wait {
  before_trace: string;
  seconds: number;
  from: number;
  to: number;
  approver: string;
  approver_name: string;
  role: string;
  limit: number | null;
  decision: string;
  wait_s: number | null;
  link: { trace_id: string; span_id: string }[];
}

export interface RunDetail {
  run: RunRow;
  traces: TraceView[];
  waits: Wait[];
  flags: { name: FlagName; why: string; spans: string[] }[];
  price_tables: string[];
  same_ticket: string[];
  root: Attrs;
  service: string;
  dataset: string;
}

export interface Actor {
  kind: "agent" | "person" | "system";
  id: string;
  role?: string;
  model?: string;
  name?: string;
  title?: string;
}

export interface Effect {
  tool: string;
  order_id?: string;
  amount?: number;
  reason_code?: string;
  sku?: string;
  quantity?: number;
  label_reason?: string;
}

export interface AuditRecord {
  seq: number;
  at: string;
  type: "proposal" | "approval" | "refusal" | "write" | "data_access" | "handoff" | "run_closed";
  actor: Actor;
  action: Record<string, any>;
  authority: Record<string, any>;
  evidence: string[];
  subject: Record<string, string>;
  trace_id: string;
  span_id: string;
  hash: string;
  prev: string;
  links_ok: boolean;
  sentence: string;
  refers_to: { proposal: number | null; approval: number | null };
}

export interface AuditAnswer {
  run_id: string;
  ticket: string;
  records: AuditRecord[];
  verify: { ok: boolean; count: number; head: string; problems: string[] };
  customers: string[];
  reads: { tool: string; orders?: string[]; status: string; seq: number }[];
  evidence: string[];
  orders: string[];
  passages: string[];
  changes: { effect: Effect; calls: number; outcomes: string[]; keys: string[] }[];
  writes: number;
  approvals: number;
  trace_ids: string[];
  dataset: string;
  store: string;
}

export interface CostGroup {
  runs: number;
  resolved: number;
  cost: number;
  per_run: number | null;
  per_resolved: number | null;
  success: number | null;
}

export interface CostBucket extends CostGroup {
  start: number;
  end: number;
  models: Record<string, number>;
}

export interface CostAnswer {
  bucket: "day" | "hour";
  series: CostBucket[];
  total: CostGroup;
  groups: Record<"model" | "language" | "outcome" | "release", (CostGroup & { key: string })[]>;
  steps: { model: string; step: number; calls: number; cost: number; tokens_in: number; tokens_out: number }[];
  top: RunRow[];
  budget_per_resolved: number;
  price_tables: { date: string; model_calls: number }[];
  releases: { release: string; first_run: number; run_id: string }[];
  tz_hours: number;
  dataset: string;
  prometheus?: { available: boolean; query: string; error?: string; series?: { labels: Record<string, string>; points: [number, number][] }[] };
}

export interface Step {
  index: number;
  kind: "model" | "tool" | "approval";
  sig: string;
  name: string;
  span_id: string;
  value: Record<string, any>;
  requested?: string[];
  tool?: string;
  tool_kind?: string;
  order?: string;
  attempt?: number;
  key?: string;
  cost?: number;
  tokens_in?: number;
  tokens_out?: number;
  wait_s?: number;
}

export interface CompareAnswer {
  a: RunRow;
  b: RunRow;
  same_ticket: boolean;
  rows: { a: Step | null; b: Step | null; same: boolean }[];
  first_difference: { row: number; kind: "model_decision" | "tool_result" | "approval"; a: Step | null; b: Step | null } | null;
  tickets: Record<string, string[]>;
  dataset: string;
}
