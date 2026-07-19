// -- Run 相关类型，映射后端 API 返回结构 --
export type TaskStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "cancelled"
  | "skipped";

export type RunStatus = "success" | "partial" | "failed" | "cancelled";

export interface Task {
  task_id: string;
  title: string;
  instruction: string;
  dependencies: string[];
  required_capabilities: string[];
  tool_allowlist: string[];
  input_refs: string[];
  output_schema: Record<string, unknown> | null;
  success_criteria: string[];
  timeout_seconds: number | null;
  max_attempts: number;
}

export interface Plan {
  plan_id: string;
  version: number;
  objective: string;
  assumptions: string[];
  global_success_criteria: string[];
  tasks: Task[];
}

export interface TaskResult {
  task_id: string;
  attempt: number;
  status: TaskStatus;
  output: Record<string, unknown> | null;
  artifact_refs: string[];
  error_code: string | null;
  error_message: string | null;
  started_at: string | null;
  ended_at: string | null;
  token_usage: number | null;
  cost: number | null;
  tools_used: string[];
}

export interface AggregateResult {
  candidate_answer: string;
  task_outputs: Record<string, unknown>;
  artifact_refs: string[];
}

export interface ReviewResult {
  passed: boolean;
  score: number | null;
  failed_task_ids: string[];
  issues: string[];
  evidence_refs: string[];
  suggested_action: string | null;
}

export interface FinalAnswer {
  content: string;
  status: RunStatus;
  artifact_refs: string[];
  warnings: string[];
}

export interface RunBudget {
  max_plan_versions: number;
  max_review_cycles: number;
  max_task_attempts: number;
  max_concurrent_tasks: number;
  max_total_seconds: number;
  max_model_calls: number | null;
  max_tokens: number | null;
  max_cost: number | null;
  used_model_calls: number;
  used_tokens: number;
  used_cost: number;
}

// GET /runs/{run_id} 返回的完整快照
export interface RunSnapshot {
  run_id: string;
  user_request: string;
  plan: Plan | null;
  plan_version: number;
  task_events: TaskResult[];
  assignments: Record<string, unknown>;
  current_assignment: unknown | null;
  aggregate: AggregateResult | null;
  review: ReviewResult | null;
  diagnosis: unknown | null;
  budget: RunBudget;
  cycle_count: number;
  final_answer: FinalAnswer | null;
  // 合成字段（API 注入）
  status: string;
  error?: string;
}

// POST /runs 返回
export interface CreateRunResponse {
  run_id: string;
  status: string;
}

// 前端增强：为每个 Task 绑定运行时进度
export interface TaskWithProgress {
  task: Task;
  result: TaskResult | null;
  progress: TaskProgress;
}

export type TaskProgress =
  | { stage: "pending" }
  | { stage: "running"; started_at?: string }
  | { stage: "completed" }
  | { stage: "failed"; error?: string }
  | { stage: "skipped" };

// 运行列表项（左侧侧边栏）
export interface RunListItem {
  run_id: string;
  user_request: string;
  status: string;
  created_at: string;
}

// 工作流阶段
export type WorkflowPhase =
  | "queued"
  | "planning"
  | "executing"
  | "aggregating"
  | "reviewing"
  | "finalizing"
  | "done"
  | "failed";
