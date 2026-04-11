import { formatBytes, formatDate } from "../../lib/format";
import { MetricCard } from "../../components/MetricCard";
import { SectionHeader } from "../../components/SectionHeader";
import type { Skill } from "../../types";

type SkillsTabProps = {
  skills: Skill[];
  onCreate: () => void;
  onEdit: (skill: Skill) => void;
  onDelete: (skill: Skill) => void | Promise<void>;
};

export function SkillsTab({
  skills,
  onCreate,
  onEdit,
  onDelete,
}: SkillsTabProps) {
  const builtinCount = skills.filter((skill) => skill.source === "builtin").length;
  const archiveReadyCount = skills.filter(
    (skill) => skill.source === "archive" && skill.archive_ready,
  ).length;
  const archivePendingCount = skills.filter(
    (skill) => skill.source === "archive" && !skill.archive_ready,
  ).length;

  return (
    <section className="panel">
      <SectionHeader
        actions={
          <button className="primary-button" onClick={onCreate} type="button">
            添加 Skill
          </button>
        }
        description="维护内建与自定义 Skill。"
        eyebrow="Catalog"
        title="Skill 目录"
      />
      <div className="metric-strip compact-strip">
        <MetricCard label="总数" value={skills.length} />
        <MetricCard label="内建" value={builtinCount} />
        <MetricCard label="归档就绪" value={archiveReadyCount} />
        <MetricCard label="待补归档" value={archivePendingCount} />
      </div>
      <div className="table-shell">
        <table>
          <thead>
            <tr>
              <th>Skill</th>
              <th>归档</th>
              <th>描述</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {skills.map((skill) => (
              <tr key={skill.skill_id}>
                <td>
                  <strong>{skill.name}</strong>
                  <span className="cell-subtle">{skill.skill_id}</span>
                </td>
                <td>
                  {skill.source === "builtin" ? (
                    <>
                      <span className="package-pill ready">内建 Skill</span>
                      <span className="cell-subtle">
                        {skill.action_names.length
                          ? skill.action_names.join(" · ")
                          : "系统预置能力"}
                      </span>
                      <span className="cell-subtle">分配后可直接使用</span>
                    </>
                  ) : (
                    <>
                      <span className={`package-pill${skill.archive_ready ? " ready" : " pending"}`}>
                        {skill.archive_ready ? "归档已就绪" : "待上传归档"}
                      </span>
                      <span className="cell-subtle">
                        {skill.archive_filename || "未上传 zip"}
                      </span>
                      <span className="cell-subtle">
                        {skill.archive_ready
                          ? `${formatBytes(skill.archive_size)} · ${skill.archive_sha256?.slice(0, 10)}...`
                          : "上传后可分配"}
                      </span>
                    </>
                  )}
                </td>
                <td>{skill.description || "无描述"}</td>
                <td>{formatDate(skill.created_at)}</td>
                <td>
                  <div className="row-actions">
                    <button
                      className="ghost-button"
                      onClick={() => onEdit(skill)}
                      type="button"
                    >
                      编辑
                    </button>
                    {skill.source === "archive" ? (
                      <button
                        className="danger-button"
                        onClick={() => void onDelete(skill)}
                        type="button"
                      >
                        删除
                      </button>
                    ) : null}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
