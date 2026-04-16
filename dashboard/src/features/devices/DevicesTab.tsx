import { MetricCard } from "../../components/MetricCard";
import { StatusPill } from "../../components/StatusPill";
import { SectionHeader } from "../../components/SectionHeader";
import { formatDate } from "../../lib/format";
import type { Device, Skill } from "../../types";

type DevicesTabProps = {
  devices: Device[];
  skills: Skill[];
  onCreate: () => void;
  onEdit: (device: Device) => void;
  onAssign: (deviceId: string) => void | Promise<void>;
  onDelete: (device: Device) => void | Promise<void>;
};

export function DevicesTab({
  devices,
  skills,
  onCreate,
  onEdit,
  onAssign,
  onDelete,
}: DevicesTabProps) {
  const onlineCount = devices.filter((device) => device.connected).length;
  const readySkillCount = skills.filter(
    (skill) => skill.source === "builtin" || skill.archive_ready,
  ).length;

  return (
    <section className="panel">
      <SectionHeader
        actions={
          <button className="primary-button" onClick={onCreate} type="button">
            添加设备
          </button>
        }
        eyebrow="Registry"
        title="设备清单"
      />
      <div className="metric-strip compact-strip deployment-strip">
        <MetricCard label="已登记设备" value={devices.length} detail="包含 CLI 与 App 终端" />
        <MetricCard label="在线设备" value={onlineCount} detail="当前可接收任务" />
        <MetricCard label="可分配 Skill" value={readySkillCount} detail="当前可立即分配" />
      </div>
      <div className="table-shell">
        <table>
          <thead>
            <tr>
              <th>设备</th>
              <th>类型</th>
              <th>状态</th>
              <th>最后活跃</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {devices.map((device) => (
              <tr key={device.device_id}>
                <td>
                  <strong>{device.name}</strong>
                  <span className="cell-subtle">{device.device_id}</span>
                </td>
                <td>{device.type}</td>
                <td>
                  {device.connected ? (
                    <StatusPill status="connected" active />
                  ) : (
                    <span className="status-pill status-offline">离线</span>
                  )}
                </td>
                <td>{formatDate(device.last_seen_at)}</td>
                <td>
                  <div className="row-actions">
                    <button
                      className="ghost-button"
                      onClick={() => onEdit(device)}
                      type="button"
                    >
                      编辑
                    </button>
                    <button
                      className="ghost-button"
                      onClick={() => void onAssign(device.device_id)}
                      type="button"
                    >
                      分配 Skill
                    </button>
                    <button
                      className="danger-button"
                      onClick={() => void onDelete(device)}
                      type="button"
                    >
                      删除
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
