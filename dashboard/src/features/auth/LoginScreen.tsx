import type { FormEvent } from "react";

type LoginScreenProps = {
  loginPending: boolean;
  loginError: string | null;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
};

export function LoginScreen({
  loginPending,
  loginError,
  onSubmit,
}: LoginScreenProps) {
  return (
    <main className="login-scene">
      <section className="login-poster">
        <p className="eyebrow">OpenJarvis Control Plane</p>
        <h1>任务、设备、技能统一控制台</h1>
        <p className="poster-copy">
          统一查看任务、设备与技能状态，处理审批、跟踪执行过程，并保持三端协作闭环。
        </p>
        <div className="poster-grid">
          <div>
            <span>任务协同</span>
            <strong>下发、审批、恢复</strong>
          </div>
          <div>
            <span>执行范围</span>
            <strong>设备、Skills、实时日志</strong>
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
