import type {
  AICallLog,
  Device,
  Overview,
  QuickDeployDraft,
  QuickDeployModuleId,
  Skill,
  SystemInfo,
  Task,
} from "./types";

function normalizeGatewayBaseUrl(raw: string): string {
  const trimmed = raw.trim().replace(/\/+$/, "");
  if (!trimmed) {
    return "";
  }
  if (/^https?:\/\//i.test(trimmed)) {
    return trimmed;
  }
  return trimmed.startsWith("/") ? trimmed : `/${trimmed}`;
}

const gatewayBaseUrl = normalizeGatewayBaseUrl(
  import.meta.env.VITE_GATEWAY_BASE_URL ?? "",
);

function buildUrl(path: string): string {
  if (!gatewayBaseUrl) {
    return path;
  }
  return `${gatewayBaseUrl}${path}`;
}

function buildAbsoluteGatewayUrl(path: string): URL {
  return new URL(buildUrl(path), window.location.origin);
}

function toWebSocketUrl(url: URL): string {
  if (url.protocol === "https:") {
    url.protocol = "wss:";
  } else if (url.protocol === "http:") {
    url.protocol = "ws:";
  }
  return url.toString();
}

async function request<T>(
  path: string,
  init: RequestInit = {},
  token?: string,
): Promise<T> {
  const headers = new Headers(init.headers);
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(buildUrl(path), {
    ...init,
    headers,
  });
  if (response.status === 204) {
    return undefined as T;
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const detail =
      typeof payload.detail === "string"
        ? payload.detail
        : `Request failed with status ${response.status}`;
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

function parseDownloadFilename(headerValue: string | null): string | null {
  if (!headerValue) {
    return null;
  }
  const matched = headerValue.match(/filename="([^"]+)"/i);
  return matched?.[1] ?? null;
}

async function requestFile(
  path: string,
  init: RequestInit = {},
  token?: string,
): Promise<{ blob: Blob; filename: string | null }> {
  const headers = new Headers(init.headers);
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(buildUrl(path), {
    ...init,
    headers,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const detail =
      typeof payload.detail === "string"
        ? payload.detail
        : `Request failed with status ${response.status}`;
    throw new Error(detail);
  }
  return {
    blob: await response.blob(),
    filename: parseDownloadFilename(response.headers.get("content-disposition")),
  };
}

export const dashboardApi = {
  gatewayBaseUrl,
  buildWebSocketUrl(path: string, query: Record<string, string> = {}): string {
    const url = buildAbsoluteGatewayUrl(path);
    Object.entries(query).forEach(([key, value]) => {
      url.searchParams.set(key, value);
    });
    return toWebSocketUrl(url);
  },
  login(username: string, password: string): Promise<{ access_token: string }> {
    return request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
  },
  getOverview(token: string): Promise<Overview> {
    return request("/dashboard/api/overview", {}, token);
  },
  listDevices(token: string): Promise<Device[]> {
    return request("/dashboard/api/devices", {}, token);
  },
  getDevice(token: string, deviceId: string): Promise<Device> {
    return request(`/dashboard/api/devices/${deviceId}`, {}, token);
  },
  createDevice(
    token: string,
    payload: {
      device_id: string;
      name: string;
      type: string;
      device_key?: string;
    },
  ): Promise<Device> {
    return request(
      "/dashboard/api/devices",
      { method: "POST", body: JSON.stringify(payload) },
      token,
    );
  },
  updateDevice(
    token: string,
    deviceId: string,
    payload: { name?: string; type?: string; device_key?: string },
  ): Promise<Device> {
    return request(
      `/dashboard/api/devices/${deviceId}`,
      { method: "PUT", body: JSON.stringify(payload) },
      token,
    );
  },
  deleteDevice(token: string, deviceId: string): Promise<void> {
    return request(`/dashboard/api/devices/${deviceId}`, { method: "DELETE" }, token);
  },
  downloadClientPackage(
    token: string,
    payload: {
      device_id: string;
      name: string;
      device_key?: string;
      gateway_url: string;
      repo_url: string;
      repo_ref: string;
      network_profile: "global" | "cn";
      skill_ids: string[];
    },
  ): Promise<{ blob: Blob; filename: string | null }> {
    return requestFile(
      "/dashboard/api/client-packages",
      { method: "POST", body: JSON.stringify(payload) },
      token,
    );
  },
  getQuickDeployDraft(token: string): Promise<QuickDeployDraft> {
    return request("/dashboard/api/quick-deploy/draft", {}, token);
  },
  downloadQuickDeployPackage(
    token: string,
    payload: {
      targets: QuickDeployModuleId[];
      modules: Record<QuickDeployModuleId, Record<string, string>>;
      client_package: {
        device_name: string;
        repo_url: string;
        repo_ref: string;
        register_device: boolean;
        skill_ids: string[];
      };
    },
  ): Promise<{ blob: Blob; filename: string | null }> {
    return requestFile(
      "/dashboard/api/quick-deploy/package",
      { method: "POST", body: JSON.stringify(payload) },
      token,
    );
  },
  listSkills(token: string): Promise<Skill[]> {
    return request("/dashboard/api/skills", {}, token);
  },
  createSkill(
    token: string,
    payload: { skill_id: string; name: string; description: string; config: Record<string, unknown> },
  ): Promise<Skill> {
    return request(
      "/dashboard/api/skills",
      { method: "POST", body: JSON.stringify(payload) },
      token,
    );
  },
  updateSkill(
    token: string,
    skillId: string,
    payload: { name?: string; description?: string; config?: Record<string, unknown> },
  ): Promise<Skill> {
    return request(
      `/dashboard/api/skills/${skillId}`,
      { method: "PUT", body: JSON.stringify(payload) },
      token,
    );
  },
  deleteSkill(token: string, skillId: string): Promise<void> {
    return request(`/dashboard/api/skills/${skillId}`, { method: "DELETE" }, token);
  },
  uploadSkillArchive(token: string, skillId: string, archive: File): Promise<Skill> {
    return request(
      `/dashboard/api/skills/${skillId}/archive`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/zip",
          "X-Skill-Archive-Name": archive.name,
        },
        body: archive,
      },
      token,
    );
  },
  createTask(
    token: string,
    payload: { device_id?: string; instruction: string },
  ): Promise<Task> {
    return request(
      "/tasks",
      { method: "POST", body: JSON.stringify(payload) },
      token,
    );
  },
  assignSkill(
    token: string,
    deviceId: string,
    payload: { skill_id: string; config: Record<string, unknown> },
  ): Promise<void> {
    return request(
      `/dashboard/api/devices/${deviceId}/skills`,
      { method: "POST", body: JSON.stringify(payload) },
      token,
    );
  },
  unassignSkill(token: string, deviceId: string, skillId: string): Promise<void> {
    return request(
      `/dashboard/api/devices/${deviceId}/skills/${skillId}`,
      { method: "DELETE" },
      token,
    );
  },
  listTasks(token: string, filters: { status?: string; device_id?: string }): Promise<Task[]> {
    const params = new URLSearchParams();
    if (filters.status) {
      params.set("status", filters.status);
    }
    if (filters.device_id) {
      params.set("device_id", filters.device_id);
    }
    const suffix = params.toString() ? `?${params.toString()}` : "";
    return request(`/dashboard/api/tasks${suffix}`, {}, token);
  },
  submitTaskDecision(
    token: string,
    taskId: string,
    approved: boolean,
  ): Promise<Task> {
    return request(
      `/tasks/${taskId}/decision`,
      {
        method: "POST",
        body: JSON.stringify({ approved }),
      },
      token,
    );
  },
  deleteTask(token: string, taskId: string): Promise<void> {
    return request(`/tasks/${taskId}`, { method: "DELETE" }, token);
  },
  getSystemInfo(token: string): Promise<SystemInfo> {
    return request("/dashboard/api/system", {}, token);
  },
  listAiCallLogs(
    token: string,
    filters: { source?: string; device_id?: string; limit?: number } = {},
  ): Promise<AICallLog[]> {
    const params = new URLSearchParams();
    if (filters.source) {
      params.set("source", filters.source);
    }
    if (filters.device_id) {
      params.set("device_id", filters.device_id);
    }
    if (filters.limit) {
      params.set("limit", String(filters.limit));
    }
    const suffix = params.toString() ? `?${params.toString()}` : "";
    return request(`/dashboard/api/ai/calls${suffix}`, {}, token);
  },
  testGatewayAiConfig(
    token: string,
  ): Promise<{ provider: string; model: string; response: Record<string, unknown> }> {
    return request("/dashboard/api/ai/test/gateway", { method: "POST" }, token);
  },
  testDeviceAiConfig(
    token: string,
    deviceId: string,
  ): Promise<{ provider: string; model: string; response: Record<string, unknown> }> {
    return request(`/dashboard/api/ai/test/devices/${deviceId}`, { method: "POST" }, token);
  },
  saveGatewayAiConfig(
    token: string,
    payload: {
      provider: string;
      model: string;
      api_key: string;
      base_url?: string;
    },
  ): Promise<void> {
    return request(
      "/dashboard/api/ai/gateway",
      { method: "PUT", body: JSON.stringify(payload) },
      token,
    );
  },
  clearGatewayAiConfig(token: string): Promise<void> {
    return request("/dashboard/api/ai/gateway", { method: "DELETE" }, token);
  },
  saveDeviceAiConfig(
    token: string,
    deviceId: string,
    payload: {
      provider: string;
      model: string;
      api_key: string;
      base_url?: string;
    },
  ): Promise<void> {
    return request(
      `/dashboard/api/ai/devices/${deviceId}`,
      { method: "PUT", body: JSON.stringify(payload) },
      token,
    );
  },
  clearDeviceAiConfig(token: string, deviceId: string): Promise<void> {
    return request(`/dashboard/api/ai/devices/${deviceId}`, { method: "DELETE" }, token);
  },
};
