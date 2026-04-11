import type { FormEvent } from "react";

import { KeyValueGrid } from "../../components/KeyValueGrid";
import { SideSheet } from "../../components/SideSheet";
import { FormField } from "../../components/FormField";
import { SectionHeader } from "../../components/SectionHeader";
import type { AssignmentForm } from "../../app/model";
import { formatBytes } from "../../lib/format";
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
  const readySkills = skills.filter(
    (skill) => skill.source === "builtin" || skill.archive_ready,
  );

  return (
    <SideSheet
      title={`分配 Skill · ${device.device_id}`}
      subtitle="选择 Skill 并填写分配参数。"
      onClose={onClose}
    >
      <div className="stack">
        <KeyValueGrid
          items={[
            { label: "设备名称", value: device.name },
            { label: "当前状态", value: device.connected ? "在线" : "离线" },
          ]}
        />

        <form className="stack" onSubmit={onSubmit}>
          <FormField htmlFor="assignment-skill-id" label="选择 Skill">
            <select
              id="assignment-skill-id"
              value={readySkills.length ? form.skill_id : ""}
              onChange={(event) => onChange({ skill_id: event.target.value })}
            >
              {readySkills.map((skill) => (
                <option key={skill.skill_id} value={skill.skill_id}>
                  {skill.name} ({skill.skill_id})
                </option>
              ))}
            </select>
          </FormField>
          {!readySkills.length ? (
            <p className="error-text">当前没有可分配的 Skill。</p>
          ) : null}
          <FormField htmlFor="assignment-config" label="分配配置 JSON">
            <textarea
              id="assignment-config"
              rows={6}
              value={form.config}
              onChange={(event) => onChange({ config: event.target.value })}
            />
          </FormField>
          {error ? <p className="error-text">{error}</p> : null}
          <button className="primary-button" disabled={!readySkills.length} type="submit">
            分配 Skill
          </button>
        </form>

        <section className="panel panel-nested">
          <SectionHeader compact eyebrow="Attached" title="已分配 Skill" />
          {(device.skills ?? []).length ? (
            <div className="assignment-list">
              {(device.skills ?? []).map((skill) => (
                <article key={skill.skill_id} className="assignment-row">
                  <div>
                    <strong>{skill.name || skill.skill_id}</strong>
                    <span>{skill.description || skill.skill_id}</span>
                    <span>
                      {skill.source === "builtin"
                        ? skill.action_names?.join(" · ") || "内建能力"
                        : skill.archive_filename
                          ? `${skill.archive_filename} · ${formatBytes(skill.archive_size)}`
                          : "待准备"}
                    </span>
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
