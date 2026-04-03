import { formatBytes, formatDate } from "../../lib/format";
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
      <div className="panel-head">
        <div>
          <p className="eyebrow">Catalog</p>
          <h3>Skill 目录</h3>
          <p className="muted">内建 Skills 可直接分配给设备，自定义 Skills 通过 zip 归档上传后同步。</p>
        </div>
        <button className="primary-button" onClick={onCreate} type="button">
          添加 Skill
        </button>
      </div>
      <div className="metric-strip compact-strip">
        <article>
          <span>总数</span>
          <strong>{skills.length}</strong>
        </article>
        <article>
          <span>内建</span>
          <strong>{builtinCount}</strong>
        </article>
        <article>
          <span>归档就绪</span>
          <strong>{archiveReadyCount}</strong>
        </article>
        <article>
          <span>待补归档</span>
          <strong>{archivePendingCount}</strong>
        </article>
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
                      <span className="cell-subtle">分配后可直接被 AI 调用</span>
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
                          : "上传后才可分配给设备"}
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
