import { useEffect, useRef, useState } from "react";
import { ArrowUp, Loader2, Plus } from "lucide-react";
import type { RunSnapshot } from "../types";
import { RunDetail } from "./RunDetail";
import EmptyState from "./EmptyState";

interface DashboardProps {
  activeRun: RunSnapshot | null;
  activeRunId: string | null;
  loading: boolean;
  error: string | null;
  onSubmit: (request: string) => Promise<string | null>;
  onNewSession: () => void;
}

export function Dashboard({ activeRun, activeRunId, loading, error, onSubmit, onNewSession }: DashboardProps) {
  const [input, setInput] = useState("");
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!loading) inputRef.current?.focus();
  }, [loading, activeRunId]);

  const handleSubmit = async () => {
    const request = input.trim();
    if (!request || loading) return;
    await onSubmit(request);
    setInput("");
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void handleSubmit();
    }
  };

  return (
    <div className="flex h-full min-h-0 flex-col">
      <header className="flex h-16 shrink-0 items-center gap-3 border-b border-surface-border bg-surface/95 px-4 backdrop-blur sm:px-6">
        <div className="min-w-0 flex-1">
          {activeRun ? (
            <div className="flex min-w-0 items-center gap-2.5">
              <h2 className="truncate text-sm font-medium">{activeRun.user_request}</h2>
              <StatusBadge status={activeRun.status} />
            </div>
          ) : (
            <div>
              <h2 className="text-sm font-semibold">新会话</h2>
              <p className="text-xs text-muted">提交目标后开始一次独立运行</p>
            </div>
          )}
        </div>
        <button type="button" onClick={onNewSession} className="inline-flex min-h-11 items-center gap-2 rounded-lg border border-surface-border px-3 text-xs font-medium text-muted-foreground transition-colors hover:bg-surface-raised hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent">
          <Plus className="h-4 w-4" aria-hidden="true" />
          <span className="hidden sm:inline">新建会话</span>
        </button>
      </header>

      {error && !activeRun ? (
        <div className="m-6 rounded-xl border border-red-500/30 bg-red-500/10 p-4" role="alert">
          <p className="text-sm font-medium text-red-300">无法读取运行状态</p>
          <p className="mt-1 text-xs text-red-200/80">{error}</p>
        </div>
      ) : activeRun && activeRunId ? (
        <div className="min-h-0 flex-1 overflow-y-auto">
          <RunDetail run={activeRun} />
        </div>
      ) : (
        <div className="flex min-h-0 flex-1 items-center justify-center px-4">
          <div className="w-full max-w-2xl">
            <EmptyState />
            <InputBar input={input} setInput={setInput} loading={loading} onSubmit={() => void handleSubmit()} onKeyDown={handleKeyDown} inputRef={inputRef} />
          </div>
        </div>
      )}

      {activeRun && (
        <div className="shrink-0 border-t border-surface-border bg-surface px-4 py-3 sm:px-6">
          <div className="mx-auto max-w-5xl">
            <InputBar input={input} setInput={setInput} loading={loading} onSubmit={() => void handleSubmit()} onKeyDown={handleKeyDown} inputRef={inputRef} compact />
          </div>
        </div>
      )}
    </div>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { label: string; className: string }> = {
    queued: { label: "排队中", className: "bg-slate-500/20 text-slate-200" },
    running: { label: "运行中", className: "bg-sky-500/15 text-sky-300" },
    planning: { label: "规划中", className: "bg-violet-500/15 text-violet-300" },
    executing: { label: "执行中", className: "bg-cyan-500/15 text-cyan-300" },
    aggregating: { label: "汇总中", className: "bg-amber-500/15 text-amber-300" },
    reviewing: { label: "审核中", className: "bg-orange-500/15 text-orange-300" },
    finalizing: { label: "生成结果", className: "bg-emerald-500/15 text-emerald-300" },
    done: { label: "已完成", className: "bg-emerald-500/15 text-emerald-300" },
    success: { label: "已完成", className: "bg-emerald-500/15 text-emerald-300" },
    partial: { label: "部分完成", className: "bg-yellow-500/15 text-yellow-300" },
    failed: { label: "失败", className: "bg-red-500/15 text-red-300" },
    cancelled: { label: "已取消", className: "bg-slate-500/20 text-slate-200" },
  };
  const info = config[status] ?? { label: status, className: "bg-slate-500/20 text-slate-200" };
  const isRunning = ["queued", "running", "planning", "executing", "aggregating", "reviewing", "finalizing"].includes(status);
  return <span aria-live="polite" className={`inline-flex shrink-0 items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium ${info.className}`}>{isRunning && <span className="dot-pulse h-1.5 w-1.5" aria-hidden="true" />}{info.label}</span>;
}

interface InputBarProps {
  input: string;
  setInput: (value: string) => void;
  loading: boolean;
  onSubmit: () => void;
  onKeyDown: (event: React.KeyboardEvent) => void;
  inputRef: React.RefObject<HTMLTextAreaElement | null>;
  compact?: boolean;
}

function InputBar({ input, setInput, loading, onSubmit, onKeyDown, inputRef, compact = false }: InputBarProps) {
  return (
    <div className={`relative rounded-2xl border border-surface-border bg-surface-raised transition-colors focus-within:border-accent/60 ${compact ? "" : "shadow-xl shadow-black/10"}`}>
      <label htmlFor="run-request" className="sr-only">运行目标</label>
      <textarea id="run-request" ref={inputRef} value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={onKeyDown} placeholder="描述你希望 Agent 完成的目标…" rows={compact ? 1 : 3} disabled={loading} className="w-full resize-none bg-transparent px-4 py-3 pr-14 text-sm leading-6 text-[#e5e7eb] outline-none placeholder:text-muted/60 disabled:cursor-not-allowed" />
      <button type="button" onClick={onSubmit} disabled={loading || !input.trim()} aria-label="开始运行" className="absolute bottom-2 right-2 inline-flex h-9 w-9 items-center justify-center rounded-xl bg-accent text-white transition-colors hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent">
        {loading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : <ArrowUp className="h-4 w-4" aria-hidden="true" />}
      </button>
      {!compact && <p className="px-4 pb-3 text-[11px] text-muted/60">Enter 发送 · Shift + Enter 换行</p>}
    </div>
  );
}
