// Auto-generated TypeScript types from Pydantic models
// DO NOT EDIT - Run 'python scripts/generate-types.py' to regenerate

export type TaskType = "test" | "fix" | "refactor" | "feature" | "doc" | "chore" | "design" | "investigate";

export type TaskStatus = "TODO" | "IN_PROGRESS" | "DONE" | "BLOCKED" | "SKIPPED" | "OUT_OF_SCOPE" | "CANCELLED" | "FAILED" | "WAITING";

export interface Task {
  id: number;
  title: string;
  type: TaskType;
  status: TaskStatus;
  depends_on: number[];
  commit_sha: string | null;
  last_updated_at: string | null;
}

export type SignalLevel = "blocker" | "high" | "info";

export type SignalType = "ci" | "lint" | "bench" | "system" | "other";

export interface Signal {
  id: string;
  type: SignalType;
  kind: string;
  level: SignalLevel;
  open: boolean;
  title: string;
  message: string;
  link: string | null;
  extra: Record<string, any>;
  attempts: number;
}

export type NowReason = "ci_blocker" | "task" | "completed" | "idle" | "waiting_on_lock" | "deadlocked" | "escalated";

export interface Now {
  reason: NowReason;
  task_id: number | null;
  signal_id: string | null;
}

export interface SessionState {
  session: string;
  description: string;
  tasks: Task[];
  signals: Signal[];
  now: Now;
  lock_holder: string | null;
  created_at: string;
  last_updated_at: string;
}

export interface SessionSummary {
  id: string;
  description: string;
  task_count: number;
  signal_count: number;
}
