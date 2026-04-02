import { formatDate } from "../../lib/format";
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
  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Catalog</p>
          <h3>Skill 目录</h3>
        </div>
        <button className="primary-button" onClick={onCreate} type="button">
          添加 Skill
        </button>
      </div>
      <div className="table-shell">
        <table>
          <thead>
            <tr>
              <th>Skill</th>
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
