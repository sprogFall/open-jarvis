import { useRuns } from "./hooks/useRuns";
import { usePolling } from "./hooks/usePolling";
import { useCallback } from "react";
import Sidebar from "./components/Sidebar";
import { Dashboard } from "./components/Dashboard";

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
  } = useRuns();

  // 轮询当前活跃运行的快照
  const isActive = activeRunId !== null;
  const shouldPoll =
    isActive &&
    activeRun !== null &&
    !["success", "partial", "failed", "cancelled"].includes(
      activeRun.status,
    );

  const poll = useCallback(() => {
    if (activeRunId) fetchRun(activeRunId);
  }, [activeRunId, fetchRun]);

  usePolling(poll, 2000, shouldPoll);

  return (
    <div className="flex h-screen bg-[#121212] text-[#e5e7eb] overflow-hidden">
      {/* 左侧栏 */}
      <Sidebar
        runs={runList}
        activeRunId={activeRunId}
        onSelectRun={selectRun}
      />

      {/* 主区域 */}
      <main className="flex-1 flex flex-col min-w-0 h-full">
        <Dashboard
          activeRun={activeRun}
          activeRunId={activeRunId}
          loading={loading}
          error={error}
          onSubmit={submitRequest}
        />
      </main>
    </div>
  );
}
