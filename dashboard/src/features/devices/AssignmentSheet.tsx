import type { FormEvent } from "react";

import { SideSheet } from "../../components/SideSheet";
import type { AssignmentForm } from "../../app/model";
import type { Device, DeviceSkill, Skill } from "../../types";

type AssignmentSheetProps = {
  device: Device;
  skills: Skill[];
  form: AssignmentForm;
  error: string | null;
  onClose: () => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onChange: (patch: Partial<AssignmentForm>) => void;
  onRemove: (skill: DeviceSkill) => void | Promise<void>;
};

export function AssignmentSheet({
  device,
  skills,
  form,
  error,
  onClose,
  onSubmit,
  onChange,
  onRemove,
}: AssignmentSheetProps) {
  return (
    <SideSheet
      title={`分配 Skill · ${device.device_id}`}
      subtitle="已分配的 Skill 会立即进入设备能力清单。"
      onClose={onClose}
    >
      <div className="stack">
        <div className="inline-metadata">
          <div>
            <span>设备名称</span>
            <strong>{device.name}</strong>
          </div>
          <div>
            <span>当前状态</span>
            <strong>{device.connected ? "在线" : "离线"}</strong>
          </div>
        </div>

        <form className="stack" onSubmit={onSubmit}>
          <label className="field">
            <span>选择 Skill</span>
            <select
              value={form.skill_id}
              onChange={(event) => onChange({ skill_id: event.target.value })}
            >
              {skills.map((skill) => (
                <option key={skill.skill_id} value={skill.skill_id}>
                  {skill.name} ({skill.skill_id})
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>分配配置 JSON</span>
            <textarea
              rows={6}
              value={form.config}
              onChange={(event) => onChange({ config: event.target.value })}
            />
          </label>
          {error ? <p className="error-text">{error}</p> : null}
          <button className="primary-button" disabled={!skills.length} type="submit">
            分配 Skill
          </button>
        </form>

        <section className="panel panel-nested">
          <div className="panel-head compact">
            <div>
              <p className="eyebrow">Attached</p>
              <h3>已分配 Skill</h3>
            </div>
          </div>
          {(device.skills ?? []).length ? (
            <div className="assignment-list">
              {(device.skills ?? []).map((skill) => (
                <article key={skill.skill_id} className="assignment-row">
                  <div>
                    <strong>{skill.name || skill.skill_id}</strong>
                    <span>{skill.description || skill.skill_id}</span>
                  </div>
                  <button
                    className="danger-button"
                    onClick={() => void onRemove(skill)}
                    type="button"
                  >
                    移除
                  </button>
                </article>
              ))}
            </div>
          ) : (
            <p className="empty-copy">当前没有为该设备分配 Skill。</p>
          )}
        </section>
      </div>
    </SideSheet>
  );
}
