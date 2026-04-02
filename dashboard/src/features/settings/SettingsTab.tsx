import type { SystemInfo } from "../../types";

type SettingsTabProps = {
  systemInfo: SystemInfo | null;
};

export function SettingsTab({ systemInfo }: SettingsTabProps) {
  const configuredDevices = systemInfo?.configured_devices ?? [];

  return (
    <section className="panel panel-stack">
      <div className="panel-head">
        <div>
          <p className="eyebrow">System</p>
          <h3>运行信息</h3>
        </div>
      </div>
      <div className="system-grid">
        <article>
          <span>操作账号</span>
          <strong>{systemInfo?.admin_username ?? "-"}</strong>
        </article>
        <article>
          <span>已配置设备数</span>
          <strong>{configuredDevices.length || "-"}</strong>
        </article>
        <article>
          <span>设备范围</span>
          <strong>{configuredDevices.join(", ") || "-"}</strong>
        </article>
        <article>
          <span>当前焦点</span>
          <strong>任务跟踪、设备管理、Skill 分配</strong>
        </article>
      </div>
      <div className="callout">
        <p className="eyebrow">Operations</p>
        <h4>业务配置与账号范围</h4>
        <p>
          当前控制台聚焦任务流转、设备接入和 Skill 管理。
          {configuredDevices.length
            ? ` 已纳管设备：${configuredDevices.join(", ")}。`
            : " 当前还没有纳管设备。"}
        </p>
      </div>
    </section>
  );
}
