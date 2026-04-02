import { useState } from "react";
import type { FormEvent } from "react";

import { dashboardApi } from "./api";
import { AppShell } from "./app/AppShell";
import { LoginScreen } from "./features/auth/LoginScreen";
import { getErrorMessage } from "./lib/format";
import {
  clearStoredToken,
  readStoredToken,
  storeToken,
} from "./lib/storage";

export default function App() {
  const [token, setToken] = useState<string | null>(readStoredToken());
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loginPending, setLoginPending] = useState(false);

  async function submitLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const username = String(formData.get("username") ?? "");
    const password = String(formData.get("password") ?? "");
    setLoginPending(true);
    setLoginError(null);

    try {
      const response = await dashboardApi.login(username, password);
      storeToken(response.access_token);
      setToken(response.access_token);
      setLoginError(null);
    } catch (error) {
      setLoginError(getErrorMessage(error));
    } finally {
      setLoginPending(false);
    }
  }

  function clearSession(message?: string) {
    clearStoredToken();
    setToken(null);
    setLoginError(message ?? null);
  }

  return (
    <div className="dashboard-shell">
      <div className="ambient ambient-a" />
      <div className="ambient ambient-b" />

      {!token ? (
        <LoginScreen
          gatewayLabel={dashboardApi.gatewayBaseUrl || "same-origin"}
          loginPending={loginPending}
          loginError={loginError}
          onSubmit={submitLogin}
        />
      ) : (
        <AppShell
          token={token}
          onLogout={() => clearSession()}
          onSessionExpired={clearSession}
        />
      )}
    </div>
  );
}
