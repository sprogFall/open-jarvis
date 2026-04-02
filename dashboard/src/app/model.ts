import type { TaskStatus } from "../types";

export type TabId = "overview" | "devices" | "skills" | "tasks" | "settings";

export type DeviceForm = {
  device_id: string;
  name: string;
  type: string;
  device_key: string;
};

export type SkillForm = {
  skill_id: string;
  name: string;
  description: string;
  config: string;
};

export type AssignmentForm = {
  skill_id: string;
  config: string;
};

export const tabs: Array<{ id: TabId; label: string; hint: string }> = [
  { id: "overview", label: "概览", hint: "任务与连接状态" },
  { id: "devices", label: "设备", hint: "注册、轮换、分配 Skill" },
  { id: "skills", label: "Skills", hint: "能力目录与配置" },
  { id: "tasks", label: "任务", hint: "任务状态与日志" },
  { id: "settings", label: "系统", hint: "网关参数与部署信息" },
];

export const taskStatuses: TaskStatus[] = [
  "PENDING_DISPATCH",
  "RUNNING",
  "AWAITING_APPROVAL",
  "APPROVED",
  "REJECTED",
  "COMPLETED",
  "FAILED",
];

export function createEmptyDeviceForm(): DeviceForm {
  return { device_id: "", name: "", type: "cli", device_key: "" };
}

export function createEmptySkillForm(): SkillForm {
  return { skill_id: "", name: "", description: "", config: "{}" };
}

export function createEmptyAssignmentForm(): AssignmentForm {
  return { skill_id: "", config: "{}" };
}
