export function parseJsonInput(raw: string): Record<string, unknown> {
  if (!raw.trim()) {
    return {};
  }
  const parsed = JSON.parse(raw);
  if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") {
    throw new Error("配置必须是 JSON 对象");
  }
  return parsed as Record<string, unknown>;
}
