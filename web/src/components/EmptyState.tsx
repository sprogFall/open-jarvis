import { Bot, Sparkles } from "lucide-react";

export default function EmptyState() {
  return (
    <div className="text-center mb-8 animate-fade-in">
      <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-accent/15 mb-5">
        <Bot className="w-7 h-7 text-accent" />
      </div>
      <h2 className="text-xl font-semibold tracking-tight mb-2">
        Open Jarvis Workbench
      </h2>
      <p className="text-sm text-muted max-w-sm mx-auto leading-relaxed">
        描述你的任务目标，Agent 将自动规划、拆解子任务、并行执行，并汇总结果。
      </p>
      <div className="flex items-center justify-center gap-6 mt-5 text-[11px] text-muted/70">
        <div className="flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5" />
          <span>自动规划</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span>⚡</span>
          <span>并行执行</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span>🔍</span>
          <span>质量审核</span>
        </div>
      </div>
    </div>
  );
}
