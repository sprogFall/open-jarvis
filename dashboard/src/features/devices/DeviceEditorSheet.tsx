import type { FormEvent } from "react";

import { SideSheet } from "../../components/SideSheet";
import type { DeviceForm } from "../../app/model";

type DeviceEditorSheetProps = {
  mode: "create" | "edit";
  form: DeviceForm;
  error: string | null;
  onClose: () => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onChange: (patch: Partial<DeviceForm>) => void;
};

export function DeviceEditorSheet({
  mode,
  form,
  error,
  onClose,
  onSubmit,
  onChange,
}: DeviceEditorSheetProps) {
  return (
    <SideSheet
      title={mode === "create" ? "添加设备" : `编辑 ${form.device_id}`}
      subtitle="设备注册信息会直接写入网关持久化存储。"
      onClose={onClose}
    >
      <form className="stack" onSubmit={onSubmit}>
        <label className="field">
          <span>设备 ID</span>
          <input
            disabled={mode === "edit"}
            value={form.device_id}
            onChange={(event) => onChange({ device_id: event.target.value })}
          />
        </label>
        <label className="field">
          <span>名称</span>
          <input
            value={form.name}
            onChange={(event) => onChange({ name: event.target.value })}
          />
        </label>
        <label className="field">
          <span>类型</span>
          <select
            value={form.type}
            onChange={(event) => onChange({ type: event.target.value })}
          >
            <option value="cli">CLI</option>
            <option value="app">App</option>
          </select>
        </label>
        <label className="field">
          <span>设备密钥</span>
          <input
            placeholder={mode === "create" ? "留空自动生成" : ""}
            value={form.device_key}
            onChange={(event) => onChange({ device_key: event.target.value })}
          />
        </label>
        {error ? <p className="error-text">{error}</p> : null}
        <button className="primary-button" type="submit">
          {mode === "create" ? "创建设备" : "保存变更"}
        </button>
      </form>
    </SideSheet>
  );
}
