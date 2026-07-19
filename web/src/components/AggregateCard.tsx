import { Merge, FileOutput } from "lucide-react";
import type { AggregateResult } from "../types";
import MarkdownRenderer from "./MarkdownRenderer";

interface AggregateCardProps {
  aggregate: AggregateResult;
}

export function AggregateCard({ aggregate }: AggregateCardProps) {
  return (
    <div className="bg-surface-raised rounded-2xl border border-surface-border overflow-hidden animate-slide-up">
      <div className="flex items-center gap-3 px-5 py-4 border-b border-surface-border">
        <div className="w-8 h-8 rounded-xl bg-amber-500/15 flex items-center justify-center shrink-0">
          <Merge className="w-4 h-4 text-amber-400" />
        </div>
        <div>
          <h3 className="text-sm font-semibold">结果汇总</h3>
          <p className="text-[10px] text-muted">多任务执行结果整合</p>
        </div>
      </div>
      <div className="px-5 py-4 space-y-3">
        <div>
          <MarkdownRenderer content={aggregate.candidate_answer} compact />
        </div>

        {aggregate.artifact_refs.length > 0 && (
          <div>
            <p className="text-[10px] text-muted/60 uppercase tracking-wider mb-1.5">引用产物</p>
            <div className="flex flex-wrap gap-1.5">
              {aggregate.artifact_refs.map((ref, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-surface-overlay text-[10px] font-mono text-muted/70"
                >
                  <FileOutput className="w-3 h-3" />
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
