import type { TaskStatus } from "../types";

export type TabId =
  | "overview"
  | "chat"
  | "devices"
  | "skills"
  | "tasks"
  | "ai-calls"
  | "settings";

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
  source: "builtin" | "archive";
  archive_file: File | null;
  existing_archive_filename: string;
  existing_archive_sha256: string;
  existing_archive_size: number;
};

export type AssignmentForm = {
  skill_id: string;
  config: string;
};

export type GatewayAiForm = {
  provider: string;
  model: string;
  api_key: string;
  base_url: string;
};

export type DeviceAiForm = {
  device_id: string;
  provider: string;
  model: string;
  api_key: string;
  base_url: string;
};

export type ClientDeploymentForm = {
  device_id: string;
  name: string;
  device_key: string;
  gateway_url: string;
  repo_url: string;
  repo_ref: string;
  network_profile: "global" | "cn";
  skill_ids: string[];
};

export const tabs: Array<{ id: TabId; label: string; hint: string }> = [
  { id: "overview", label: "概览", hint: "任务与连接状态" },
  { id: "chat", label: "聊天", hint: "下发任务、审批、日志" },
  { id: "devices", label: "设备", hint: "注册、轮换、分配 Skill" },
  { id: "skills", label: "Skills", hint: "能力目录与配置" },
  { id: "tasks", label: "任务", hint: "任务状态与日志" },
  { id: "ai-calls", label: "AI 调用", hint: "查看模型请求、响应与测试记录" },
  { id: "settings", label: "系统", hint: "业务配置与账号范围" },
];

export const taskStatuses: TaskStatus[] = [
  "PENDING_DISPATCH",
  "RUNNING",
  "AWAITING_APPROVAL",
  "APPROVED",
  "RESUMING",
  "REJECTED",
  "COMPLETED",
  "FAILED",
];

export function createEmptyDeviceForm(): DeviceForm {
  return { device_id: "", name: "", type: "cli", device_key: "" };
}

export function createEmptySkillForm(): SkillForm {
  return {
    skill_id: "",
    name: "",
    description: "",
    config: "{}",
    source: "archive",
    archive_file: null,
    existing_archive_filename: "",
    existing_archive_sha256: "",
    existing_archive_size: 0,
  };
}

export function createEmptyAssignmentForm(): AssignmentForm {
  return { skill_id: "", config: "{}" };
}

export function createEmptyGatewayAiForm(): GatewayAiForm {
  return {
    provider: "",
    model: "",
    api_key: "",
    base_url: "",
  };
}

export function createEmptyDeviceAiForm(): DeviceAiForm {
  return {
    device_id: "",
    provider: "",
    model: "",
    api_key: "",
    base_url: "",
  };
}

export function createEmptyClientDeploymentForm(
  gatewayUrl: string = "",
): ClientDeploymentForm {
  return {
    device_id: "",
    name: "",
    device_key: "",
    gateway_url: gatewayUrl,
    repo_url: "",
    repo_ref: "main",
    network_profile: "global",
    skill_ids: [],
  };
}

export type ChatQuickPrompt = {
  label: string;
  prompt: string;
};
