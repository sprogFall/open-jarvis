import { CheckCircle2, XCircle, AlertTriangle, Lightbulb, ArrowRight } from "lucide-react";
import type { ReviewResult } from "../types";

interface ReviewCardProps {
  review: ReviewResult;
}

export function ReviewCard({ review }: ReviewCardProps) {
  return (
    <div className="bg-surface-raised rounded-2xl border border-surface-border overflow-hidden animate-slide-up">
      <div className="flex items-center gap-3 px-5 py-4 border-b border-surface-border">
        <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
          review.passed ? "bg-emerald-500/15" : "bg-orange-500/15"
        }`}>
          {review.passed ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-orange-400" />
          )}
        </div>
        <div>
          <h3 className="text-sm font-semibold">质量审核</h3>
          <p className={`text-[10px] ${review.passed ? "text-emerald-400/80" : "text-orange-400/80"}`}>
            {review.passed ? "审核通过" : "审核未通过"}
            {review.score !== null && ` · 评分 ${review.score}`}
          </p>
        </div>
      </div>

      <div className="px-5 py-4 space-y-3">
        {/* 问题列表 */}
        {review.issues.length > 0 && (
          <div className="space-y-1.5">
            <p className="text-[10px] text-muted/60 uppercase tracking-wider">发现的问题</p>
            {review.issues.map((issue, i) => (
              <div key={i} className="flex items-start gap-2 text-xs text-muted/80">
                <XCircle className="w-3.5 h-3.5 text-orange-500/60 shrink-0 mt-0.5" />
                <span>{issue}</span>
              </div>
            ))}
          </div>
        )}

        {/* 未通过任务 */}
        {review.failed_task_ids.length > 0 && (
          <div>
            <p className="text-[10px] text-muted/60 uppercase tracking-wider mb-1">未通过任务</p>
            <div className="flex flex-wrap gap-1.5">
              {review.failed_task_ids.map((tid) => (
                <span
                  key={tid}
                  className="px-2 py-0.5 rounded-md bg-red-500/10 text-[11px] font-mono text-red-400/80"
                >
                  {tid}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* 建议动作 */}
        {review.suggested_action && (
          <div className="flex items-center gap-2 p-3 rounded-xl bg-accent/5 border border-accent/10">
            <Lightbulb className="w-4 h-4 text-accent shrink-0" />
            <div className="flex items-center gap-2 text-xs">
              <span className="text-muted/70">建议动作：</span>
              <span className="font-medium text-accent-hover">{review.suggested_action}</span>
            </div>
          </div>
        )}

        {/* 证据引用 */}
        {review.evidence_refs.length > 0 && (
          <div>
            <p className="text-[10px] text-muted/60 uppercase tracking-wider mb-1">证据引用</p>
            <div className="flex flex-wrap gap-1.5">
              {review.evidence_refs.map((ref, i) => (
                <span
                  key={i}
                  className="px-2 py-0.5 rounded-md bg-surface-overlay text-[10px] font-mono text-muted/60"
                >
                  {ref}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
