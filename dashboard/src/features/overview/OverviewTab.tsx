import { taskStatuses } from "../../app/model";
import { MetricCard } from "../../components/MetricCard";
import { SectionHeader } from "../../components/SectionHeader";
import { formatTaskStatus } from "../../lib/format";
import type { Overview } from "../../types";

type OverviewTabProps = {
  overview: Overview | null;
};

export function OverviewTab({ overview }: OverviewTabProps) {
  const connectedRatio = overview
    ? `${overview.connected_devices.length}/${overview.device_count || 0}`
    : "-";

  return (
    <section className="surface-grid">
      <div className="metric-strip">
        <MetricCard label="注册设备" value={overview?.device_count ?? "-"} />
        <MetricCard label="在线占比" value={connectedRatio} />
        <MetricCard label="App 连接" value={overview?.app_connections ?? "-"} />
        <MetricCard label="Skills" value={overview?.skill_count ?? "-"} />
      </div>

      <section className="panel">
        <SectionHeader eyebrow="Queue" title="任务状态分布" />
        <div className="bar-stack">
          {taskStatuses.map((status) => {
            const value = overview?.task_counts[status] ?? 0;
            const max = Math.max(
              ...Object.values(overview?.task_counts ?? { [status]: 1 }),
              1,
            );
            const width = `${Math.max((value / max) * 100, value ? 12 : 3)}%`;
            return (
              <div className="bar-row" key={status}>
                <span>{formatTaskStatus(status)}</span>
                <div className="bar-track">
                  <div className="bar-fill" style={{ width }} />
                </div>
                <strong>{value}</strong>
              </div>
            );
          })}
        </div>
      </section>

      <section className="panel">
        <SectionHeader eyebrow="Presence" title="在线设备" />
        <div className="presence-list">
          {(overview?.connected_devices ?? []).length ? (
            overview?.connected_devices.map((deviceId) => (
              <article className="presence-row" key={deviceId}>
                <div>
                  <strong>{deviceId}</strong>
                  <span>WebSocket 已连接</span>
                </div>
                <span className="live-dot solid" />
              </article>
            ))
          ) : (
            <p className="empty-copy">当前没有在线设备。</p>
          )}
        </div>
      </section>
    </section>
  );
}
