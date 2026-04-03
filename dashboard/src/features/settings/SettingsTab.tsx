import type { FormEvent } from "react";

import type { Device, SystemInfo } from "../../types";
import type { DeviceAiForm, GatewayAiForm } from "../../app/model";

type SettingsTabProps = {
  systemInfo: SystemInfo | null;
  devices: Device[];
  gatewayAiForm: GatewayAiForm;
  gatewayAiError: string | null;
  deviceAiForm: DeviceAiForm;
  deviceAiError: string | null;
  onGatewayAiChange: (patch: Partial<GatewayAiForm>) => void;
  onDeviceAiChange: (patch: Partial<DeviceAiForm>) => void;
  onSaveGatewayAiConfig: (event: FormEvent<HTMLFormElement>) => void;
  onSaveDeviceAiConfig: (event: FormEvent<HTMLFormElement>) => void;
  onClearGatewayAiConfig: () => void;
  onClearDeviceAiConfig: () => void;
};

export function SettingsTab({
  systemInfo,
  devices,
  gatewayAiForm,
  gatewayAiError,
  deviceAiForm,
  deviceAiError,
  onGatewayAiChange,
  onDeviceAiChange,
  onSaveGatewayAiConfig,
  onSaveDeviceAiConfig,
  onClearGatewayAiConfig,
  onClearDeviceAiConfig,
}: SettingsTabProps) {
  const configuredDevices = systemInfo?.configured_devices ?? [];
  const clientDevices = devices.filter((device) => device.type === "cli");

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
      <form className="panel panel-stack" onSubmit={onSaveGatewayAiConfig}>
        <div className="panel-head">
          <div>
            <p className="eyebrow">Gateway</p>
            <h4>Gateway AI 覆盖</h4>
          </div>
        </div>
        <label className="field">
          <span>供应商</span>
          <input
            value={gatewayAiForm.provider}
            onChange={(event) => onGatewayAiChange({ provider: event.target.value })}
            placeholder="openai / anthropic / custom"
          />
        </label>
        <label className="field">
          <span>模型</span>
          <input
            value={gatewayAiForm.model}
            onChange={(event) => onGatewayAiChange({ model: event.target.value })}
            placeholder="gpt-4o-mini"
          />
        </label>
        <label className="field">
          <span>API Key</span>
          <input
            type="password"
            value={gatewayAiForm.api_key}
            onChange={(event) => onGatewayAiChange({ api_key: event.target.value })}
            placeholder="sk-..."
          />
        </label>
        <label className="field">
          <span>Base URL（可选）</span>
          <input
            value={gatewayAiForm.base_url}
            onChange={(event) => onGatewayAiChange({ base_url: event.target.value })}
            placeholder="https://llm.example/v1/chat/completions"
          />
        </label>
        {gatewayAiError ? <div className="banner-error">{gatewayAiError}</div> : null}
        <div className="panel-head">
          <button className="primary-button" type="submit">
            保存 Gateway 覆盖
          </button>
          <button className="ghost-button" onClick={onClearGatewayAiConfig} type="button">
            清除覆盖
          </button>
        </div>
      </form>
      <form className="panel panel-stack" onSubmit={onSaveDeviceAiConfig}>
        <div className="panel-head">
          <div>
            <p className="eyebrow">CLI</p>
            <h4>CLI AI 覆盖</h4>
          </div>
        </div>
        <label className="field">
          <span>目标设备</span>
          <select
            value={deviceAiForm.device_id}
            onChange={(event) => onDeviceAiChange({ device_id: event.target.value })}
          >
            <option value="">请选择 CLI 设备</option>
            {clientDevices.map((device) => (
              <option key={device.device_id} value={device.device_id}>
                {device.name} ({device.device_id})
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>供应商</span>
          <input
            value={deviceAiForm.provider}
            onChange={(event) => onDeviceAiChange({ provider: event.target.value })}
            placeholder="custom / openai / anthropic"
          />
        </label>
        <label className="field">
          <span>模型</span>
          <input
            value={deviceAiForm.model}
            onChange={(event) => onDeviceAiChange({ model: event.target.value })}
            placeholder="deepseek-chat"
          />
        </label>
        <label className="field">
          <span>API Key</span>
          <input
            type="password"
            value={deviceAiForm.api_key}
            onChange={(event) => onDeviceAiChange({ api_key: event.target.value })}
            placeholder="sk-..."
          />
        </label>
        <label className="field">
          <span>Base URL（可选）</span>
          <input
            value={deviceAiForm.base_url}
            onChange={(event) => onDeviceAiChange({ base_url: event.target.value })}
            placeholder="https://llm.example/v1/chat/completions"
          />
        </label>
        {deviceAiError ? <div className="banner-error">{deviceAiError}</div> : null}
        <div className="panel-head">
          <button className="primary-button" type="submit">
            保存 CLI 覆盖
          </button>
          <button className="ghost-button" onClick={onClearDeviceAiConfig} type="button">
            清除覆盖
          </button>
        </div>
      </form>
    </section>
  );
}
