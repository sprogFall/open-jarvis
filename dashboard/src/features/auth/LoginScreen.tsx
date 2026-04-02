import type { FormEvent } from "react";

type LoginScreenProps = {
  gatewayLabel: string;
  loginPending: boolean;
  loginError: string | null;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
};

export function LoginScreen({
  gatewayLabel,
  loginPending,
  loginError,
  onSubmit,
}: LoginScreenProps) {
  return (
    <main className="login-scene">
      <section className="login-poster">
        <p className="eyebrow">OpenJarvis Control Plane</p>
        <h1>纯前端部署的运维面板</h1>
        <p className="poster-copy">
          使用 Nginx 托管静态资源，通过 JWT 与网关 API 交互，保留设备、Skill 与任务的统一控制面。
        </p>
        <div className="poster-grid">
          <div>
            <span>Build</span>
            <strong>dist / static</strong>
          </div>
          <div>
            <span>Runtime</span>
            <strong>{gatewayLabel}</strong>
          </div>
        </div>
      </section>

      <section className="login-card">
        <p className="eyebrow">Operator Access</p>
        <h2>登录 Dashboard</h2>
        <form className="stack" onSubmit={onSubmit}>
          <label className="field">
            <span>用户名</span>
            <input name="username" defaultValue="operator" placeholder="operator" />
          </label>
          <label className="field">
            <span>密码</span>
            <input name="password" type="password" placeholder="passw0rd" />
          </label>
          {loginError ? <p className="error-text">{loginError}</p> : null}
          <button className="primary-button" disabled={loginPending} type="submit">
            {loginPending ? "登录中..." : "进入控制台"}
          </button>
        </form>
      </section>
    </main>
  );
}
