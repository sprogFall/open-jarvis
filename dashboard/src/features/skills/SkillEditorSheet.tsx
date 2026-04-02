import type { FormEvent } from "react";

import { SideSheet } from "../../components/SideSheet";
import type { SkillForm } from "../../app/model";
import { formatBytes } from "../../lib/format";

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
  const selectedArchiveName = form.archive_file?.name || form.existing_archive_filename;
  const archiveHash = form.archive_file
    ? "上传后生成"
    : form.existing_archive_sha256
      ? `${form.existing_archive_sha256.slice(0, 10)}...`
      : "未上传";

  return (
    <SideSheet
      title={mode === "create" ? "添加 Skill" : `编辑 ${form.skill_id}`}
      subtitle="上传 zip 后，Gateway 会把归档下发给已分配设备，并在本地工作目录解压成技能文件夹。"
      onClose={onClose}
    >
      <form className="stack" onSubmit={onSubmit}>
        <section className="callout">
          <h4>归档约束</h4>
          <p>zip 内必须包含 `SKILL.md`，可以直接位于根目录，也可以包在单个 Skill 文件夹内。</p>
          <p>
            设备收到分配后会将其解压到
            <code> &lt;workspace&gt;/{form.skill_id || "skill-id"}/ </code>
            。
          </p>
        </section>

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
          <span>{mode === "create" ? "上传归档 zip" : "替换归档 zip"}</span>
          <input
            accept=".zip,application/zip"
            type="file"
            onChange={(event) =>
              onChange({ archive_file: event.target.files?.[0] ?? null })
            }
          />
        </label>
        <section className="panel panel-nested">
          <div className="panel-head compact">
            <div>
              <p className="eyebrow">Archive</p>
              <h3>归档状态</h3>
            </div>
          </div>
          <div className="detail-grid">
            <div>
              <span>当前文件</span>
              <strong>{selectedArchiveName || "未选择 zip"}</strong>
            </div>
            <div>
              <span>当前大小</span>
              <strong>
                {form.archive_file
                  ? formatBytes(form.archive_file.size)
                  : formatBytes(form.existing_archive_size)}
              </strong>
            </div>
            <div>
              <span>当前校验</span>
              <strong>{archiveHash}</strong>
            </div>
            <div>
              <span>上传提示</span>
              <strong>{mode === "create" ? "创建时必须上传 zip" : "可只改配置，不替换 zip"}</strong>
            </div>
          </div>
        </section>
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
