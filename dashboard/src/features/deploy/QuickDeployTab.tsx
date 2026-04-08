import { KeyValueGrid } from "../../components/KeyValueGrid";
import { MetricCard } from "../../components/MetricCard";
import { FormField } from "../../components/FormField";
import { SectionHeader } from "../../components/SectionHeader";
import type { QuickDeployForm } from "../../app/model";
import type {
  Device,
  QuickDeployDraft,
  QuickDeployField,
  QuickDeployModuleId,
  Skill,
} from "../../types";

type QuickDeployTabProps = {
  draft: QuickDeployDraft;
  form: QuickDeployForm;
  skills: Skill[];
  devices: Device[];
  busy: boolean;
  error: string | null;
  onToggleTarget: (moduleId: QuickDeployModuleId) => void;
  onFieldChange: (moduleId: QuickDeployModuleId, key: string, value: string) => void;
  onClientPackageChange: (patch: Partial<QuickDeployForm["client_package"]>) => void;
  onToggleSkill: (skillId: string) => void;
  onSubmit: () => void | Promise<void>;
};

const moduleOrder: QuickDeployModuleId[] = ["gateway", "client", "dashboard"];

function renderFieldInput(
  moduleId: QuickDeployModuleId,
  field: QuickDeployField,
  value: string,
  onFieldChange: QuickDeployTabProps["onFieldChange"],
) {
  const inputId = `${moduleId}-${field.key.toLowerCase()}`;
  if (field.input_type === "select") {
    return (
      <select
        id={inputId}
        value={value}
        onChange={(event) => onFieldChange(moduleId, field.key, event.target.value)}
      >
        <option value="global">Global</option>
        <option value="cn">CN</option>
      </select>
    );
  }

  return (
    <input
      id={inputId}
      type={field.input_type}
      value={value}
      onChange={(event) => onFieldChange(moduleId, field.key, event.target.value)}
    />
  );
}

export function QuickDeployTab({
  draft,
  form,
  skills,
  devices,
  busy,
  error,
  onToggleTarget,
  onFieldChange,
  onClientPackageChange,
  onToggleSkill,
  onSubmit,
}: QuickDeployTabProps) {
  const selectedTargets = new Set(form.targets);
  const readySkills = skills.filter(
    (skill) => skill.source === "builtin" || skill.archive_ready,
  );
  const selectedSkills = readySkills.filter((skill) => form.client_package.skill_ids.includes(skill.skill_id));
  const clientSelected = selectedTargets.has("client");
  const syncEnabled = clientSelected && form.client_package.register_device;
  const selectedTargetLabel = form.targets.length
    ? form.targets.map((target) => draft.modules[target].title).join(" / ")
    : "待选择";
  const gatewayValue = form.modules.client.OMNI_AGENT_GATEWAY_URL
    || form.modules.dashboard.VITE_GATEWAY_BASE_URL
    || "待填写";

  return (
    <section className="panel quick-deploy-shell">
      <SectionHeader
        eyebrow="Quick Deploy"
        title="快速部署"
        description="把 Gateway / Client / Dashboard 的独立部署配置收拢到同一工作区，按模块勾选后统一生成工件。"
        actions={(
          <button className="primary-button" disabled={busy} onClick={() => void onSubmit()} type="button">
            {busy ? "正在生成…" : "生成快速部署包"}
          </button>
        )}
      />

      <div className="quick-deploy-hero">
        <div className="quick-deploy-hero-copy">
          <p className="eyebrow">Gateway / Client / Dashboard</p>
          <h4>按模块整理部署工件，再决定是否同步写入 Gateway。</h4>
          <p className="muted">
            Client 会把接入地址、设备标识与可选 Skill 一起带走；Gateway 与 Dashboard 则分别生成独立 `.env`。
          </p>
        </div>
        <div className="metric-strip compact-strip deployment-strip">
          <MetricCard label="目标模块" value={form.targets.length} detail={selectedTargetLabel} />
          <MetricCard label="同步创建设备" value={syncEnabled ? "开启" : "关闭"} detail={syncEnabled ? "生成时登记设备并预分配 Skill" : "仅生成工件，不写回 Gateway"} />
          <MetricCard label="可部署 Skill" value={readySkills.length} detail={selectedSkills.length ? selectedSkills.map((skill) => skill.name).join(" · ") : "当前未选择"} />
        </div>
      </div>

      <div className="quick-target-row" role="group" aria-label="部署目标选择">
        {moduleOrder.map((moduleId) => {
          const meta = draft.modules[moduleId];
          const active = selectedTargets.has(moduleId);

          return (
            <label
              className={`quick-target-chip${active ? " active" : ""}`}
              key={moduleId}
            >
              <input
                checked={active}
                onChange={() => onToggleTarget(moduleId)}
                type="checkbox"
              />
              <div>
                <strong>{meta.title}</strong>
                <small>{meta.artifact_label}</small>
              </div>
            </label>
          );
        })}
      </div>

      <div className="quick-deploy-layout">
        <div className="panel-stack">
          {moduleOrder.map((moduleId) => {
            const meta = draft.modules[moduleId];
            const active = selectedTargets.has(moduleId);
            const moduleValues = form.modules[moduleId];

            return (
              <section
                className={`panel panel-nested quick-module${active ? " selected" : ""}`}
                key={moduleId}
              >
                <SectionHeader
                  compact
                  eyebrow={meta.artifact_label}
                  title={meta.title}
                  description={meta.description}
                  titleAs="h4"
                />

                {moduleId === "client" ? (
                  <div className="quick-client-extra">
                    <div className="detail-grid">
                      <FormField
                        htmlFor="quick-client-device-name"
                        label="设备名称"
                        note="用于部署包说明与可选的 Gateway 设备登记。"
                      >
                        <input
                          id="quick-client-device-name"
                          value={form.client_package.device_name}
                          onChange={(event) => onClientPackageChange({ device_name: event.target.value })}
                        />
                      </FormField>
                      <FormField
                        htmlFor="quick-client-repo-ref"
                        label="代码分支"
                        note="默认使用 main。"
                      >
                        <input
                          id="quick-client-repo-ref"
                          value={form.client_package.repo_ref}
                          onChange={(event) => onClientPackageChange({ repo_ref: event.target.value })}
                        />
                      </FormField>
                      <FormField
                        className="deployment-form-span"
                        htmlFor="quick-client-repo-url"
                        label="代码仓库"
                        note="部署脚本会拉取这份代码，再执行独立的 Client Compose。"
                      >
                        <input
                          id="quick-client-repo-url"
                          value={form.client_package.repo_url}
                          onChange={(event) => onClientPackageChange({ repo_url: event.target.value })}
                        />
                      </FormField>
                    </div>

                    <label className={`quick-inline-toggle${syncEnabled ? " active" : ""}`}>
                      <input
                        checked={form.client_package.register_device}
                        onChange={(event) => onClientPackageChange({ register_device: event.target.checked })}
                        type="checkbox"
                      />
                      <div>
                        <strong>同步在 Gateway 创建设备</strong>
                        <small>勾选后会在生成时登记设备，并把已选 Skill 一并预分配。</small>
                      </div>
                    </label>

                    <div className="skill-option-list">
                      {readySkills.map((skill) => {
                        const selected = form.client_package.skill_ids.includes(skill.skill_id);

                        return (
                          <label
                            className={`skill-option${selected ? " selected" : ""}`}
                            key={skill.skill_id}
                          >
                            <input
                              checked={selected}
                              onChange={() => onToggleSkill(skill.skill_id)}
                              type="checkbox"
                            />
                            <div className="skill-option-copy">
                              <strong>{skill.name}</strong>
                              <span>{skill.skill_id}</span>
                              <small>{skill.description || "当前没有额外描述。"}</small>
                            </div>
                            <div className="skill-option-meta">
                              <span className={`package-pill${skill.source === "builtin" || skill.archive_ready ? " ready" : " pending"}`}>
                                {skill.source === "builtin" ? "内建" : "归档就绪"}
                              </span>
                            </div>
                          </label>
                        );
                      })}
                    </div>
                  </div>
                ) : null}

                <div className="detail-grid quick-field-grid">
                  {meta.fields.map((field) => (
                    <FormField
                      className={field.key.includes("URL") || field.key.includes("DOCKERFILE") ? "deployment-form-span" : undefined}
                      htmlFor={`${moduleId}-${field.key.toLowerCase()}`}
                      key={`${moduleId}-${field.key}`}
                      label={field.required ? `${field.label} *` : field.label}
                      note={field.description}
                    >
                      {renderFieldInput(moduleId, field, moduleValues[field.key] ?? "", onFieldChange)}
                    </FormField>
                  ))}
                </div>
              </section>
            );
          })}
        </div>

        <aside className="quick-deploy-side">
          <div className="callout quick-deploy-callout">
            <h4>当前打包摘要</h4>
            <p>
              选中模块后会分别输出对应目录；Client 目录还会附带
              <code>deploy-client.sh</code>
              与独立 Compose 文件。
            </p>
          </div>

          <KeyValueGrid
            items={[
              {
                label: "部署目标",
                value: selectedTargetLabel,
                hint: "下载包会按模块拆目录，不互相覆盖。",
              },
              {
                label: "Gateway 地址",
                value: gatewayValue,
                hint: "优先写入 Client 与 Dashboard 的连接配置。",
              },
              {
                label: "Client 设备",
                value: form.modules.client.OMNI_AGENT_DEVICE_ID || "待填写",
                hint: syncEnabled ? "生成时会同步登记到 Gateway。" : "当前只生成本地工件。",
              },
              {
                label: "已登记设备",
                value: devices.length,
                hint: "可用于确认当前 Gateway 中已有的设备基线。",
              },
            ]}
          />

          {error ? <p className="error-text">{error}</p> : null}

          <div className="quick-deploy-actions">
            <button className="primary-button" disabled={busy} onClick={() => void onSubmit()} type="button">
              {busy ? "正在生成…" : "生成快速部署包"}
            </button>
          </div>
        </aside>
      </div>
    </section>
  );
}
