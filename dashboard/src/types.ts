export type TaskStatus =
  | "PENDING_DISPATCH"
  | "RUNNING"
  | "AWAITING_APPROVAL"
  | "APPROVED"
  | "REJECTED"
  | "COMPLETED"
  | "FAILED";

export type Device = {
  device_id: string;
  name: string;
  type: string;
  device_key: string;
  created_at: string;
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

export type SystemInfo = {
  database_url: string;
  jwt_algorithm: string;
  admin_username: string;
  configured_devices: string[];
  dashboard_origins: string[];
  skill_archives_path: string;
};
