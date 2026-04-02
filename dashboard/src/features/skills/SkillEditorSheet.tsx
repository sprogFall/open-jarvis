import type { FormEvent } from "react";

import { SideSheet } from "../../components/SideSheet";
import type { SkillForm } from "../../app/model";

type SkillEditorSheetProps = {
  mode: "create" | "edit";
  form: SkillForm;
  error: string | null;
  onClose: () => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onChange: (patch: Partial<SkillForm>) => void;
};

export function SkillEditorSheet({
  mode,
  form,
  error,
  onClose,
  onSubmit,
  onChange,
}: SkillEditorSheetProps) {
  return (
    <SideSheet
      title={mode === "create" ? "添加 Skill" : `编辑 ${form.skill_id}`}
      subtitle="Skill 配置会按 JSON 对象原样写入后端。"
      onClose={onClose}
    >
      <form className="stack" onSubmit={onSubmit}>
        <label className="field">
          <span>Skill ID</span>
          <input
            disabled={mode === "edit"}
            value={form.skill_id}
            onChange={(event) => onChange({ skill_id: event.target.value })}
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
          <span>描述</span>
          <textarea
            rows={3}
            value={form.description}
            onChange={(event) => onChange({ description: event.target.value })}
          />
        </label>
        <label className="field">
          <span>配置 JSON</span>
          <textarea
            rows={8}
            value={form.config}
            onChange={(event) => onChange({ config: event.target.value })}
          />
        </label>
        {error ? <p className="error-text">{error}</p> : null}
        <button className="primary-button" type="submit">
          {mode === "create" ? "创建 Skill" : "保存变更"}
        </button>
      </form>
    </SideSheet>
  );
}
