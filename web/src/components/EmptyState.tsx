import { Bot, GitFork, ShieldCheck, Sparkles } from "lucide-react";

export default function EmptyState() {
  return (
    <section className="mb-8 text-center">
      <div className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-accent/15">
        <Bot className="h-7 w-7 text-accent" aria-hidden="true" />
      </div>
      <h1 className="mt-5 text-2xl font-semibold tracking-tight">开始一个独立运行</h1>
      <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-muted">描述目标后，Open Jarvis 会生成计划、执行子任务、汇总结果，并展示整个运行过程。</p>
      <div className="mx-auto mt-6 grid max-w-lg grid-cols-3 gap-3 text-left text-[11px] text-muted">
        <Feature icon={Sparkles} label="自动规划" />
        <Feature icon={GitFork} label="任务执行" />
        <Feature icon={ShieldCheck} label="质量审核" />
      </div>
    </section>
  );
}

function Feature({ icon: Icon, label }: { icon: typeof Sparkles; label: string }) {
  return <div className="flex items-center justify-center gap-1.5"><Icon className="h-3.5 w-3.5 text-accent-hover" aria-hidden="true" /><span>{label}</span></div>;
}
