import type { RunListItem } from "../types";
import { Bot, Plus, SquareChevronRight } from "lucide-react";

interface SidebarProps {
  runs: RunListItem[];
  activeRunId: string | null;
  onSelectRun: (runId: string) => void;
  onNewSession: () => void;
}

const STATUS_BADGE: Record<string, { label: string; color: string }> = {
  queued: { label: "排队中", color: "bg-slate-400" },
  running: { label: "运行中", color: "bg-sky-400" },
  planning: { label: "规划中", color: "bg-violet-400" },
  executing: { label: "执行中", color: "bg-cyan-400" },
  aggregating: { label: "汇总中", color: "bg-amber-400" },
  reviewing: { label: "审核中", color: "bg-orange-400" },
  finalizing: { label: "生成结果", color: "bg-emerald-400" },
  done: { label: "已完成", color: "bg-emerald-500" },
  success: { label: "已完成", color: "bg-emerald-500" },
  partial: { label: "部分完成", color: "bg-yellow-400" },
  failed: { label: "失败", color: "bg-red-400" },
  cancelled: { label: "已取消", color: "bg-slate-400" },
};

export default function Sidebar({ runs, activeRunId, onSelectRun, onNewSession }: SidebarProps) {
  return (
    <aside className="hidden h-full w-72 shrink-0 flex-col border-r border-surface-border bg-surface lg:flex">
      <div className="flex h-16 items-center gap-2.5 border-b border-surface-border px-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/20">
          <Bot className="h-5 w-5 text-accent" aria-hidden="true" />
        </div>
        <div className="min-w-0 flex-1">
          <h1 className="text-sm font-semibold tracking-tight">Open Jarvis</h1>
          <p className="text-[10px] text-muted">Agent Workbench</p>
        </div>
      </div>

      <div className="px-3 pt-3">
        <button
          type="button"
          onClick={onNewSession}
          className="flex min-h-11 w-full items-center justify-center gap-2 rounded-xl bg-accent px-3 text-sm font-medium text-white shadow-sm transition-colors hover:bg-accent-hover focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
        >
          <Plus className="h-4 w-4" aria-hidden="true" />
          新建会话
        </button>
      </div>

      <nav aria-label="运行历史" className="flex-1 overflow-y-auto px-2 py-4">
        <p className="mb-2 px-3 text-[11px] font-medium uppercase tracking-wider text-muted">运行历史</p>
        {runs.length === 0 ? (
          <p className="px-3 py-5 text-center text-xs leading-5 text-muted">尚无运行记录。创建会话后，执行过程会显示在这里。</p>
        ) : (
          <ul className="space-y-1">
            {runs.map((run) => {
              const badge = STATUS_BADGE[run.status] ?? { label: run.status, color: "bg-slate-400" };
              const isActive = run.run_id === activeRunId;
              return (
                <li key={run.run_id}>
                  <button
                    type="button"
                    onClick={() => onSelectRun(run.run_id)}
                    aria-current={isActive ? "page" : undefined}
                    className={`group w-full rounded-xl px-3 py-3 text-left text-xs transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent ${
                      isActive ? "bg-accent/15 ring-1 ring-accent/30" : "hover:bg-surface-raised"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="flex-1 truncate font-medium">{run.user_request}</span>
                      <SquareChevronRight className={`h-3.5 w-3.5 shrink-0 text-accent transition-opacity ${isActive ? "opacity-100" : "opacity-0 group-hover:opacity-70"}`} aria-hidden="true" />
                    </div>
                    <div className="mt-1.5 flex items-center gap-1.5">
                      <span className={`inline-block h-1.5 w-1.5 rounded-full ${badge.color}`} aria-hidden="true" />
                      <span className="text-[11px] text-muted">{badge.label}</span>
                      <time className="ml-auto text-[11px] text-muted/60" dateTime={run.created_at}>{formatTime(run.created_at)}</time>
                    </div>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </nav>

      <div className="border-t border-surface-border px-4 py-3 text-center text-[10px] text-muted/60">Open Jarvis · Agent operations</div>
    </aside>
  );
}

function formatTime(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  const minutes = Math.floor((Date.now() - date.getTime()) / 60_000);
  if (minutes < 1) return "刚刚";
  if (minutes < 60) return `${minutes} 分钟前`;
  if (minutes < 24 * 60) return `${Math.floor(minutes / 60)} 小时前`;
  if (minutes < 7 * 24 * 60) return `${Math.floor(minutes / (24 * 60))} 天前`;
  return date.toLocaleDateString("zh-CN", { month: "numeric", day: "numeric" });
}
