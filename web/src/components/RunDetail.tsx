import { useMemo } from "react";
import {
  Lightbulb,
  ListChecks,
  Merge,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  ChevronDown,
  ChevronRight,
  MessageSquareText,
  Gauge,
  Zap,
} from "lucide-react";
import type { RunSnapshot, TaskWithProgress, TaskProgress, WorkflowPhase } from "../types";
import { PlanView } from "./PlanView";
import { AggregateCard } from "./AggregateCard";
import { ReviewCard } from "./ReviewCard";
import { FinalAnswer } from "./FinalAnswer";
import { StatusBadge } from "./Dashboard";

interface RunDetailProps {
  run: RunSnapshot;
}

/** 根据快照推断工作流阶段 */
function inferPhase(run: RunSnapshot): WorkflowPhase {
  if (run.final_answer) return "done";
  if (run.status === "failed" || run.error) return "failed";
  if (run.review) return "reviewing";
  if (run.aggregate) return "aggregating";
  if (run.plan && run.task_events.length > 0) return "executing";
  if (run.plan) return "planning";
  return "queued";
}

/** 将 plan.tasks 与 task_events 合并为 TaskWithProgress[] */
function mergeTasks(run: RunSnapshot): TaskWithProgress[] {
  if (!run.plan) return [];
  const eventMap = new Map(run.task_events.map((e) => [e.task_id, e]));
  return run.plan.tasks.map((task) => {
    const result = eventMap.get(task.task_id) ?? null;
    let progress: TaskProgress;
    if (!result) {
      progress = { stage: "pending" };
    } else if (result.status === "completed") {
      progress = { stage: "completed" };
    } else if (result.status === "failed") {
      progress = { stage: "failed", error: result.error_message ?? undefined };
    } else if (result.status === "running") {
      progress = { stage: "running", started_at: result.started_at ?? undefined };
    } else if (result.status === "skipped") {
      progress = { stage: "skipped" };
    } else {
      progress = { stage: "pending" };
    }
    return { task, result, progress };
  });
}

const PHASE_STEPS: { phase: WorkflowPhase; label: string; icon: React.FC<{ className?: string }> }[] = [
  { phase: "queued", label: "排队", icon: Clock },
  { phase: "planning", label: "规划", icon: Lightbulb },
  { phase: "executing", label: "执行", icon: ListChecks },
  { phase: "aggregating", label: "汇总", icon: Merge },
  { phase: "reviewing", label: "审核", icon: CheckCircle2 },
  { phase: "finalizing", label: "完成", icon: MessageSquareText },
];

export function RunDetail({ run }: RunDetailProps) {
  const phase = useMemo(() => inferPhase(run), [run]);
  const tasks = useMemo(() => mergeTasks(run), [run]);

  const isFinished = ["done", "failed"].includes(phase);
  const isFailed = phase === "failed";

  return (
    <div className="max-w-4xl mx-auto px-6 py-6 space-y-6 animate-fade-in">
      {/* 工作流进度条 */}
      <WorkflowProgress phase={phase} isFailed={isFailed} />

      {/* 错误提示 */}
      {run.error && (
        <div className="flex items-start gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/20">
          <XCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-red-300">运行错误</p>
            <p className="text-xs text-red-400/80 mt-1 font-mono">{run.error}</p>
          </div>
        </div>
      )}

      {/* 预算信息 */}
      {run.plan && <BudgetBar run={run} />}

      {/* 计划 + 任务 DAG */}
      {run.plan && (
        <PlanView plan={run.plan} tasks={tasks} />
      )}

      {/* 汇总结果 */}
      {run.aggregate && <AggregateCard aggregate={run.aggregate} />}

      {/* 审核结果 */}
      {run.review && <ReviewCard review={run.review} />}

      {/* 最终答案 */}
      {run.final_answer && <FinalAnswer answer={run.final_answer} />}

      {/* 运行中无计划时的等待 */}
      {!run.plan && !isFinished && (
        <div className="flex flex-col items-center justify-center py-16 text-muted">
          <div className="w-10 h-10 rounded-full border-2 border-accent/30 border-t-accent animate-spin mb-4" />
          <p className="text-sm">Agent 正在分析你的请求...</p>
          <p className="text-xs mt-1 text-muted/60">预计几秒内生成执行计划</p>
        </div>
      )}
    </div>
  );
}

/* ---- 工作流进度条 ---- */
function WorkflowProgress({
  phase,
  isFailed,
}: {
  phase: WorkflowPhase;
  isFailed: boolean;
}) {
  const currentIdx = PHASE_STEPS.findIndex((s) => s.phase === phase);

  return (
    <div className="bg-surface-raised rounded-2xl border border-surface-border p-4">
      <div className="flex items-center justify-between">
        {PHASE_STEPS.map((step, i) => {
          const Icon = step.icon;
          const isActive = i === currentIdx && !isFailed;
          const isDone = i < currentIdx || (i === currentIdx && phase === "done");
          const isError = isFailed && i === currentIdx;
          return (
            <div key={step.phase} className="flex items-center flex-1 last:flex-none">
              <div className="flex flex-col items-center gap-1.5">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300 ${
                    isError
                      ? "bg-red-500/20 text-red-400 ring-1 ring-red-500/30"
                      : isDone
                        ? "bg-emerald-500/15 text-emerald-400"
                        : isActive
                          ? "bg-accent/20 text-accent ring-1 ring-accent/30"
                          : "bg-surface-overlay text-muted/50"
                  }`}
                >
                  {isError ? (
                    <XCircle className="w-4 h-4" />
                  ) : isActive ? (
                    <div className="w-3.5 h-3.5 rounded-full border-2 border-accent border-t-transparent animate-spin" />
                  ) : (
                    <Icon className="w-4 h-4" />
                  )}
                </div>
                <span
                  className={`text-[10px] font-medium transition-colors duration-300 ${
                    isActive ? "text-accent" : isDone ? "text-emerald-400/80" : isError ? "text-red-400" : "text-muted/50"
                  }`}
                >
                  {step.label}
                </span>
              </div>
              {i < PHASE_STEPS.length - 1 && (
                <div className="flex-1 h-0.5 mx-1 -mt-5">
                  <div className="h-full rounded-full bg-surface-overlay overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-700 ${
                        i < currentIdx || (isDone && i < currentIdx)
                          ? "bg-emerald-500/50"
                          : i === currentIdx && isActive
                            ? "bg-accent/30"
                            : ""
                      }`}
                      style={{
                        width:
                          i < currentIdx
                            ? "100%"
                            : i === currentIdx && !isFailed && phase !== "done"
                              ? "40%"
                              : "0%",
                      }}
                    />
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ---- 资源预算条 ---- */
function BudgetBar({ run }: { run: RunSnapshot }) {
  const b = run.budget;
  const totalTasks = run.plan?.tasks.length ?? 0;
  const completedTasks = run.task_events.filter(
    (e) => e.status === "completed",
  ).length;
  const failedTasks = run.task_events.filter(
    (e) => e.status === "failed",
  ).length;
  const runningTasks = run.task_events.filter(
    (e) => e.status === "running",
  ).length;

  return (
    <div className="bg-surface-raised rounded-2xl border border-surface-border p-4">
      <div className="flex items-center gap-2 mb-3">
        <Gauge className="w-4 h-4 text-muted" />
        <span className="text-xs font-medium text-muted">运行资源监控</span>
      </div>
      <div className="grid grid-cols-4 gap-3 text-xs">
        <MetricItem
          label="计划版本"
          value={`v${run.plan_version} / ${b.max_plan_versions}`}
          color="text-violet-400"
        />
        <MetricItem
          label="循环次数"
          value={`${run.cycle_count} / ${b.max_review_cycles}`}
          color="text-orange-400"
        />
        <MetricItem
          label="Token 消耗"
          value={`${b.used_tokens.toLocaleString()}${b.max_tokens ? ` / ${b.max_tokens.toLocaleString()}` : ""}`}
          color="text-cyan-400"
        />
        <MetricItem
          label="任务进度"
          value={`${completedTasks}/${totalTasks}`}
          sub={`${runningTasks} 运行中${failedTasks > 0 ? ` · ${failedTasks} 失败` : ""}`}
          color="text-emerald-400"
        />
      </div>
    </div>
  );
}

function MetricItem({
  label,
  value,
  sub,
  color,
}: {
  label: string;
  value: string;
  sub?: string;
  color: string;
}) {
  return (
    <div className="bg-surface px-3 py-2.5 rounded-xl">
      <p className="text-[10px] text-muted/60 mb-0.5">{label}</p>
      <p className={`font-mono font-medium text-sm ${color}`}>{value}</p>
      {sub && <p className="text-[10px] text-muted/50 mt-0.5">{sub}</p>}
    </div>
  );
}
