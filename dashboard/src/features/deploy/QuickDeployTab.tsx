import { MetricCard } from "../../components/MetricCard";
import { FormField } from "../../components/FormField";
import { SectionHeader } from "../../components/SectionHeader";
import type { QuickDeployForm } from "../../app/model";
import type {
  QuickDeployDraft,
  QuickDeployField,
  QuickDeployModuleId,
  Skill,
} from "../../types";

type QuickDeployTabProps = {
  draft: QuickDeployDraft;
  form: QuickDeployForm;
  skills: Skill[];
  busy: boolean;
  error: string | null;
  onFieldChange: (moduleId: QuickDeployModuleId, key: string, value: string) => void;
  onClientPackageChange: (patch: Partial<QuickDeployForm["client_package"]>) => void;
  onToggleSkill: (skillId: string) => void;
  onSubmit: () => void | Promise<void>;
};

const clientVisibleFieldKeys = [
  "OMNI_AGENT_GATEWAY_URL",
  "OMNI_AGENT_DEVICE_ID",
  "OMNI_AGENT_DEVICE_KEY",
  "DEPLOY_NETWORK_PROFILE",
] as const;

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

function pickVisibleClientFields(draft: QuickDeployDraft): QuickDeployField[] {
  const fieldMap = new Map(
    draft.modules.client.fields.map((field) => [field.key, field] as const),
  );

  return clientVisibleFieldKeys.flatMap((key) => {
    const field = fieldMap.get(key);
    return field ? [field] : [];
  });
}

export function QuickDeployTab({
  draft,
  form,
  skills,
  busy,
  error,
  onFieldChange,
  onClientPackageChange,
  onToggleSkill,
  onSubmit,
}: QuickDeployTabProps) {
  const readySkills = skills.filter(
    (skill) => skill.source === "builtin" || skill.archive_ready,
  );
  const selectedSkills = readySkills.filter((skill) => form.client_package.skill_ids.includes(skill.skill_id));
  const selectedSkillLabel = selectedSkills.length
    ? selectedSkills.map((skill) => skill.name).join(" · ")
    : "不随包下发";
  const deviceId = form.modules.client.OMNI_AGENT_DEVICE_ID?.trim() || "待填写";
  const deviceName = form.client_package.device_name.trim() || "与设备 ID 一致";
  const syncEnabled = form.client_package.register_device;
  const clientFields = pickVisibleClientFields(draft);

  return (
    <section className="panel quick-deploy-shell">
      <SectionHeader
        eyebrow="Quick Deploy"
        title="CLI 快速部署"
        description="只保留 CLI 设备接入、代码拉取和可选 Skill 同步，生成 Client 部署包。"
        actions={(
          <button className="primary-button" disabled={busy} onClick={() => void onSubmit()} type="button">
            {busy ? "正在生成…" : "生成 Client 部署包"}
          </button>
        )}
      />

      <div className="quick-deploy-hero">
        <div className="quick-deploy-hero-copy">
          <p className="eyebrow">Client 部署包</p>
          <h4>生成可直接下发到 CLI 设备的部署包。</h4>
          <p className="muted">
            下载包内会包含 <code>client/.env</code>、<code>deploy-client.sh</code> 和独立
            Compose 文件。
          </p>
        </div>
        <div className="metric-strip compact-strip deployment-strip">
          <MetricCard label="CLI 设备" value={deviceId} detail={deviceName} />
          <MetricCard
            label="同步登记"
            value={syncEnabled ? "开启" : "关闭"}
            detail={syncEnabled ? "生成时写入 Gateway 设备表" : "仅下载本地部署包"}
          />
          <MetricCard label="随包 Skill" value={selectedSkills.length} detail={selectedSkillLabel} />
        </div>
      </div>

      <section className="panel panel-nested quick-module selected">
        <SectionHeader
          compact
          eyebrow="CLI"
          title="CLI 接入信息"
          description="填写设备标识、Gateway 地址和代码来源后即可生成 Client 部署包。"
          titleAs="h4"
        />

        <div className="quick-client-extra">
          <div className="detail-grid">
            <FormField
              htmlFor="quick-client-device-name"
              label="设备显示名"
              note="用于部署包说明和可选的 Gateway 设备登记。"
            >
              <input
                id="quick-client-device-name"
                value={form.client_package.device_name}
                onChange={(event) => onClientPackageChange({ device_name: event.target.value })}
              />
            </FormField>
            <FormField
              className="deployment-form-span"
              htmlFor="quick-client-repo-url"
              label="代码仓库"
              note="部署脚本会先拉取这份代码，再执行 Client Compose。"
            >
              <input
                id="quick-client-repo-url"
                value={form.client_package.repo_url}
                onChange={(event) => onClientPackageChange({ repo_url: event.target.value })}
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
          </div>

          <div className="detail-grid quick-field-grid">
            {clientFields.map((field) => (
              <FormField
                className={field.key.includes("URL") ? "deployment-form-span" : undefined}
                htmlFor={`client-${field.key.toLowerCase()}`}
                key={`client-${field.key}`}
                label={field.required ? `${field.label} *` : field.label}
                note={field.description}
              >
                {renderFieldInput("client", field, form.modules.client[field.key] ?? "", onFieldChange)}
              </FormField>
            ))}
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

          {readySkills.length ? (
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
          ) : (
            <div className="callout quick-deploy-callout">
              <h4>可选 Skill</h4>
              <p>当前没有可随 Client 部署包一起下发的 Skill。</p>
            </div>
          )}
        </div>

        {error ? <p className="error-text">{error}</p> : null}

        <div className="quick-deploy-actions">
          <button className="primary-button" disabled={busy} onClick={() => void onSubmit()} type="button">
            {busy ? "正在生成…" : "生成 Client 部署包"}
          </button>
        </div>
      </section>
    </section>
  );
}
