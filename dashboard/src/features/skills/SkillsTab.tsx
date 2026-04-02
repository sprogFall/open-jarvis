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
  const readyCount = skills.filter((skill) => skill.archive_ready).length;

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Catalog</p>
          <h3>Skill 目录</h3>
          <p className="muted">Skills 以 zip 归档上传，分配给设备后会被同步并解压为本地文件夹。</p>
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
          <span>归档就绪</span>
          <strong>{readyCount}</strong>
        </article>
        <article>
          <span>待补归档</span>
          <strong>{skills.length - readyCount}</strong>
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
                    <button
                      className="danger-button"
                      onClick={() => void onDelete(skill)}
                      type="button"
                    >
                      删除
                    </button>
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
