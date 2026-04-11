import type { FormEvent } from "react";

import { SideSheet } from "../../components/SideSheet";
import { FormField } from "../../components/FormField";
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
      subtitle="填写设备基本信息。"
      onClose={onClose}
    >
      <form className="stack" onSubmit={onSubmit}>
        <FormField htmlFor="device-editor-id" label="设备 ID">
          <input
            disabled={mode === "edit"}
            id="device-editor-id"
            value={form.device_id}
            onChange={(event) => onChange({ device_id: event.target.value })}
          />
        </FormField>
        <FormField htmlFor="device-editor-name" label="名称">
          <input
            id="device-editor-name"
            value={form.name}
            onChange={(event) => onChange({ name: event.target.value })}
          />
        </FormField>
        <FormField htmlFor="device-editor-type" label="类型">
          <select
            id="device-editor-type"
            value={form.type}
            onChange={(event) => onChange({ type: event.target.value })}
          >
            <option value="cli">CLI</option>
            <option value="app">App</option>
          </select>
        </FormField>
        <FormField htmlFor="device-editor-key" label="设备密钥">
          <input
            id="device-editor-key"
            placeholder={mode === "create" ? "留空自动生成" : "留空保持现有密钥"}
            value={form.device_key}
            onChange={(event) => onChange({ device_key: event.target.value })}
          />
        </FormField>
        {error ? <p className="error-text">{error}</p> : null}
        <button className="primary-button" type="submit">
          {mode === "create" ? "创建设备" : "保存变更"}
        </button>
      </form>
    </SideSheet>
  );
}
