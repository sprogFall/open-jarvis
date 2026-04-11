import type { FormEvent } from "react";

import { FormField } from "../../components/FormField";
import { KeyValueGrid } from "../../components/KeyValueGrid";
import { SectionHeader } from "../../components/SectionHeader";
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
          ? "维护内建 Skill 信息。"
          : "上传归档并维护 Skill 信息。"
      }
      onClose={onClose}
    >
      <form className="stack" onSubmit={onSubmit}>
        <section className="callout">
          <h4>{isBuiltin ? "使用方式" : "上传要求"}</h4>
          {isBuiltin ? (
            <p>内建 Skill 无需上传归档，可直接分配给设备。</p>
          ) : (
            <>
              <p>zip 内需包含 `SKILL.md`。</p>
              <p>上传完成后即可分配到设备。</p>
            </>
          )}
        </section>

        <FormField htmlFor="skill-editor-id" label="Skill ID">
          <input
            disabled={mode === "edit"}
            id="skill-editor-id"
            value={form.skill_id}
            onChange={(event) => onChange({ skill_id: event.target.value })}
          />
        </FormField>
        <FormField htmlFor="skill-editor-name" label="名称">
          <input
            id="skill-editor-name"
            value={form.name}
            onChange={(event) => onChange({ name: event.target.value })}
          />
        </FormField>
        <FormField htmlFor="skill-editor-description" label="描述">
          <textarea
            id="skill-editor-description"
            rows={3}
            value={form.description}
            onChange={(event) => onChange({ description: event.target.value })}
          />
        </FormField>
        {!isBuiltin ? (
          <FormField
            htmlFor="skill-editor-archive"
            label={mode === "create" ? "上传归档 zip" : "替换归档 zip"}
          >
            <input
              accept=".zip,application/zip"
              id="skill-editor-archive"
              type="file"
              onChange={(event) =>
                onChange({ archive_file: event.target.files?.[0] ?? null })
              }
            />
          </FormField>
        ) : null}
        <section className="panel panel-nested">
          <SectionHeader
            compact
            eyebrow={isBuiltin ? "Builtin" : "Archive"}
            title={isBuiltin ? "能力状态" : "归档状态"}
          />
          <KeyValueGrid
            items={[
              {
                label: isBuiltin ? "来源" : "当前文件",
                value: isBuiltin ? "系统预置" : selectedArchiveName || "未选择 zip",
              },
              {
                label: isBuiltin ? "分配方式" : "当前大小",
                value: isBuiltin
                  ? "分配后可用"
                  : form.archive_file
                    ? formatBytes(form.archive_file.size)
                    : formatBytes(form.existing_archive_size),
              },
              {
                label: isBuiltin ? "归档" : "当前校验",
                value: isBuiltin ? "不需要 zip" : archiveHash,
              },
              {
                label: "上传提示",
                value: isBuiltin
                  ? "可直接修改描述或默认配置"
                  : mode === "create"
                    ? "创建时必须上传 zip"
                    : "可只改配置，不替换 zip",
              },
            ]}
          />
        </section>
        <FormField htmlFor="skill-editor-config" label="配置 JSON">
          <textarea
            id="skill-editor-config"
            rows={8}
            value={form.config}
            onChange={(event) => onChange({ config: event.target.value })}
          />
        </FormField>
        {error ? <p className="error-text">{error}</p> : null}
        <button className="primary-button" type="submit">
          {mode === "create" ? "创建 Skill" : "保存变更"}
        </button>
      </form>
    </SideSheet>
  );
}
