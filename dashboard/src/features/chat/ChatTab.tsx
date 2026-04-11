import { useEffect, useMemo, useState } from "react";

import { FormField } from "../../components/FormField";
import { SectionHeader } from "../../components/SectionHeader";
import { StatusPill } from "../../components/StatusPill";
import {
  describeTaskNarrative,
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
  gatewayAi: AIConfigSummary | null;
  clientAi: AIConfigSummary[];
  onSelectTask: (taskId: string | null) => void;
  onSelectDevice: (deviceId: string) => void;
  onSendTask: (instruction: string) => Promise<void>;
  onSubmitDecision: (approved: boolean) => Promise<void>;
  onDeleteTask: (taskId: string) => Promise<void>;
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
  gatewayAi,
  clientAi,
  onSelectTask,
  onSelectDevice,
  onSendTask,
  onSubmitDecision,
  onDeleteTask,
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

  async function handleDelete() {
    if (!selectedTask) {
      return;
    }
    setDecisionPending(true);
    try {
      await onDeleteTask(selectedTask.task_id);
    } catch {
      // error banner is handled by the controller
    } finally {
      setDecisionPending(false);
    }
  }

  const canDeleteTask = selectedTask
    ? ["COMPLETED", "FAILED", "REJECTED"].includes(selectedTask.status)
    : false;

  return (
    <section className="chat-layout">
      <aside className="panel chat-rail">
        <SectionHeader
          actions={
            <button className="ghost-button" onClick={() => onSelectTask(null)} type="button">
              新对话
            </button>
          }
          compact
          eyebrow="线程"
          title="聊天任务"
        />

        <div className="chat-rail-status">
          <span className="live-dot" />
          <div>
            <strong>手动同步</strong>
            <small>查看最新任务进展</small>
          </div>
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
        <SectionHeader
          actions={
            <div className="header-actions">
              {selectedTask && canDeleteTask ? (
                <button
                  className="ghost-button"
                  disabled={decisionPending}
                  onClick={() => void handleDelete()}
                  type="button"
                >
                  删除记录
                </button>
              ) : null}
              <button className="ghost-button" onClick={() => void onRefresh()} type="button">
                手动同步
              </button>
            </div>
          }
          className="chat-stage-head"
          eyebrow="会话"
          title={selectedTask ? `任务 ${selectedTask.task_id}` : "给 Jarvis 一个目标"}
        />

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
                  <SectionHeader
                    actions={<StatusPill status={selectedTask.status} />}
                    compact
                    eyebrow="审批"
                    title="待审批动作"
                    titleAs="h4"
                  />
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
                  <SectionHeader compact eyebrow="日志" title="执行日志" titleAs="h4" />
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
                  下发任务并查看审批、恢复和结果。
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
            <FormField className="chat-target-field" htmlFor="chat-target-device" label="执行目标">
              <select
                id="chat-target-device"
                value={selectedDeviceId}
                onChange={(event) => onSelectDevice(event.target.value)}
              >
                {targets.map((target) => (
                  <option key={target.device_id} value={target.device_id}>
                    {target.label}
                  </option>
                ))}
              </select>
            </FormField>
            <div className="chat-effective-ai">
              <span>当前模型</span>
              <strong>
                {effectiveAi
                  ? `${effectiveAi.provider} · ${effectiveAi.model}`
                  : "尚未配置 AI"}
              </strong>
              {effectiveAi ? (
                <small>用于当前任务</small>
              ) : (
                <small>请先完成 AI 设置。</small>
              )}
            </div>
          </div>
          <FormField htmlFor="chat-task-draft" label="任务描述">
            <textarea
              id="chat-task-draft"
              rows={4}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="例如：查看网关最近 100 行日志并标出异常"
            />
          </FormField>
          <div className="panel-head compact">
            <div className="muted">
              {selectedTarget
                ? `消息将发往 ${selectedTarget.name}。`
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
