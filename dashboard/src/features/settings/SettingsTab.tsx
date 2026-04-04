import type { FormEvent } from "react";

import type { AIConfigSummary, Device, SystemInfo } from "../../types";
import type { DeviceAiForm, GatewayAiForm } from "../../app/model";
import { formatAiSource } from "../../lib/format";

type SettingsTabProps = {
  systemInfo: SystemInfo | null;
  devices: Device[];
  gatewayAiSummary: AIConfigSummary | null;
  deviceAiSummary: AIConfigSummary | null;
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
  gatewayAiSummary,
  deviceAiSummary,
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
  const clientAiSummaries = systemInfo?.client_ai ?? [];
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
          Gateway 配置会作为 CLI 的默认模型来源，只有在设备存在特殊要求时，才需要单独覆盖。
        </p>
      </div>

      <section className="panel panel-stack">
        <div className="panel-head">
          <div>
            <p className="eyebrow">Effective</p>
            <h4>当前生效配置</h4>
          </div>
        </div>

        <div className="system-grid">
          <article>
            <span>Gateway 供应商</span>
            <strong>{gatewayAiSummary?.provider ?? "-"}</strong>
          </article>
          <article>
            <span>Gateway 模型</span>
            <strong>{gatewayAiSummary?.model ?? "-"}</strong>
          </article>
          <article>
            <span>Gateway Base URL</span>
            <strong>{gatewayAiSummary?.base_url ?? "-"}</strong>
          </article>
          <article>
            <span>Gateway API Key（掩码）</span>
            <strong>{gatewayAiSummary?.api_key_masked ?? "-"}</strong>
          </article>
        </div>

        <div className="panel panel-nested panel-stack">
          <div className="panel-head compact">
            <div>
              <p className="eyebrow">CLI Effective</p>
              <h4>CLI 生效摘要</h4>
            </div>
          </div>
          {deviceAiSummary ? (
            <div className="system-grid">
              <article>
                <span>当前设备</span>
                <strong>{deviceAiSummary.device_id ?? deviceAiForm.device_id}</strong>
              </article>
              <article>
                <span>当前供应商</span>
                <strong>{deviceAiSummary.provider}</strong>
              </article>
              <article>
                <span>当前模型</span>
                <strong>{deviceAiSummary.model}</strong>
              </article>
              <article>
                <span>API Key（掩码）</span>
                <strong>{deviceAiSummary.api_key_masked}</strong>
              </article>
            </div>
          ) : null}
          {clientAiSummaries.length ? (
            <div className="assignment-list">
              {clientAiSummaries.map((summary) => (
                <article key={summary.device_id ?? summary.model} className="assignment-row">
                  <div>
                    <strong>{summary.device_id ?? "CLI 设备"}</strong>
                    <span>{summary.provider} · {summary.model}</span>
                    <span>
                      {formatAiSource(summary.source)} · {summary.base_url ?? "默认 Base URL"}
                    </span>
                  </div>
                  <div className="alignment-right">
                    <span>API Key（掩码）</span>
                    <strong>{summary.api_key_masked}</strong>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <p className="empty-copy">当前还没有可展示的 CLI 生效配置。</p>
          )}
        </div>
      </section>

      <form className="panel panel-stack" onSubmit={onSaveGatewayAiConfig}>
        <div className="panel-head">
          <div>
            <p className="eyebrow">Gateway</p>
            <h4>Gateway AI 默认配置</h4>
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
            保存 Gateway 默认
          </button>
          <button className="ghost-button" onClick={onClearGatewayAiConfig} type="button">
            清除默认
          </button>
        </div>
      </form>

      <form className="panel panel-stack" onSubmit={onSaveDeviceAiConfig}>
        <div className="panel-head">
          <div>
            <p className="eyebrow">CLI</p>
            <h4>CLI 特殊覆盖</h4>
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

        {deviceAiSummary ? (
          <div className="system-grid">
            <article>
              <span>当前供应商</span>
              <strong>{deviceAiSummary.provider}</strong>
            </article>
            <article>
              <span>当前模型</span>
              <strong>{deviceAiSummary.model}</strong>
            </article>
            <article>
              <span>当前来源</span>
              <strong>{formatAiSource(deviceAiSummary.source)}</strong>
            </article>
            <article>
              <span>API Key（掩码）</span>
              <strong>{deviceAiSummary.api_key_masked}</strong>
            </article>
          </div>
        ) : null}

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
