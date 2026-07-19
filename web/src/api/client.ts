import type { CreateRunResponse, RunSnapshot } from "../types";

const BASE = "/api/v1";

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`HTTP ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

/** POST /runs — 创建新运行 */
export function createRun(userRequest: string): Promise<CreateRunResponse> {
  return request<CreateRunResponse>("/runs", {
    method: "POST",
    body: JSON.stringify({ user_request: userRequest }),
  });
}

/** GET /runs/{run_id} — 查询完整快照 */
export function getRun(runId: string): Promise<RunSnapshot> {
  return request<RunSnapshot>(`/runs/${runId}`);
}
