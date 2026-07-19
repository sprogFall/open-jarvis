import type { RunListItem } from "../types";
import { Bot, SquareChevronRight } from "lucide-react";

interface SidebarProps {
  runs: RunListItem[];
  activeRunId: string | null;
  onSelectRun: (runId: string) => void;
}

const STATUS_BADGE: Record<string, { label: string; color: string }> = {
  queued: { label: "排队中", color: "bg-slate-500" },
  running: { label: "运行中", color: "bg-blue-500" },
  planning: { label: "规划中", color: "bg-violet-500" },
  executing: { label: "执行中", color: "bg-cyan-500" },
  aggregating: { label: "汇总中", color: "bg-amber-500" },
  reviewing: { label: "审核中", color: "bg-orange-500" },
  finalizing: { label: "收尾中", color: "bg-emerald-500" },
  done: { label: "已完成", color: "bg-emerald-600" },
  success: { label: "已完成", color: "bg-emerald-600" },
  partial: { label: "部分完成", color: "bg-yellow-600" },
  failed: { label: "失败", color: "bg-red-500" },
  cancelled: { label: "已取消", color: "bg-slate-500" },
  not_found: { label: "未找到", color: "bg-slate-500" },
};

export default function Sidebar({ runs, activeRunId, onSelectRun }: SidebarProps) {
  return (
    <aside className="w-72 h-full bg-surface flex flex-col border-r border-surface-border shrink-0 select-none">
      {/* Header */}
      <div className="flex items-center gap-2.5 px-4 h-14 border-b border-surface-border shrink-0">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-accent/20">
          <Bot className="w-5 h-5 text-accent" />
        </div>
        <div>
          <h1 className="text-sm font-semibold tracking-tight">Open Jarvis</h1>
          <p className="text-[10px] text-muted">Agent Workbench</p>
        </div>
      </div>

      {/* Run List */}
      <div className="flex-1 overflow-y-auto py-2 px-2">
        <p className="px-3 mb-2 text-[11px] font-medium uppercase tracking-wider text-muted">
          运行历史
        </p>
        {runs.length === 0 ? (
          <p className="px-3 py-4 text-xs text-muted text-center">
            暂无运行记录，输入请求开始
          </p>
        ) : (
          <ul className="space-y-1">
            {runs.map((run) => {
              const badge = STATUS_BADGE[run.status] ?? {
                label: run.status,
                color: "bg-slate-500",
              };
              const isActive = run.run_id === activeRunId;
              return (
                <li key={run.run_id}>
                  <button
                    onClick={() => onSelectRun(run.run_id)}
                    className={`w-full text-left px-3 py-2.5 rounded-lg text-xs transition-all duration-150 group ${
                      isActive
                        ? "bg-accent/15 ring-1 ring-accent/30"
                        : "hover:bg-surface-raised"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="truncate font-medium flex-1">
                        {run.user_request.length > 36
                          ? run.user_request.slice(0, 36) + "…"
                          : run.user_request}
                      </span>
                      <SquareChevronRight
                        className={`w-3.5 h-3.5 shrink-0 transition-opacity ${
                          isActive
                            ? "opacity-100 text-accent"
                            : "opacity-0 group-hover:opacity-60 text-muted"
                        }`}
                      />
                    </div>
                    <div className="flex items-center gap-1.5 mt-1.5">
                      <span
                        className={`inline-block w-1.5 h-1.5 rounded-full ${badge.color}`}
                      />
                      <span className="text-[11px] text-muted">
                        {badge.label}
                      </span>
                      <span className="text-[11px] text-muted/50 ml-auto">
                        {formatTime(run.created_at)}
                      </span>
                    </div>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-surface-border text-[10px] text-muted/50 text-center">
        Open Jarvis v0.1
      </div>
    </aside>
  );
}

function formatTime(iso: string): string {
  try {
    const d = new Date(iso);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffMin = Math.floor(diffMs / 60000);
    if (diffMin < 1) return "刚刚";
    if (diffMin < 60) return `${diffMin}分钟前`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr}小时前`;
    const diffDay = Math.floor(diffHr / 24);
    if (diffDay < 7) return `${diffDay}天前`;
    return d.toLocaleDateString("zh-CN");
  } catch {
    return "";
  }
}
