export type TaskStatus =
  | "PENDING_DISPATCH"
  | "RUNNING"
  | "AWAITING_APPROVAL"
  | "APPROVED"
  | "RESUMING"
  | "REJECTED"
  | "COMPLETED"
  | "FAILED";

export type Device = {
  device_id: string;
  name: string;
  type: string;
  last_seen_at: string | null;
  connected: boolean;
  skills?: DeviceSkill[];
};

export type Skill = {
  skill_id: string;
  name: string;
  description: string;
  config: Record<string, unknown>;
  source: "builtin" | "archive";
  action_names: string[];
  archive_ready: boolean;
  archive_filename: string | null;
  archive_sha256: string | null;
  archive_size: number;
  archive_updated_at: string | null;
  created_at: string;
};

export type DeviceSkill = {
  device_id?: string;
  skill_id: string;
  name?: string;
  description?: string;
  assigned_at: string;
  config: Record<string, unknown>;
  skill_config?: Record<string, unknown>;
  source?: "builtin" | "archive";
  action_names?: string[];
  archive_ready?: boolean;
  archive_filename?: string | null;
  archive_sha256?: string | null;
  archive_size?: number;
  archive_updated_at?: string | null;
  download_path?: string;
};

export type Task = {
  task_id: string;
  device_id: string;
  instruction: string;
  status: TaskStatus;
  checkpoint_id: string | null;
  command: string | null;
  reason: string | null;
  result: string | null;
  error: string | null;
  logs: string[];
};

export type Overview = {
  device_count: number;
  skill_count: number;
  app_connections: number;
  connected_devices: string[];
  task_counts: Record<string, number>;
};

export type AIConfigSource = "gateway_default" | "device_override" | "environment_fallback";

export type AICallSource = "gateway_router" | "client_planner" | "config_test";

export type AIConfigSummary = {
  provider: string;
  model: string;
  base_url: string | null;
  api_key_masked: string;
  source: AIConfigSource;
  device_id?: string;
};

export type SystemInfo = {
  gateway_ai: AIConfigSummary | null;
  client_ai: AIConfigSummary[];
};

export type AICallLog = {
  call_id: string;
  source: AICallSource;
  device_id: string | null;
  task_id: string | null;
  provider: string;
  model: string;
  endpoint: string | null;
  system_prompt: string;
  user_prompt: string;
  response: Record<string, unknown> | null;
  error: string | null;
  created_at: string;
};

export type QuickDeployModuleId = "client" | "gateway" | "dashboard";

export type QuickDeployField = {
  key: string;
  label: string;
  description: string;
  required: boolean;
  secret: boolean;
  input_type: "text" | "url" | "password" | "select";
  value: string;
};

export type QuickDeployModule = {
  title: string;
  description: string;
  artifact_label: string;
  fields: QuickDeployField[];
};

export type QuickDeployDraft = {
  modules: Record<QuickDeployModuleId, QuickDeployModule>;
  client_package: {
    repo_url: string;
    repo_ref: string;
    register_device: boolean;
  };
};
