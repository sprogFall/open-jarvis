import { useCallback } from "react";
import { useRuns } from "./hooks/useRuns";
import { usePolling } from "./hooks/usePolling";
import Sidebar from "./components/Sidebar";
import { Dashboard } from "./components/Dashboard";

const FINISHED_STATUSES = ["success", "partial", "failed", "cancelled", "done"];

export default function App() {
  const {
    runList,
    activeRunId,
    activeRun,
    loading,
    error,
    submitRequest,
    fetchRun,
    selectRun,
    startNewSession,
  } = useRuns();

  const shouldPoll = Boolean(
    activeRunId && activeRun && !FINISHED_STATUSES.includes(activeRun.status),
  );

  const poll = useCallback(async () => {
    if (activeRunId) await fetchRun(activeRunId);
  }, [activeRunId, fetchRun]);

  usePolling(poll, 2000, shouldPoll);

  return (
    <div className="flex h-dvh overflow-hidden bg-[#10131a] text-[#e5e7eb]">
      <Sidebar
        runs={runList}
        activeRunId={activeRunId}
        onSelectRun={selectRun}
        onNewSession={startNewSession}
      />
      <main className="flex min-w-0 flex-1 flex-col">
        <Dashboard
          activeRun={activeRun}
          activeRunId={activeRunId}
          loading={loading}
          error={error}
          onSubmit={submitRequest}
          onNewSession={startNewSession}
        />
      </main>
    </div>
  );
}
