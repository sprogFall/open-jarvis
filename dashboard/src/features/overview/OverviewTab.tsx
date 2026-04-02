import { taskStatuses } from "../../app/model";
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
        <article>
          <span>注册设备</span>
          <strong>{overview?.device_count ?? "-"}</strong>
        </article>
        <article>
          <span>在线占比</span>
          <strong>{connectedRatio}</strong>
        </article>
        <article>
          <span>App 连接</span>
          <strong>{overview?.app_connections ?? "-"}</strong>
        </article>
        <article>
          <span>Skills</span>
          <strong>{overview?.skill_count ?? "-"}</strong>
        </article>
      </div>

      <section className="panel">
        <div className="panel-head">
          <div>
            <p className="eyebrow">Queue</p>
            <h3>任务状态分布</h3>
          </div>
        </div>
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
        <div className="panel-head">
          <div>
            <p className="eyebrow">Presence</p>
            <h3>在线设备</h3>
          </div>
        </div>
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
