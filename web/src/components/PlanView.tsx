import { useState } from "react";
import {
  ChevronDown,
  ChevronRight,
  Target,
  GripVertical,
  CheckCircle2,
  Clock,
  Loader2,
  XCircle,
  SkipForward,
  GitBranch,
  Wrench,
} from "lucide-react";
import type { Plan, TaskWithProgress } from "../types";
import MarkdownRenderer from "./MarkdownRenderer";

interface PlanViewProps {
  plan: Plan;
  tasks: TaskWithProgress[];
}

export function PlanView({ plan, tasks }: PlanViewProps) {
  const [expanded, setExpanded] = useState(true);

  const progress = tasks.length > 0
    ? Math.round(
        (tasks.filter((t) => t.progress.stage === "completed").length /
          tasks.length) *
          100,
      )
    : 0;

  return (
    <div className="bg-surface-raised rounded-2xl border border-surface-border overflow-hidden animate-slide-up">
      {/* Plan 头部 */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 px-5 py-4 hover:bg-surface-overlay/50 transition-colors text-left"
      >
        <div className="w-8 h-8 rounded-xl bg-violet-500/15 flex items-center justify-center shrink-0">
          <Target className="w-4 h-4 text-violet-400" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold truncate">执行计划</h3>
          <p className="text-xs text-muted mt-0.5 truncate">{plan.objective}</p>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          {/* 简易进度环 */}
          <div className="relative w-8 h-8">
            <svg className="w-8 h-8 -rotate-90" viewBox="0 0 32 32">
              <circle
                cx="16" cy="16" r="13"
                fill="none"
                stroke="currentColor"
                strokeWidth="3"
                className="text-surface-border"
              />
              <circle
                cx="16" cy="16" r="13"
                fill="none"
                stroke="currentColor"
                strokeWidth="3"
                strokeLinecap="round"
                className="text-emerald-400 transition-all duration-700"
                strokeDasharray={`${(progress / 100) * 81.68} 81.68`}
              />
            </svg>
            <span className="absolute inset-0 flex items-center justify-center text-[9px] font-mono font-bold text-emerald-400">
              {progress}
            </span>
          </div>
          {expanded ? (
            <ChevronDown className="w-4 h-4 text-muted" />
          ) : (
            <ChevronRight className="w-4 h-4 text-muted" />
          )}
        </div>
      </button>

      {expanded && (
        <div className="border-t border-surface-border px-5 py-4 space-y-4">
          {/* 目标与假设 */}
          <div>
            <MarkdownRenderer content={plan.objective} compact />
            {plan.assumptions.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {plan.assumptions.map((a, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-surface-overlay text-[10px] text-muted/80"
                  >
                    <span className="text-accent text-[10px]">※</span>
                    {a}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* 全局成功标准 */}
          {plan.global_success_criteria.length > 0 && (
            <div className="space-y-1">
              <p className="text-[11px] font-medium text-muted/60 uppercase tracking-wider">
                验收标准
              </p>
              {plan.global_success_criteria.map((c, i) => (
                <div key={i} className="flex items-start gap-2 text-xs text-muted/80">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500/60 shrink-0 mt-0.5" />
                  <span>{c}</span>
                </div>
              ))}
            </div>
          )}

          {/* 任务 DAG 视图 */}
          <div>
            <p className="text-[11px] font-medium text-muted/60 uppercase tracking-wider mb-2">
              子任务 ({tasks.length})
            </p>
            <div className="space-y-2">
              {tasks.map((t) => (
                <TaskCard key={t.task.task_id} item={t} allTasks={tasks} />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ---- 单任务卡片 ---- */
function TaskCard({
  item,
  allTasks,
}: {
  item: TaskWithProgress;
  allTasks: TaskWithProgress[];
}) {
  const [expanded, setExpanded] = useState(false);
  const { task, result, progress } = item;

  const statusConfig: Record<string, { icon: React.ReactNode; label: string; bg: string; border: string }> = {
    pending: {
      icon: <Clock className="w-3.5 h-3.5" />,
      label: "等待中",
      bg: "bg-surface",
      border: "border-surface-border",
    },
    running: {
      icon: <Loader2 className="w-3.5 h-3.5 animate-spin" />,
      label: "执行中",
      bg: "bg-blue-500/5",
      border: "border-blue-500/20",
    },
    completed: {
      icon: <CheckCircle2 className="w-3.5 h-3.5" />,
      label: "已完成",
      bg: "bg-emerald-500/5",
      border: "border-emerald-500/20",
    },
    failed: {
      icon: <XCircle className="w-3.5 h-3.5" />,
      label: "失败",
      bg: "bg-red-500/5",
      border: "border-red-500/20",
    },
    skipped: {
      icon: <SkipForward className="w-3.5 h-3.5" />,
      label: "已跳过",
      bg: "bg-surface-overlay",
      border: "border-surface-border",
    },
  };

  const cfg = statusConfig[progress.stage] ?? statusConfig.pending;

  // 依赖的任务
  const deps = task.dependencies
    .map((did) => allTasks.find((t) => t.task.task_id === did))
    .filter(Boolean) as TaskWithProgress[];

  return (
    <div
      className={`rounded-xl border transition-all duration-300 ${cfg.bg} ${cfg.border}`}
    >
      {/* 主行 */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 px-4 py-3 text-left"
      >
        {/* 状态图标 */}
        <div
          className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${
            progress.stage === "completed"
              ? "text-emerald-400 bg-emerald-500/10"
              : progress.stage === "failed"
                ? "text-red-400 bg-red-500/10"
                : progress.stage === "running"
                  ? "text-blue-400 bg-blue-500/10"
                  : "text-muted/60 bg-surface-overlay"
          }`}
        >
          {cfg.icon}
        </div>

        {/* 标题 */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <GripVertical className="w-3 h-3 text-muted/40 shrink-0" />
            <p className="text-sm font-medium truncate">{task.title}</p>
          </div>
          {/* 依赖连线 */}
          {deps.length > 0 && (
            <div className="flex items-center gap-1 mt-1 flex-wrap">
              <GitBranch className="w-3 h-3 text-muted/50 shrink-0" />
              {deps.map((d) => {
                const depCfg = statusConfig[d.progress.stage] ?? statusConfig.pending;
                return (
                  <span
                    key={d.task.task_id}
                    className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] bg-surface-overlay text-muted/60"
                  >
                    {depCfg.icon}
                    <span className="truncate max-w-[80px]">{d.task.title}</span>
                  </span>
                );
              })}
            </div>
          )}
        </div>

        {/* 右侧信息 */}
        <div className="flex items-center gap-3 shrink-0">
          {result?.token_usage && (
            <span className="text-[10px] text-muted/50 font-mono">
              {result.token_usage.toLocaleString()} tok
            </span>
          )}
          <span className={`text-[11px] font-medium ${
            progress.stage === "completed" ? "text-emerald-400" :
            progress.stage === "failed" ? "text-red-400" :
            progress.stage === "running" ? "text-blue-400" :
            "text-muted/60"
          }`}>
            {cfg.label}
          </span>
          {expanded ? (
            <ChevronDown className="w-3.5 h-3.5 text-muted/50" />
          ) : (
            <ChevronRight className="w-3.5 h-3.5 text-muted/50" />
          )}
        </div>
      </button>

      {/* 展开详情 */}
      {expanded && (
        <div className="border-t border-surface-border px-4 py-3 space-y-3 animate-fade-in">
          {/* 执行指令 */}
          <div>
            <p className="text-[10px] text-muted/60 uppercase tracking-wider mb-1">执行指令</p>
            <MarkdownRenderer content={task.instruction} compact />
          </div>

          {/* 参数 */}
          <div className="grid grid-cols-2 gap-2 text-[10px]">
            {task.required_capabilities.length > 0 && (
              <div className="flex items-center gap-1.5 text-muted/60">
                <Wrench className="w-3 h-3" />
                <span>需要能力：{task.required_capabilities.join("、")}</span>
              </div>
            )}
            {task.timeout_seconds && (
              <div className="flex items-center gap-1.5 text-muted/60">
                <Clock className="w-3 h-3" />
                <span>超时：{task.timeout_seconds}s</span>
              </div>
            )}
            <div className="flex items-center gap-1.5 text-muted/60">
              <span>最大重试：{task.max_attempts} 次</span>
            </div>
          </div>

          {/* 成功标准 */}
          {task.success_criteria.length > 0 && (
            <div className="space-y-1">
              <p className="text-[10px] text-muted/60 uppercase tracking-wider">成功标准</p>
              {task.success_criteria.map((c, i) => (
                <div key={i} className="flex items-start gap-1.5 text-[11px] text-muted/70">
                  <CheckCircle2 className="w-3 h-3 text-emerald-500/50 shrink-0 mt-0.5" />
                  <span>{c}</span>
                </div>
              ))}
            </div>
          )}

          {/* 执行输出 */}
          {result?.output && (
            <div>
              <p className="text-[10px] text-muted/60 uppercase tracking-wider mb-1">执行输出</p>
              <pre className="bg-surface rounded-lg p-3 text-[11px] text-muted/80 font-mono overflow-x-auto max-h-40 overflow-y-auto leading-relaxed">
                {JSON.stringify(result.output, null, 2)}
              </pre>
            </div>
          )}

          {/* 错误信息 */}
          {progress.stage === "failed" && "error" in progress && progress.error && (
            <div className="flex items-start gap-2 p-2.5 rounded-lg bg-red-500/10 border border-red-500/15">
              <XCircle className="w-3.5 h-3.5 text-red-400 shrink-0 mt-0.5" />
              <p className="text-[11px] text-red-400/90 font-mono">{progress.error}</p>
            </div>
          )}

          {/* 使用的工具 */}
          {result?.tools_used && result.tools_used.length > 0 && (
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-[10px] text-muted/60">使用工具：</span>
              {result.tools_used.map((t, i) => (
                <span key={i} className="px-1.5 py-0.5 rounded bg-surface-overlay text-[10px] font-mono text-muted/70">
                  {t}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
