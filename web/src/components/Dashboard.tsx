import { useState, useRef, useEffect } from "react";
import { ArrowUp, Loader2 } from "lucide-react";
import type { RunSnapshot } from "../types";
import { RunDetail } from "./RunDetail";
import EmptyState from "./EmptyState";

interface DashboardProps {
  activeRun: RunSnapshot | null;
  activeRunId: string | null;
  loading: boolean;
  error: string | null;
  onSubmit: (request: string) => Promise<string | null>;
}

export function Dashboard({
  activeRun,
  activeRunId,
  loading,
  error,
  onSubmit,
}: DashboardProps) {
  const [input, setInput] = useState("");
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // 新建请求后保持输入框焦点
  useEffect(() => {
    if (!loading && inputRef.current) {
      inputRef.current.focus();
    }
  }, [loading]);

  const handleSubmit = async () => {
    const trimmed = input.trim();
    if (!trimmed || loading) return;
    await onSubmit(trimmed);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // 有活跃运行 → 展示详情
  if (activeRun && activeRunId) {
    return (
      <div className="flex flex-col h-full overflow-hidden animate-fade-in">
        {/* 顶部标题栏 */}
        <header className="shrink-0 px-6 h-14 flex items-center border-b border-surface-border bg-surface">
          <div className="flex items-center gap-3 min-w-0">
            <h2 className="text-sm font-medium text-muted-foreground truncate max-w-lg">
              {activeRun.user_request}
            </h2>
            <StatusBadge status={activeRun.status} />
          </div>
          <div className="ml-auto flex items-center gap-2">
            {activeRun.plan && (
              <span className="text-[11px] text-muted">
                Plan v{activeRun.plan.version}
              </span>
            )}
          </div>
        </header>

        {/* 详情内容 */}
        <div className="flex-1 overflow-y-auto">
          <RunDetail run={activeRun} />
        </div>

        {/* 底部输入栏（紧凑模式） */}
        <div className="shrink-0 border-t border-surface-border bg-surface px-6 py-3">
          <InputBar
            input={input}
            setInput={setInput}
            loading={loading}
            onSubmit={handleSubmit}
            onKeyDown={handleKeyDown}
            inputRef={inputRef}
            compact
          />
        </div>
      </div>
    );
  }

  // 错误提示
  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 text-sm mb-2">请求出错</p>
          <p className="text-xs text-muted">{error}</p>
        </div>
      </div>
    );
  }

  // 空状态 + 大输入框
  return (
    <div className="flex-1 flex flex-col">
      <div className="flex-1 flex items-center justify-center">
        <div className="w-full max-w-[640px] px-6">
          <EmptyState />
          <InputBar
            input={input}
            setInput={setInput}
            loading={loading}
            onSubmit={handleSubmit}
            onKeyDown={handleKeyDown}
            inputRef={inputRef}
          />
        </div>
      </div>
    </div>
  );
}

/* ---- 状态徽章 ---- */
export function StatusBadge({ status }: { status: string }) {
  const cfg: Record<string, { label: string; cls: string }> = {
    queued: { label: "排队中", cls: "bg-slate-600/30 text-slate-300" },
    running: { label: "运行中", cls: "bg-blue-600/20 text-blue-300" },
    planning: { label: "规划中", cls: "bg-violet-600/20 text-violet-300" },
    executing: { label: "执行中", cls: "bg-cyan-600/20 text-cyan-300" },
    aggregating: { label: "汇总中", cls: "bg-amber-600/20 text-amber-300" },
    reviewing: { label: "审核中", cls: "bg-orange-600/20 text-orange-300" },
    finalizing: { label: "收尾中", cls: "bg-emerald-600/20 text-emerald-300" },
    success: { label: "已完成", cls: "bg-emerald-600/20 text-emerald-300" },
    partial: { label: "部分完成", cls: "bg-yellow-600/20 text-yellow-300" },
    failed: { label: "失败", cls: "bg-red-600/20 text-red-300" },
    cancelled: { label: "已取消", cls: "bg-slate-600/20 text-slate-300" },
  };

  const info = cfg[status] ?? { label: status, cls: "bg-slate-600/20 text-slate-300" };

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium ${info.cls}`}>
      {status === "running" && <span className="dot-pulse text-blue-400" />}
      {info.label}
    </span>
  );
}

/* ---- 输入栏 ---- */
interface InputBarProps {
  input: string;
  setInput: (v: string) => void;
  loading: boolean;
  onSubmit: () => void;
  onKeyDown: (e: React.KeyboardEvent) => void;
  inputRef: React.RefObject<HTMLTextAreaElement | null>;
  compact?: boolean;
}

function InputBar({
  input,
  setInput,
  loading,
  onSubmit,
  onKeyDown,
  inputRef,
  compact = false,
}: InputBarProps) {
  return (
    <div
      className={`relative rounded-2xl border transition-colors duration-200 ${
        compact
          ? "bg-surface-raised border-surface-border focus-within:border-accent/40"
          : "bg-surface-raised border-surface-border focus-within:border-accent/50 shadow-lg"
      }`}
    >
      <textarea
        ref={inputRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={onKeyDown}
        placeholder="描述你想做的事情..."
        rows={compact ? 1 : 2}
        className="w-full bg-transparent outline-none resize-none text-sm placeholder:text-muted/50 py-3 px-4 pr-12 text-[#e5e7eb]"
        disabled={loading}
      />
      <button
        onClick={onSubmit}
        disabled={loading || input.trim().length === 0}
        className="absolute right-2 bottom-2 p-1.5 rounded-lg transition-all duration-150
          bg-accent/20 hover:bg-accent/30 text-accent hover:text-accent-hover
          disabled:opacity-30 disabled:cursor-not-allowed"
        title="发送 (Enter)"
      >
        {loading ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <ArrowUp className="w-4 h-4" />
        )}
      </button>
    </div>
  );
}
