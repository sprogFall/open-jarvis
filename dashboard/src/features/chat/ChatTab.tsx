import { useEffect, useMemo, useState } from "react";

import { StatusPill } from "../../components/StatusPill";
import {
  describeTaskNarrative,
  formatAiSource,
  formatTaskStatus,
  summarizeTask,
} from "../../lib/format";
import type { AIConfigSummary, Task } from "../../types";

type ChatTarget = {
  device_id: string;
  name: string;
  type: string;
  connected: boolean;
  label: string;
};

type ChatTabProps = {
  tasks: Task[];
  selectedTask: Task | null;
  selectedTaskId: string | null;
  targets: ChatTarget[];
  selectedDeviceId: string;
  socketState: "connecting" | "connected" | "offline";
  gatewayAi: AIConfigSummary | null;
  clientAi: AIConfigSummary[];
  onSelectTask: (taskId: string | null) => void;
  onSelectDevice: (deviceId: string) => void;
  onSendTask: (instruction: string) => Promise<void>;
  onSubmitDecision: (approved: boolean) => Promise<void>;
  onRefresh: () => void | Promise<void>;
};

const quickPrompts = [
  { label: "巡检容器", prompt: "检查 docker 容器状态并汇总异常" },
  { label: "恢复挂起任务", prompt: "检查当前所有挂起任务并给出恢复建议" },
  { label: "查看网关日志", prompt: "查看网关最近 100 行日志并标出异常" },
];

export function ChatTab({
  tasks,
  selectedTask,
  selectedTaskId,
  targets,
  selectedDeviceId,
  socketState,
  gatewayAi,
  clientAi,
  onSelectTask,
  onSelectDevice,
  onSendTask,
  onSubmitDecision,
  onRefresh,
}: ChatTabProps) {
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [decisionPending, setDecisionPending] = useState(false);

  useEffect(() => {
    if (selectedTaskId) {
      setDraft("");
    }
  }, [selectedTaskId]);

  const selectedTarget = useMemo(
    () => targets.find((target) => target.device_id === selectedDeviceId) ?? targets[0] ?? null,
    [selectedDeviceId, targets],
  );

  const effectiveAi = useMemo(() => {
    if (!selectedTarget) {
      return gatewayAi;
    }
    if (selectedTarget.type === "gateway") {
      return gatewayAi;
    }
    return clientAi.find((summary) => summary.device_id === selectedTarget.device_id) ?? gatewayAi;
  }, [clientAi, gatewayAi, selectedTarget]);

  async function handleSend() {
    const instruction = draft.trim();
    if (!instruction) {
      return;
    }
    setSending(true);
    try {
      await onSendTask(instruction);
      setDraft("");
    } catch {
      // error banner is handled by the controller
    } finally {
      setSending(false);
    }
  }

  async function handleDecision(approved: boolean) {
    setDecisionPending(true);
    try {
      await onSubmitDecision(approved);
    } catch {
      // error banner is handled by the controller
    } finally {
      setDecisionPending(false);
    }
  }

  return (
    <section className="chat-layout">
      <aside className="panel chat-rail">
        <div className="panel-head compact">
          <div>
            <p className="eyebrow">线程</p>
            <h3>聊天任务</h3>
          </div>
          <button className="ghost-button" onClick={() => onSelectTask(null)} type="button">
            新对话
          </button>
        </div>

        <div className="chat-rail-status">
          <span className={`live-dot${socketState === "connected" ? " solid" : ""}`} />
          <strong>{socketState === "connected" ? "实时同步中" : socketState === "connecting" ? "正在连接" : "实时连接已断开"}</strong>
        </div>

        <div className="chat-thread-list">
          {tasks.length ? (
            tasks.map((task) => (
              <button
                key={task.task_id}
                className={`chat-thread${selectedTaskId === task.task_id ? " active" : ""}`}
                onClick={() => onSelectTask(task.task_id)}
                type="button"
              >
                <div className="chat-thread-head">
                  <strong>{task.device_id}</strong>
                  <StatusPill status={task.status} />
                </div>
                <span>{task.instruction}</span>
                <small>{summarizeTask(task)}</small>
              </button>
            ))
          ) : (
            <p className="empty-copy">还没有聊天线程，先发出第一条任务。</p>
          )}
        </div>
      </aside>

      <div className="panel chat-stage">
        <div className="panel-head chat-stage-head">
          <div>
            <p className="eyebrow">会话</p>
            <h3>{selectedTask ? `任务 ${selectedTask.task_id}` : "给 Jarvis 一个目标"}</h3>
          </div>
          <div className="header-actions">
            <button className="ghost-button" onClick={() => void onRefresh()} type="button">
              刷新线程
            </button>
          </div>
        </div>

        <div className="chat-conversation">
          {selectedTask ? (
            <>
              <section className="chat-hero">
                <div>
                  <p className="eyebrow">状态</p>
                  <h4>{formatTaskStatus(selectedTask.status)}</h4>
                  <p className="muted">目标设备：{selectedTask.device_id}</p>
                </div>
                <StatusPill status={selectedTask.status} />
              </section>

              <article className="chat-bubble chat-bubble-user">
                <span>你</span>
                <strong>任务已发送</strong>
                <p>{selectedTask.instruction}</p>
              </article>

              <article className="chat-bubble chat-bubble-assistant">
                <span>Jarvis</span>
                <strong>任务分析</strong>
                <p>{describeTaskNarrative(selectedTask)}</p>
              </article>

              {selectedTask.command || selectedTask.reason || selectedTask.status === "AWAITING_APPROVAL" ? (
                <section className="chat-card chat-approval-card">
                  <div className="panel-head compact">
                    <div>
                      <p className="eyebrow">审批</p>
                      <h4>待审批动作</h4>
                    </div>
                    <StatusPill status={selectedTask.status} />
                  </div>
                  <pre>{selectedTask.command || "等待命令生成"}</pre>
                  {selectedTask.reason ? <p className="muted">{selectedTask.reason}</p> : null}
                  {selectedTask.status === "AWAITING_APPROVAL" ? (
                    <div className="row-actions">
                      <button
                        className="primary-button"
                        disabled={decisionPending}
                        onClick={() => void handleDecision(true)}
                        type="button"
                      >
                        批准继续
                      </button>
                      <button
                        className="danger-button"
                        disabled={decisionPending}
                        onClick={() => void handleDecision(false)}
                        type="button"
                      >
                        拒绝执行
                      </button>
                    </div>
                  ) : null}
                </section>
              ) : null}

              {selectedTask.logs.length ? (
                <section className="chat-card log-panel">
                  <div className="panel-head compact">
                    <div>
                      <p className="eyebrow">日志</p>
                      <h4>实时日志</h4>
                    </div>
                  </div>
                  <pre>{selectedTask.logs.join("\n")}</pre>
                </section>
              ) : null}

              {selectedTask.result ? (
                <section className="chat-card chat-result success">
                  <p className="eyebrow">结果</p>
                  <h4>执行结果</h4>
                  <pre>{selectedTask.result}</pre>
                </section>
              ) : null}

              {selectedTask.error ? (
                <section className="chat-card chat-result failure">
                  <p className="eyebrow">结果</p>
                  <h4>执行错误</h4>
                  <pre>{selectedTask.error}</pre>
                </section>
              ) : null}
            </>
          ) : (
            <section className="chat-welcome">
              <div className="chat-welcome-hero">
                <p className="eyebrow">快速开始</p>
                <h4>像聊天一样下发任务</h4>
                <p>
                  在同一条线程里查看审批、恢复状态和执行日志；需要特殊模型时再为 CLI 单独覆盖。
                </p>
              </div>
              <div className="chat-prompt-list">
                {quickPrompts.map((prompt) => (
                  <button
                    key={prompt.label}
                    className="chat-quick-action"
                    onClick={() => setDraft(prompt.prompt)}
                    type="button"
                  >
                    <strong>{prompt.label}</strong>
                    <span>{prompt.prompt}</span>
                  </button>
                ))}
              </div>
            </section>
          )}
        </div>

        <div className="chat-composer">
          <div className="chat-composer-head">
            <label className="field chat-target-field">
              <span>执行目标</span>
              <select
                value={selectedDeviceId}
                onChange={(event) => onSelectDevice(event.target.value)}
              >
                {targets.map((target) => (
                  <option key={target.device_id} value={target.device_id}>
                    {target.label}
                  </option>
                ))}
              </select>
            </label>
            <div className="chat-effective-ai">
              <span>当前生效配置</span>
              <strong>
                {effectiveAi
                  ? `${effectiveAi.provider} · ${effectiveAi.model}`
                  : "尚未配置 AI"}
              </strong>
              {effectiveAi ? (
                <small>
                  {formatAiSource(effectiveAi.source)} · API Key（掩码）{effectiveAi.api_key_masked}
                </small>
              ) : (
                <small>请先在系统页配置 Gateway 默认 AI，或为特定 CLI 设置覆盖。</small>
              )}
            </div>
          </div>
          <label className="field">
            <span>任务描述</span>
            <textarea
              rows={4}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="例如：查看网关最近 100 行日志并标出异常"
            />
          </label>
          <div className="panel-head compact">
            <div className="muted">
              {selectedTarget
                ? `消息会发往 ${selectedTarget.name}，后续审批与日志会继续回收到当前线程。`
                : "请选择执行目标后再发送任务。"}
            </div>
            <button
              className="primary-button"
              disabled={!draft.trim() || !selectedTarget || sending}
              onClick={() => void handleSend()}
              type="button"
            >
              {sending ? "发送中…" : "发送任务"}
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
