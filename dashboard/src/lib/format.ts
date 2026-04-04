import type { AIConfigSource, Task } from "../types";

export function formatDate(value: string | null | undefined): string {
  if (!value) {
    return "未记录";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("zh-CN", { hour12: false });
}

export function formatTaskStatus(status: string): string {
  const labels: Record<string, string> = {
    PENDING_DISPATCH: "待分发",
    RUNNING: "运行中",
    AWAITING_APPROVAL: "待审批",
    APPROVED: "已批准",
    RESUMING: "恢复执行中",
    REJECTED: "已拒绝",
    COMPLETED: "已完成",
    FAILED: "失败",
  };
  return labels[status] ?? status;
}

export function formatBytes(value: number | null | undefined): string {
  if (!value) {
    return "0 B";
  }
  if (value < 1024) {
    return `${value} B`;
  }
  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

export function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "请求失败";
}

export function maskSecret(value: string | null | undefined): string {
  const raw = (value ?? "").trim();
  if (!raw) {
    return "-";
  }
  if (raw.length <= 8) {
    return `${raw.slice(0, 2)}****`;
  }
  return `${raw.slice(0, 4)}****${raw.slice(-4)}`;
}

export function summarizeTask(task: Task): string {
  return task.command || task.result || task.error || task.reason || task.instruction;
}

export function describeTaskNarrative(task: Task): string {
  if (task.status === "AWAITING_APPROVAL" && task.command) {
    return `已整理出待审批操作：${task.command}${task.reason ? `。原因：${task.reason}` : ""}`;
  }
  if (task.status === "RUNNING" || task.status === "RESUMING") {
    return "正在执行已规划动作，新的日志会持续回收到当前线程。";
  }
  if (task.status === "APPROVED") {
    return "审批已通过，执行端正在恢复任务。";
  }
  if (task.status === "COMPLETED") {
    return task.result || "任务已完成，结果已回传。";
  }
  if (task.status === "FAILED") {
    return task.error || "任务执行失败，请查看日志定位原因。";
  }
  if (task.status === "REJECTED") {
    return "这条任务在审批环节被拒绝，系统已停止继续执行。";
  }
  return "任务已进入执行链路，Jarvis 会继续同步审批与日志。";
}

export function formatAiSource(source: AIConfigSource | null | undefined): string {
  if (source === "device_override") {
    return "设备覆盖";
  }
  if (source === "environment_fallback") {
    return "环境回退";
  }
  return "继承 Gateway 默认";
}
