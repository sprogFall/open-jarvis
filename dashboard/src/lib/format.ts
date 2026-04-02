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
    REJECTED: "已拒绝",
    COMPLETED: "已完成",
    FAILED: "失败",
  };
  return labels[status] ?? status;
}

export function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "请求失败";
}
