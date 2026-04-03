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
  const isBuiltin = form.source === "builtin";
  const selectedArchiveName = form.archive_file?.name || form.existing_archive_filename;
  const archiveHash = form.archive_file
    ? "上传后生成"
    : form.existing_archive_sha256
      ? `${form.existing_archive_sha256.slice(0, 10)}...`
      : "未上传";

  return (
    <SideSheet
      title={mode === "create" ? "添加 Skill" : `编辑 ${form.skill_id}`}
      subtitle={
        isBuiltin
          ? "内建 Skill 由系统预置，分配后会直接暴露给 AI 规划器。"
          : "上传 zip 后，Gateway 会把归档下发给已分配设备，并在本地工作目录解压成技能文件夹。"
      }
      onClose={onClose}
    >
      <form className="stack" onSubmit={onSubmit}>
        <section className="callout">
          <h4>{isBuiltin ? "内建能力" : "归档约束"}</h4>
          {isBuiltin ? (
            <p>内建 Skill 不需要上传归档，分配后即可被当前设备上的 AI 规划器发现与调用。</p>
          ) : (
            <>
              <p>zip 内必须包含 `SKILL.md`，可以直接位于根目录，也可以包在单个 Skill 文件夹内。</p>
              <p>
                设备收到分配后会将其解压到
                <code> &lt;workspace&gt;/{form.skill_id || "skill-id"}/ </code>
                。
              </p>
            </>
          )}
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
        {!isBuiltin ? (
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
        ) : null}
        <section className="panel panel-nested">
          <div className="panel-head compact">
            <div>
              <p className="eyebrow">{isBuiltin ? "Builtin" : "Archive"}</p>
              <h3>{isBuiltin ? "能力状态" : "归档状态"}</h3>
            </div>
          </div>
          <div className="detail-grid">
            <div>
              <span>{isBuiltin ? "来源" : "当前文件"}</span>
              <strong>{isBuiltin ? "系统预置" : selectedArchiveName || "未选择 zip"}</strong>
            </div>
            <div>
              <span>{isBuiltin ? "分配方式" : "当前大小"}</span>
              <strong>{isBuiltin
                ? "直接同步到 AI 能力目录"
                : form.archive_file
                  ? formatBytes(form.archive_file.size)
                  : formatBytes(form.existing_archive_size)}</strong>
            </div>
            <div>
              <span>{isBuiltin ? "归档" : "当前校验"}</span>
              <strong>{isBuiltin ? "不需要 zip" : archiveHash}</strong>
            </div>
            <div>
              <span>上传提示</span>
              <strong>{isBuiltin
                ? "可直接修改描述或默认配置"
                : mode === "create"
                  ? "创建时必须上传 zip"
                  : "可只改配置，不替换 zip"}</strong>
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
