import type { Device, Overview, Skill, SystemInfo, Task } from "./types";

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

export const dashboardApi = {
  gatewayBaseUrl,
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
  getSystemInfo(token: string): Promise<SystemInfo> {
    return request("/dashboard/api/system", {}, token);
  },
};
