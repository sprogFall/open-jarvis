import { Dialog } from "../../components/Dialog";
import { KeyValueGrid } from "../../components/KeyValueGrid";
import { SectionHeader } from "../../components/SectionHeader";
import {
  formatAiArgumentValue,
  formatAiCallSource,
  formatDate,
} from "../../lib/format";
import type { AICallLog } from "../../types";

type AiCallDetailDialogProps = {
  call: AICallLog;
  onClose: () => void;
};

export function AiCallDetailDialog({ call, onClose }: AiCallDetailDialogProps) {
  const triggeredActions = call.triggered_actions ?? [];

  return (
    <Dialog
      eyebrow="AI Detail"
      onClose={onClose}
      size="wide"
      subtitle={`${formatAiCallSource(call.source)} · ${call.provider} · ${call.model}`}
      title="请求与响应"
    >
      <div className="stack">
        <KeyValueGrid
          items={[
            { label: "时间", value: formatDate(call.created_at) },
            { label: "来源", value: formatAiCallSource(call.source) },
            { label: "设备", value: call.device_id || "-" },
            { label: "任务", value: call.task_id || "-" },
            { label: "供应商", value: call.provider },
            { label: "模型", value: call.model },
            { label: "Endpoint", value: call.endpoint || "-" },
            { label: "结果", value: call.error ? "失败" : "成功" },
          ]}
        />

        <section className="panel panel-nested panel-stack">
          <SectionHeader
            compact
            eyebrow="Skills"
            title={`触发 Skill${triggeredActions.length ? ` · ${triggeredActions.length}` : ""}`}
            titleAs="h4"
          />
          {triggeredActions.length ? (
            <div className="ai-call-action-list">
              {triggeredActions.map((action, index) => {
                const entries = Object.entries(action.args ?? {});
                return (
                  <article
                    className="ai-call-action-card"
                    key={`${call.call_id}-${action.action_name}-${index}`}
                  >
                    <div className="ai-call-action-head">
                      <div>
                        <strong>{action.skill_name}</strong>
                        <span>{action.skill_id}</span>
                      </div>
                      <span className={`package-pill${action.requires_approval ? " pending" : " ready"}`}>
                        {action.requires_approval ? "需审批" : "直接执行"}
                      </span>
                    </div>
                    <p className="ai-call-action-name">{action.action_name}</p>
                    {entries.length ? (
                      <dl className="ai-call-arg-list">
                        {entries.map(([key, value]) => (
                          <div key={key}>
                            <dt>{key}</dt>
                            <dd>{formatAiArgumentValue(value)}</dd>
                          </div>
                        ))}
                      </dl>
                    ) : (
                      <p className="empty-copy">本次没有传入额外参数。</p>
                    )}
                    {action.reason ? (
                      <p className="cell-subtle">审批原因：{action.reason}</p>
                    ) : null}
                  </article>
                );
              })}
            </div>
          ) : (
            <p className="empty-copy">当前模型响应没有触发可识别的 Skill。</p>
          )}
        </section>

        <div className="panel panel-nested panel-stack">
          <SectionHeader compact eyebrow="Prompt" title="System Prompt" titleAs="h4" />
          <pre className="ai-call-code">{call.system_prompt}</pre>
        </div>

        <div className="panel panel-nested panel-stack">
          <SectionHeader compact eyebrow="Prompt" title="User Prompt" titleAs="h4" />
          <pre className="ai-call-code">{call.user_prompt}</pre>
        </div>

        <div className="panel panel-nested panel-stack">
          <SectionHeader compact eyebrow="Response" title="模型响应" titleAs="h4" />
          <pre className="ai-call-code">
            {call.error
              ? call.error
              : JSON.stringify(call.response ?? {}, null, 2)}
          </pre>
        </div>
      </div>
    </Dialog>
  );
}
