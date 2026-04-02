import type { SystemInfo } from "../../types";

type SettingsTabProps = {
  systemInfo: SystemInfo | null;
};

export function SettingsTab({ systemInfo }: SettingsTabProps) {
  return (
    <section className="panel panel-stack">
      <div className="panel-head">
        <div>
          <p className="eyebrow">System</p>
          <h3>部署信息</h3>
        </div>
      </div>
      <div className="system-grid">
        <article>
          <span>数据库</span>
          <strong>{systemInfo?.database_url ?? "-"}</strong>
        </article>
        <article>
          <span>JWT 算法</span>
          <strong>{systemInfo?.jwt_algorithm ?? "-"}</strong>
        </article>
        <article>
          <span>管理员</span>
          <strong>{systemInfo?.admin_username ?? "-"}</strong>
        </article>
        <article>
          <span>已配置设备</span>
          <strong>{systemInfo?.configured_devices.join(", ") || "-"}</strong>
        </article>
      </div>
      <div className="callout">
        <p className="eyebrow">Deployment</p>
        <h4>前端静态托管建议</h4>
        <p>
          当前推荐将 `dist/` 发布到 Nginx，并把 `/auth/`、`/dashboard/api/`
          反代到网关。
          {systemInfo?.dashboard_origins.length
            ? ` 已配置 CORS: ${systemInfo.dashboard_origins.join(", ")}`
            : " 当前未配置额外 CORS Origin。"}
        </p>
      </div>
    </section>
  );
}
