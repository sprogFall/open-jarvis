import { useState, useCallback } from "react";
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

  const fetchRun = useCallback(async (runId: string) => {
    try {
      const snapshot = await getRun(runId);
      if (snapshot.status === "not_found") {
        setActiveRun(null);
        setError("该运行记录已不可用，可能是服务已重启。");
        return null;
      }
      setActiveRun(snapshot);
      setRunList((prev) => {
        const next = prev.map((run) =>
          run.run_id === runId ? { ...run, status: snapshot.status } : run,
        );
        saveRunList(next);
        return next;
      });
      return snapshot;
    } catch (cause: unknown) {
      setError(cause instanceof Error ? cause.message : "无法获取运行状态");
      return null;
    }
  }, []);

  const startNewSession = useCallback(() => {
    setActiveRunId(null);
    setActiveRun(null);
    setError(null);
  }, []);

  const submitRequest = useCallback(async (userRequest: string) => {
    setLoading(true);
    setError(null);
    setActiveRun(null);
    try {
      const response = await createRun(userRequest);
      const item: RunListItem = {
        run_id: response.run_id,
        user_request: userRequest,
        status: response.status,
        created_at: new Date().toISOString(),
      };
      setRunList((prev) => {
        const next = [item, ...prev.filter((run) => run.run_id !== item.run_id)];
        saveRunList(next);
        return next;
      });
      setActiveRunId(response.run_id);
      await fetchRun(response.run_id);
      return response.run_id;
    } catch (cause: unknown) {
      setError(cause instanceof Error ? cause.message : "创建运行失败");
      return null;
    } finally {
      setLoading(false);
    }
  }, [fetchRun]);

  const selectRun = useCallback(async (runId: string) => {
    setActiveRunId(runId);
    setActiveRun(null);
    setError(null);
    await fetchRun(runId);
  }, [fetchRun]);

  return {
    runList,
    activeRunId,
    activeRun,
    loading,
    error,
    submitRequest,
    fetchRun,
    selectRun,
    startNewSession,
  };
}
