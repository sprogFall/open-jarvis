import { useMemo } from "react";
import { CheckCircle2, Clock3, Cpu, Layers3, ListChecks, Loader2, Merge, MessageSquareText, RotateCcw, Settings2, ShieldCheck, XCircle } from "lucide-react";
import type { RunSnapshot, TaskProgress, TaskWithProgress, WorkflowPhase } from "../types";
import { AggregateCard } from "./AggregateCard";
import { FinalAnswer } from "./FinalAnswer";
import { PlanView } from "./PlanView";
import { ReviewCard } from "./ReviewCard";

interface RunDetailProps { run: RunSnapshot; }

function inferPhase(run: RunSnapshot): WorkflowPhase {
  if (run.status === "failed" || run.error) return "failed";
  if (run.final_answer || ["success", "partial", "done", "cancelled"].includes(run.status)) return "done";
  if (run.review) return "reviewing";
  if (run.aggregate) return "aggregating";
  if (run.plan && run.task_events.length > 0) return "executing";
  if (run.plan) return "planning";
  return "queued";
}

function mergeTasks(run: RunSnapshot): TaskWithProgress[] {
  if (!run.plan) return [];
  const latest = new Map<string, (typeof run.task_events)[number]>();
  run.task_events.forEach((event) => latest.set(event.task_id, event));
  return run.plan.tasks.map((task) => {
    const result = latest.get(task.task_id) ?? null;
    let progress: TaskProgress = { stage: "pending" };
    if (result?.status === "completed") progress = { stage: "completed" };
    else if (result?.status === "failed") progress = { stage: "failed", error: result.error_message ?? undefined };
    else if (result?.status === "running") progress = { stage: "running", started_at: result.started_at ?? undefined };
    else if (result?.status === "skipped" || result?.status === "cancelled") progress = { stage: "skipped" };
    return { task, result, progress };
  });
}

const PHASE_STEPS = [
  { phase: "queued", label: "排队", icon: Clock3 },
  { phase: "planning", label: "规划", icon: Layers3 },
  { phase: "executing", label: "执行", icon: ListChecks },
  { phase: "aggregating", label: "汇总", icon: Merge },
  { phase: "reviewing", label: "审核", icon: ShieldCheck },
  { phase: "done", label: "完成", icon: MessageSquareText },
] as const;

export function RunDetail({ run }: RunDetailProps) {
  const phase = useMemo(() => inferPhase(run), [run]);
  const tasks = useMemo(() => mergeTasks(run), [run]);
  return (
    <div className="mx-auto max-w-5xl space-y-5 px-4 py-5 sm:px-6 sm:py-6">
      <WorkflowProgress phase={phase} />
      <ResourceMonitor run={run} tasks={tasks} />
      {run.error && <div className="flex items-start gap-3 rounded-xl border border-red-500/30 bg-red-500/10 p-4" role="alert"><XCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-300" /><div><p className="text-sm font-medium text-red-200">运行发生错误</p><p className="mt-1 break-words font-mono text-xs leading-5 text-red-200/80">{run.error}</p></div></div>}
      {run.plan && <PlanView plan={run.plan} tasks={tasks} />}
      {run.aggregate && <AggregateCard aggregate={run.aggregate} />}
      {run.review && <ReviewCard review={run.review} />}
      {run.final_answer && <FinalAnswer answer={run.final_answer} />}
      {!run.plan && phase !== "failed" && phase !== "done" && <WaitingState />}
    </div>
  );
}

function WorkflowProgress({ phase }: { phase: WorkflowPhase }) {
  const currentIndex = Math.max(0, PHASE_STEPS.findIndex((step) => step.phase === phase));
  const failed = phase === "failed";
  return (
    <section aria-label="工作流进度" className="rounded-2xl border border-surface-border bg-surface-raised p-4 sm:p-5">
      <div className="mb-4 flex items-center justify-between"><div><p className="text-sm font-semibold">运行进度</p><p className="mt-0.5 text-xs text-muted">每个阶段会在快照更新时自动刷新</p></div><span className={`rounded-full px-2.5 py-1 text-[11px] font-medium ${failed ? "bg-red-500/15 text-red-300" : phase === "done" ? "bg-emerald-500/15 text-emerald-300" : "bg-accent/15 text-accent-hover"}`}>{failed ? "已中断" : phase === "done" ? "已完成" : "处理中"}</span></div>
      <ol className="grid grid-cols-3 gap-x-2 gap-y-4 sm:grid-cols-6">
        {PHASE_STEPS.map((step, index) => {
          const Icon = step.icon;
          const isComplete = !failed && (index < currentIndex || phase === "done");
          const isCurrent = !failed && index === currentIndex && phase !== "done";
          const isFailed = failed && index === currentIndex;
          return <li key={step.phase} className="relative flex min-w-0 items-center gap-2 sm:block sm:text-center">
            {index > 0 && <span className={`absolute -left-1/2 top-4 hidden h-px w-full sm:block ${isComplete ? "bg-emerald-500/70" : "bg-surface-border"}`} aria-hidden="true" />}
            <span className={`relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${isFailed ? "bg-red-500/20 text-red-300" : isComplete ? "bg-emerald-500/20 text-emerald-300" : isCurrent ? "bg-accent/20 text-accent ring-1 ring-accent/50" : "bg-surface-overlay text-muted/60"}`}>{isCurrent ? <Loader2 className="h-4 w-4 animate-spin" /> : isFailed ? <XCircle className="h-4 w-4" /> : isComplete ? <CheckCircle2 className="h-4 w-4" /> : <Icon className="h-4 w-4" />}</span>
            <span className={`relative z-10 text-[11px] font-medium ${isFailed ? "text-red-300" : isComplete ? "text-emerald-300" : isCurrent ? "text-accent-hover" : "text-muted/70"}`}>{step.label}</span>
          </li>;
        })}
      </ol>
    </section>
  );
}

function ResourceMonitor({ run, tasks }: { run: RunSnapshot; tasks: TaskWithProgress[] }) {
  const budget = run.budget;
  const counts = tasks.reduce((acc, item) => { acc[item.progress.stage] += 1; return acc; }, { pending: 0, running: 0, completed: 0, failed: 0, skipped: 0 });
  const total = tasks.length;
  const settled = counts.completed + counts.failed + counts.skipped;
  const taskPercent = total ? Math.round((settled / total) * 100) : 0;
  const planPercent = ratio(run.plan_version, budget.max_plan_versions);
  const cyclePercent = ratio(run.cycle_count, budget.max_review_cycles);
  const tokenPercent = ratio(budget.used_tokens, budget.max_tokens);
  const callPercent = ratio(budget.used_model_calls, budget.max_model_calls);
  return (
    <section aria-labelledby="resource-title" className="overflow-hidden rounded-2xl border border-surface-border bg-surface-raised">
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-surface-border px-4 py-4 sm:px-5"><div className="flex items-center gap-3"><div className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent/15"><Settings2 className="h-4 w-4 text-accent-hover" /></div><div><h3 id="resource-title" className="text-sm font-semibold">运行资源监控</h3><p className="mt-0.5 text-xs text-muted">任务进度、重规划与模型用量</p></div></div><span className="font-mono text-[11px] text-muted/70">{run.run_id}</span></div>
      <div className="grid grid-cols-2 gap-px bg-surface-border md:grid-cols-4">
        <Metric title="任务进度" value={total ? `${settled} / ${total}` : "等待计划"} caption={total ? `${counts.running} 运行中 · ${counts.pending} 待执行${counts.failed ? ` · ${counts.failed} 失败` : ""}` : "规划生成后显示"} percent={taskPercent} tone="emerald" icon={ListChecks} />
        <Metric title="计划版本" value={`v${run.plan_version} / ${budget.max_plan_versions}`} caption="超过上限将停止重规划" percent={planPercent} tone="violet" icon={Layers3} />
        <Metric title="审核循环" value={`${run.cycle_count} / ${budget.max_review_cycles}`} caption="审核不通过时触发循环" percent={cyclePercent} tone="orange" icon={RotateCcw} />
        <Metric title="Token 用量" value={`${formatNumber(budget.used_tokens)}${budget.max_tokens ? ` / ${formatNumber(budget.max_tokens)}` : ""}`} caption={`${budget.used_model_calls}${budget.max_model_calls ? ` / ${budget.max_model_calls}` : ""} 次模型调用`} percent={Math.max(tokenPercent, callPercent)} tone="cyan" icon={Cpu} />
      </div>
      <dl className="grid grid-cols-2 gap-x-4 gap-y-2 px-4 py-3 text-xs text-muted sm:grid-cols-4 sm:px-5"><div><dt>并发上限</dt><dd className="mt-1 font-mono text-muted-foreground">{budget.max_concurrent_tasks} 个任务</dd></div><div><dt>单任务重试</dt><dd className="mt-1 font-mono text-muted-foreground">最多 {budget.max_task_attempts} 次</dd></div><div><dt>时间上限</dt><dd className="mt-1 font-mono text-muted-foreground">{Math.round(budget.max_total_seconds / 60)} 分钟</dd></div><div><dt>预估成本</dt><dd className="mt-1 font-mono text-muted-foreground">{budget.used_cost ? `$${budget.used_cost.toFixed(4)}` : "—"}</dd></div></dl>
    </section>
  );
}

function Metric({ title, value, caption, percent, tone, icon: Icon }: { title: string; value: string; caption: string; percent: number; tone: "emerald" | "violet" | "orange" | "cyan"; icon: typeof ListChecks }) {
  const styles = { emerald: "bg-emerald-400 text-emerald-300", violet: "bg-violet-400 text-violet-300", orange: "bg-orange-400 text-orange-300", cyan: "bg-cyan-400 text-cyan-300" }[tone];
  const [bar, text] = styles.split(" ");
  return <div className="min-w-0 bg-surface p-4"><div className="flex items-center gap-2 text-muted"><Icon className={`h-3.5 w-3.5 ${text}`} /><p className="text-[11px] font-medium">{title}</p></div><p className={`mt-3 truncate font-mono text-base font-semibold ${text}`}>{value}</p><p className="mt-1 min-h-4 truncate text-[10px] text-muted/70">{caption}</p><div className="mt-3 h-1 overflow-hidden rounded-full bg-surface-overlay"><div className={`h-full rounded-full transition-[width] duration-500 ${bar}`} style={{ width: `${Math.min(100, percent)}%` }} /></div></div>;
}

function WaitingState() { return <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-surface-border py-12 text-center"><div className="flex h-10 w-10 items-center justify-center rounded-full bg-accent/15"><Loader2 className="h-5 w-5 animate-spin text-accent" /></div><p className="mt-4 text-sm font-medium">正在生成执行计划</p><p className="mt-1 text-xs text-muted">计划、任务和资源统计将在首个快照到达后显示。</p></div>; }
function ratio(used: number, limit: number | null | undefined): number { return limit && limit > 0 ? Math.round((used / limit) * 100) : 0; }
function formatNumber(value: number): string { return new Intl.NumberFormat("zh-CN", { notation: "compact", maximumFractionDigits: 1 }).format(value); }
