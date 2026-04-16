import { SectionHeader } from "../../components/SectionHeader";
import {
  formatAiCallSource,
  formatDate,
  summarizeTriggeredSkills,
} from "../../lib/format";
import type { AICallLog } from "../../types";

type AiCallsTabProps = {
  calls: AICallLog[];
  selectedCallId: string | null;
  onOpenDetail: (callId: string) => void;
  onRefresh: () => void | Promise<void>;
};

export function AiCallsTab({
  calls,
  selectedCallId,
  onOpenDetail,
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
                <th>触发 Skill</th>
                <th>结果</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {calls.map((call) => (
                <tr className={selectedCallId === call.call_id ? "selected-row" : ""} key={call.call_id}>
                  <td>{formatDate(call.created_at)}</td>
                  <td>{formatAiCallSource(call.source)}</td>
                  <td>{call.device_id || call.task_id || "Gateway"}</td>
                  <td>{call.provider} · {call.model}</td>
                  <td>
                    {call.triggered_actions.length ? (
                      <div className="ai-call-skill-summary">
                        <strong>{summarizeTriggeredSkills(call.triggered_actions)}</strong>
                        <span>{call.triggered_actions.map((action) => action.action_name).join(" · ")}</span>
                      </div>
                    ) : (
                      <span className="cell-subtle">未触发 Skill</span>
                    )}
                  </td>
                  <td>{call.error ? "失败" : "成功"}</td>
                  <td>
                    <button
                      className="ghost-button"
                      onClick={() => onOpenDetail(call.call_id)}
                      type="button"
                    >
                      查看详情
                    </button>
                  </td>
                </tr>
              ))}
              {!calls.length ? (
                <tr>
                  <td colSpan={7}>
                    <p className="empty-copy">当前还没有 AI 调用记录。</p>
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>
    </section>
  );
}
