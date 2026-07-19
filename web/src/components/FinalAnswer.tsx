import { MessageSquareText, AlertTriangle, FileOutput } from "lucide-react";
import type { FinalAnswer as FinalAnswerType } from "../types";
import { StatusBadge } from "./Dashboard";
import MarkdownRenderer from "./MarkdownRenderer";

interface FinalAnswerProps {
  answer: FinalAnswerType;
}

export function FinalAnswer({ answer }: FinalAnswerProps) {
  const isSuccess = answer.status === "success";

  return (
    <div className="bg-surface-raised rounded-2xl border border-surface-border overflow-hidden animate-slide-up">
      <div className="flex items-center justify-between px-5 py-4 border-b border-surface-border">
        <div className="flex items-center gap-3">
          <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
            isSuccess ? "bg-emerald-500/15" : "bg-yellow-500/15"
          }`}>
            <MessageSquareText className={`w-4 h-4 ${isSuccess ? "text-emerald-400" : "text-yellow-400"}`} />
          </div>
          <div>
            <h3 className="text-sm font-semibold">最终答案</h3>
            <p className="text-[10px] text-muted">Agent 产出的最终响应</p>
          </div>
        </div>
        <StatusBadge status={answer.status} />
      </div>

      <div className="px-5 py-4 space-y-3">
        {/* 内容 */}
        <div className="bg-surface rounded-xl px-5 py-4 border border-surface-border">
          <MarkdownRenderer content={answer.content} />
        </div>

        {/* 警告 */}
        {answer.warnings.length > 0 && (
          <div className="flex items-start gap-2 p-3 rounded-xl bg-yellow-500/5 border border-yellow-500/10">
            <AlertTriangle className="w-4 h-4 text-yellow-500 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="text-[10px] text-muted/60 uppercase tracking-wider">警告</p>
              {answer.warnings.map((w, i) => (
                <p key={i} className="text-xs text-yellow-300/80">{w}</p>
              ))}
            </div>
          </div>
        )}

        {/* 产物引用 */}
        {answer.artifact_refs.length > 0 && (
          <div className="flex items-center gap-2 flex-wrap">
            <FileOutput className="w-3.5 h-3.5 text-muted/50" />
            {answer.artifact_refs.map((ref, i) => (
              <span key={i} className="px-2 py-0.5 rounded-md bg-surface-overlay text-[10px] font-mono text-muted/60">
                {ref}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
