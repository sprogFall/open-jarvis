import type { FormEvent } from "react";

import { FormField } from "../../components/FormField";
import { KeyValueGrid } from "../../components/KeyValueGrid";
import { MetricCard } from "../../components/MetricCard";
import { SideSheet } from "../../components/SideSheet";
import type { ClientDeploymentForm } from "../../app/model";
import type { Skill } from "../../types";

type ClientBootstrapSheetProps = {
  form: ClientDeploymentForm;
  skills: Skill[];
  error: string | null;
  busy: boolean;
  onClose: () => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onChange: (patch: Partial<ClientDeploymentForm>) => void;
  onToggleSkill: (skillId: string) => void;
};

const workspaceSkillIds = new Set(["builtin-filesystem", "builtin-shell"]);
const dockerSkillIds = new Set(["builtin-docker"]);

function buildMountLabels(skillIds: string[]): string[] {
  const labels: string[] = [];
  if (skillIds.some((skillId) => workspaceSkillIds.has(skillId))) {
    labels.push("/workspace");
  }
  if (skillIds.some((skillId) => dockerSkillIds.has(skillId))) {
    labels.push("docker.sock");
  }
  return labels;
}

export function ClientBootstrapSheet({
  form,
  skills,
  error,
  busy,
  onClose,
  onSubmit,
  onChange,
  onToggleSkill,
}: ClientBootstrapSheetProps) {
  const readySkills = skills.filter((skill) => skill.source === "builtin" || skill.archive_ready);
  const selectedSkills = readySkills.filter((skill) => form.skill_ids.includes(skill.skill_id));
  const mountLabels = buildMountLabels(form.skill_ids);

  return (
    <SideSheet
      title="生成 Client 部署包"
      subtitle="填写设备与接入信息后，系统会登记设备、绑定 Skill，并输出可直接下载的压缩包。"
      onClose={onClose}
    >
      <form className="stack" onSubmit={onSubmit}>
        <div className="callout deployment-callout">
          <h4>一步完成设备登记与部署准备</h4>
          <p>
            下载前会先把设备写入 Gateway，并附上当前选中的 Skill，
            让 Client 首次连回时可以直接进入工作状态。
          </p>
        </div>

        <div className="metric-strip compact-strip deployment-strip">
          <MetricCard
            label="已选 Skill"
            value={selectedSkills.length}
            detail={selectedSkills.length ? selectedSkills.map((skill) => skill.name).join(" · ") : "只登记设备"}
          />
          <MetricCard
            label="附加挂载"
            value={mountLabels.length}
            detail={mountLabels.length ? mountLabels.join(" · ") : "无额外挂载"}
          />
          <MetricCard
            label="网络档位"
            value={form.network_profile === "cn" ? "CN" : "Global"}
            detail={form.network_profile === "cn" ? "使用国内加速构建链路" : "使用默认构建链路"}
          />
        </div>

        <KeyValueGrid
          items={[
            {
              label: "目标 Gateway",
              value: form.gateway_url || "待填写",
              hint: "生成包会写入 Client 的连接地址。",
            },
            {
              label: "代码仓库",
              value: form.repo_url || "待填写",
              hint: "部署脚本会先拉取或更新这一份代码。",
            },
            {
              label: "设备标识",
              value: form.device_id || "待填写",
              hint: "同一设备 ID 会直接用于 Gateway 注册。",
            },
            {
              label: "准备结果",
              value: "zip 下载包",
              hint: "内含部署脚本、环境文件与 Client Compose 文件。",
            },
          ]}
        />

        <div className="panel panel-nested">
          <div className="panel-head compact">
            <div className="section-copy">
              <p className="eyebrow">Identity</p>
              <h4>设备与接入信息</h4>
            </div>
          </div>

          <div className="detail-grid deployment-form-grid">
            <FormField htmlFor="client-package-device-id" label="设备 ID">
              <input
                id="client-package-device-id"
                value={form.device_id}
                onChange={(event) => onChange({ device_id: event.target.value })}
              />
            </FormField>
            <FormField htmlFor="client-package-name" label="设备名称">
              <input
                id="client-package-name"
                value={form.name}
                onChange={(event) => onChange({ name: event.target.value })}
              />
            </FormField>
            <FormField
              htmlFor="client-package-device-key"
              label="设备密钥"
              note="留空时会在生成阶段自动创建。"
            >
              <input
                id="client-package-device-key"
                value={form.device_key}
                onChange={(event) => onChange({ device_key: event.target.value })}
              />
            </FormField>
            <FormField htmlFor="client-package-network" label="网络档位">
              <select
                id="client-package-network"
                value={form.network_profile}
                onChange={(event) => onChange({
                  network_profile: event.target.value as ClientDeploymentForm["network_profile"],
                })}
              >
                <option value="global">Global</option>
                <option value="cn">CN</option>
              </select>
            </FormField>
            <FormField
              className="deployment-form-span"
              htmlFor="client-package-gateway"
              label="Gateway 地址"
              note="填写 Client 所在主机可直接访问的绝对地址。"
            >
              <input
                id="client-package-gateway"
                placeholder="https://gateway.example.com/jarvis/api"
                value={form.gateway_url}
                onChange={(event) => onChange({ gateway_url: event.target.value })}
              />
            </FormField>
            <FormField
              className="deployment-form-span"
              htmlFor="client-package-repo-url"
              label="代码仓库"
              note="支持 https 或 ssh 形式的 Git 地址。"
            >
              <input
                id="client-package-repo-url"
                placeholder="https://github.com/your-org/open-jarvis.git"
                value={form.repo_url}
                onChange={(event) => onChange({ repo_url: event.target.value })}
              />
            </FormField>
            <FormField htmlFor="client-package-repo-ref" label="分支">
              <input
                id="client-package-repo-ref"
                value={form.repo_ref}
                onChange={(event) => onChange({ repo_ref: event.target.value })}
              />
            </FormField>
          </div>
        </div>

        <div className="panel panel-nested">
          <div className="panel-head compact">
            <div className="section-copy">
              <p className="eyebrow">Capabilities</p>
              <h4>预分配 Skill</h4>
              <p className="section-description muted">
                只展示当前已经可以下发给设备的 Skill；生成包后会同步写入 Gateway。
              </p>
            </div>
          </div>

          <div className="skill-option-list">
            {skills.map((skill) => {
              const ready = skill.source === "builtin" || skill.archive_ready;
              const selected = form.skill_ids.includes(skill.skill_id);

              return (
                <label
                  className={[
                    "skill-option",
                    ready ? "" : "disabled",
                    selected ? "selected" : "",
                  ].filter(Boolean).join(" ")}
                  key={skill.skill_id}
                >
                  <input
                    checked={selected}
                    disabled={!ready}
                    onChange={() => onToggleSkill(skill.skill_id)}
                    type="checkbox"
                  />
                  <div className="skill-option-copy">
                    <strong>{skill.name}</strong>
                    <span>{skill.skill_id}</span>
                    <small>{skill.description || "当前没有额外描述。"}</small>
                  </div>
                  <div className="skill-option-meta">
                    <span className={`package-pill${ready ? " ready" : " pending"}`}>
                      {skill.source === "builtin"
                        ? "内建"
                        : ready
                          ? "归档就绪"
                          : "待上传"}
                    </span>
                  </div>
                </label>
              );
            })}
          </div>
        </div>

        {error ? <p className="error-text">{error}</p> : null}
        <button className="primary-button" disabled={busy} type="submit">
          {busy ? "正在生成部署包…" : "生成并下载部署包"}
        </button>
      </form>
    </SideSheet>
  );
}
