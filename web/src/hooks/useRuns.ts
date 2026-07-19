import { useState, useCallback, useRef } from "react";
import { createRun, getRun } from "../api/client";
import type { RunSnapshot, RunListItem } from "../types";

const STORAGE_KEY = "open-jarvis-runs";

function loadRunList(): RunListItem[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveRunList(list: RunListItem[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
}

export function useRuns() {
  const [runList, setRunList] = useState<RunListItem[]>(loadRunList);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [activeRun, setActiveRun] = useState<RunSnapshot | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const submitRequest = useCallback(async (userRequest: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await createRun(userRequest);
      const item: RunListItem = {
        run_id: res.run_id,
        user_request: userRequest,
        status: "queued",
        created_at: new Date().toISOString(),
      };
      setRunList((prev) => {
        const next = [item, ...prev];
        saveRunList(next);
        return next;
      });
      setActiveRunId(res.run_id);
      return res.run_id;
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "创建失败");
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchRun = useCallback(async (runId: string) => {
    try {
      const snapshot = await getRun(runId);
      setActiveRun(snapshot);
      // 同步状态到列表
      setRunList((prev) => {
        const next = prev.map((r) =>
          r.run_id === runId ? { ...r, status: snapshot.status } : r,
        );
        saveRunList(next);
        return next;
      });
      return snapshot;
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "查询失败");
      return null;
    }
  }, []);

  const selectRun = useCallback(
    async (runId: string) => {
      setActiveRunId(runId);
      setError(null);
      await fetchRun(runId);
    },
    [fetchRun],
  );

  return {
    runList,
    activeRunId,
    activeRun,
    loading,
    error,
    submitRequest,
    fetchRun,
    selectRun,
    setError,
  };
}
