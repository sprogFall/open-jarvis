import type { FormEvent } from "react";

import { FormField } from "../../components/FormField";
import { KeyValueGrid } from "../../components/KeyValueGrid";
import { SectionHeader } from "../../components/SectionHeader";
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
  gatewayAiTestMessage: string | null;
  deviceAiForm: DeviceAiForm;
  deviceAiError: string | null;
  deviceAiTestMessage: string | null;
  onGatewayAiChange: (patch: Partial<GatewayAiForm>) => void;
  onDeviceAiChange: (patch: Partial<DeviceAiForm>) => void;
  onSaveGatewayAiConfig: (event: FormEvent<HTMLFormElement>) => void;
  onSaveDeviceAiConfig: (event: FormEvent<HTMLFormElement>) => void;
  onClearGatewayAiConfig: () => void;
  onClearDeviceAiConfig: () => void;
  onTestGatewayAiConfig: () => void;
  onTestDeviceAiConfig: () => void;
};

export function SettingsTab({
  systemInfo,
  devices,
  gatewayAiSummary,
  deviceAiSummary,
  gatewayAiForm,
  gatewayAiError,
  gatewayAiTestMessage,
  deviceAiForm,
  deviceAiError,
  deviceAiTestMessage,
  onGatewayAiChange,
  onDeviceAiChange,
  onSaveGatewayAiConfig,
  onSaveDeviceAiConfig,
  onClearGatewayAiConfig,
  onClearDeviceAiConfig,
  onTestGatewayAiConfig,
  onTestDeviceAiConfig,
}: SettingsTabProps) {
  const configuredDevices = systemInfo?.configured_devices ?? [];
  const clientAiSummaries = systemInfo?.client_ai ?? [];
  const clientDevices = devices.filter((device) => device.type === "cli");

  return (
    <section className="panel panel-stack">
      <SectionHeader eyebrow="System" title="运行信息" />
      <KeyValueGrid
        items={[
          { label: "操作账号", value: systemInfo?.admin_username ?? "-" },
          { label: "已配置设备数", value: configuredDevices.length || "-" },
          { label: "设备范围", value: configuredDevices.join(", ") || "-" },
          { label: "当前焦点", value: "任务跟踪、设备管理、Skill 分配" },
        ]}
      />
      <div className="callout">
        <p className="eyebrow">Operations</p>
        <h4>业务配置与账号范围</h4>
        <p>
          Gateway 配置会作为 CLI 的默认模型来源，只有在设备存在特殊要求时，才需要单独覆盖。
        </p>
      </div>

      <section className="panel panel-stack">
        <SectionHeader eyebrow="Effective" title="当前生效配置" titleAs="h4" />

        <KeyValueGrid
          items={[
            { label: "Gateway 供应商", value: gatewayAiSummary?.provider ?? "-" },
            { label: "Gateway 模型", value: gatewayAiSummary?.model ?? "-" },
            { label: "Gateway Base URL", value: gatewayAiSummary?.base_url ?? "-" },
            {
              label: "Gateway API Key（掩码）",
              value: gatewayAiSummary?.api_key_masked ?? "-",
            },
          ]}
        />
        <div className="row-actions">
          <button className="ghost-button" onClick={onTestGatewayAiConfig} type="button">
            测试当前默认
          </button>
        </div>
        {gatewayAiTestMessage ? <div className="callout"><p>{gatewayAiTestMessage}</p></div> : null}

        <div className="panel panel-nested panel-stack">
          <SectionHeader compact eyebrow="CLI Effective" title="CLI 生效摘要" titleAs="h4" />
          {deviceAiSummary ? (
            <KeyValueGrid
              items={[
                {
                  label: "当前设备",
                  value: deviceAiSummary.device_id ?? deviceAiForm.device_id,
                },
                { label: "当前供应商", value: deviceAiSummary.provider },
                { label: "当前模型", value: deviceAiSummary.model },
                { label: "API Key（掩码）", value: deviceAiSummary.api_key_masked },
              ]}
            />
          ) : null}
          <div className="row-actions">
            <button className="ghost-button" onClick={onTestDeviceAiConfig} type="button">
              测试当前设备配置
            </button>
          </div>
          {deviceAiTestMessage ? <div className="callout"><p>{deviceAiTestMessage}</p></div> : null}
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
        <SectionHeader eyebrow="Gateway" title="Gateway AI 默认配置" titleAs="h4" />
        <FormField htmlFor="gateway-ai-provider" label="供应商">
          <input
            id="gateway-ai-provider"
            value={gatewayAiForm.provider}
            onChange={(event) => onGatewayAiChange({ provider: event.target.value })}
            placeholder="openai / anthropic / custom"
          />
        </FormField>
        <FormField htmlFor="gateway-ai-model" label="模型">
          <input
            id="gateway-ai-model"
            value={gatewayAiForm.model}
            onChange={(event) => onGatewayAiChange({ model: event.target.value })}
            placeholder="gpt-4o-mini"
          />
        </FormField>
        <FormField htmlFor="gateway-ai-key" label="API Key">
          <input
            id="gateway-ai-key"
            type="password"
            value={gatewayAiForm.api_key}
            onChange={(event) => onGatewayAiChange({ api_key: event.target.value })}
            placeholder="sk-..."
          />
        </FormField>
        <FormField htmlFor="gateway-ai-base-url" label="Base URL（可选）">
          <input
            id="gateway-ai-base-url"
            value={gatewayAiForm.base_url}
            onChange={(event) => onGatewayAiChange({ base_url: event.target.value })}
            placeholder="https://llm.example/v1/chat/completions"
          />
        </FormField>
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
        <SectionHeader eyebrow="CLI" title="CLI 特殊覆盖" titleAs="h4" />
        <FormField htmlFor="device-ai-device-id" label="目标设备">
          <select
            id="device-ai-device-id"
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
        </FormField>

        {deviceAiSummary ? (
          <KeyValueGrid
            items={[
              { label: "当前供应商", value: deviceAiSummary.provider },
              { label: "当前模型", value: deviceAiSummary.model },
              {
                label: "当前来源",
                value: formatAiSource(deviceAiSummary.source),
              },
              { label: "API Key（掩码）", value: deviceAiSummary.api_key_masked },
            ]}
          />
        ) : null}

        <FormField htmlFor="device-ai-provider" label="供应商">
          <input
            id="device-ai-provider"
            value={deviceAiForm.provider}
            onChange={(event) => onDeviceAiChange({ provider: event.target.value })}
            placeholder="custom / openai / anthropic"
          />
        </FormField>
        <FormField htmlFor="device-ai-model" label="模型">
          <input
            id="device-ai-model"
            value={deviceAiForm.model}
            onChange={(event) => onDeviceAiChange({ model: event.target.value })}
            placeholder="deepseek-chat"
          />
        </FormField>
        <FormField htmlFor="device-ai-key" label="API Key">
          <input
            id="device-ai-key"
            type="password"
            value={deviceAiForm.api_key}
            onChange={(event) => onDeviceAiChange({ api_key: event.target.value })}
            placeholder="sk-..."
          />
        </FormField>
        <FormField htmlFor="device-ai-base-url" label="Base URL（可选）">
          <input
            id="device-ai-base-url"
            value={deviceAiForm.base_url}
            onChange={(event) => onDeviceAiChange({ base_url: event.target.value })}
            placeholder="https://llm.example/v1/chat/completions"
          />
        </FormField>
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
