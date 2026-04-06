import { KeyValueGrid } from "../../components/KeyValueGrid";
import { SectionHeader } from "../../components/SectionHeader";
import { formatAiCallSource, formatDate } from "../../lib/format";
import type { AICallLog } from "../../types";

type AiCallsTabProps = {
  calls: AICallLog[];
  selectedCall: AICallLog | null;
  onSelectCall: (callId: string | null) => void;
  onRefresh: () => void | Promise<void>;
};

export function AiCallsTab({
  calls,
  selectedCall,
  onSelectCall,
  onRefresh,
}: AiCallsTabProps) {
  return (
    <section className="ai-calls-layout">
      <section className="panel">
        <SectionHeader
          eyebrow="Audit"
          title="AI 调用记录"
          actions={(
            <button className="ghost-button" onClick={() => void onRefresh()} type="button">
              刷新记录
            </button>
          )}
        />
        <div className="table-shell">
          <table>
            <thead>
              <tr>
                <th>时间</th>
                <th>来源</th>
                <th>目标</th>
                <th>模型</th>
                <th>结果</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {calls.map((call) => (
                <tr key={call.call_id}>
                  <td>{formatDate(call.created_at)}</td>
                  <td>{formatAiCallSource(call.source)}</td>
                  <td>{call.device_id || call.task_id || "Gateway"}</td>
                  <td>{call.provider} · {call.model}</td>
                  <td>{call.error ? "失败" : "成功"}</td>
                  <td>
                    <button
                      className="ghost-button"
                      onClick={() => onSelectCall(call.call_id)}
                      type="button"
                    >
                      查看详情
                    </button>
                  </td>
                </tr>
              ))}
              {!calls.length ? (
                <tr>
                  <td colSpan={6}>
                    <p className="empty-copy">当前还没有 AI 调用记录。</p>
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel panel-stack ai-call-detail">
        <SectionHeader eyebrow="Detail" title="请求与响应" />
        {selectedCall ? (
          <>
            <KeyValueGrid
              items={[
                { label: "时间", value: formatDate(selectedCall.created_at) },
                { label: "来源", value: formatAiCallSource(selectedCall.source) },
                { label: "设备", value: selectedCall.device_id || "-" },
                { label: "任务", value: selectedCall.task_id || "-" },
                { label: "供应商", value: selectedCall.provider },
                { label: "模型", value: selectedCall.model },
                { label: "Endpoint", value: selectedCall.endpoint || "-" },
                { label: "结果", value: selectedCall.error ? "失败" : "成功" },
              ]}
            />

            <div className="panel panel-nested panel-stack">
              <SectionHeader compact eyebrow="Prompt" title="System Prompt" titleAs="h4" />
              <pre className="ai-call-code">{selectedCall.system_prompt}</pre>
            </div>

            <div className="panel panel-nested panel-stack">
              <SectionHeader compact eyebrow="Prompt" title="User Prompt" titleAs="h4" />
              <pre className="ai-call-code">{selectedCall.user_prompt}</pre>
            </div>

            <div className="panel panel-nested panel-stack">
              <SectionHeader compact eyebrow="Response" title="模型响应" titleAs="h4" />
              <pre className="ai-call-code">
                {selectedCall.error
                  ? selectedCall.error
                  : JSON.stringify(selectedCall.response ?? {}, null, 2)}
              </pre>
            </div>
          </>
        ) : (
          <p className="empty-copy">选择一条调用记录后，可在这里查看完整请求与响应。</p>
        )}
      </section>
    </section>
  );
}
