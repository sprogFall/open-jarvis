from __future__ import annotations

import io
import textwrap
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from jarvisctl import (
    CN_PROFILE_DEFAULTS,
    GLOBAL_PROFILE_DEFAULTS,
    render_env_file,
)

from gateway.client_package import (
    ClientPackageSpec,
    PackageSkill,
    build_client_package_entries,
)


QuickDeployModule = Literal["client", "gateway", "dashboard"]

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_TEMPLATE_PATHS: dict[QuickDeployModule, Path] = {
    "client": PROJECT_ROOT / "client" / ".env.example",
    "gateway": PROJECT_ROOT / "gateway" / ".env.example",
    "dashboard": PROJECT_ROOT / "dashboard" / ".env.example",
}
QUICK_DEPLOY_MODULES: tuple[QuickDeployModule, ...] = ("client", "gateway", "dashboard")


@dataclass(frozen=True, slots=True)
class DeployFieldSpec:
    key: str
    label: str
    description: str
    required: bool = False
    secret: bool = False
    input_type: str = "text"
    default_value: str | None = None


FIELD_SPECS: dict[QuickDeployModule, tuple[DeployFieldSpec, ...]] = {
    "client": (
        DeployFieldSpec(
            "OMNI_AGENT_GATEWAY_URL",
            "Gateway 连接地址",
            "填写 Client 容器可直接访问的 Gateway 绝对地址。",
            required=True,
            input_type="url",
            default_value="",
        ),
        DeployFieldSpec(
            "OMNI_AGENT_DEVICE_ID",
            "设备 ID",
            "作为 Client 身份标识，也可用于后续在 Gateway 中定位设备。",
            required=True,
            default_value="",
        ),
        DeployFieldSpec(
            "OMNI_AGENT_DEVICE_KEY",
            "设备密钥",
            "留空时在生成阶段自动创建；只有下载工件时会写入 .env。",
            secret=True,
            input_type="password",
            default_value="",
        ),
        DeployFieldSpec(
            "DEPLOY_NETWORK_PROFILE",
            "网络档位",
            "切换镜像源与 Dockerfile 方案，兼容 Global 与 CN 两种构建链路。",
            required=True,
            input_type="select",
            default_value="global",
        ),
        DeployFieldSpec(
            "CLIENT_DOCKERFILE",
            "Client Dockerfile",
            "通常保持默认；切换网络档位时会自动联动。",
        ),
        DeployFieldSpec(
            "APT_MIRROR_HOST",
            "APT 镜像主机",
            "仅在需要替换系统包镜像时填写。",
        ),
        DeployFieldSpec(
            "PIP_INDEX_URL",
            "PIP 索引地址",
            "需要走镜像源时填写，例如企业内源或国内加速源。",
            input_type="url",
        ),
        DeployFieldSpec(
            "PIP_TRUSTED_HOST",
            "PIP 信任主机",
            "当 PIP 镜像使用自签证书或明文源时可补充。",
        ),
        DeployFieldSpec(
            "OMNI_AGENT_CLIENT_AI_PROVIDER",
            "AI Provider",
            "需要让 Client 独立调用模型时填写。",
        ),
        DeployFieldSpec(
            "OMNI_AGENT_CLIENT_AI_MODEL",
            "AI Model",
            "与 Provider 配套填写具体模型名。",
        ),
        DeployFieldSpec(
            "OMNI_AGENT_CLIENT_AI_API_KEY",
            "AI API Key",
            "只有生成的 .env 会写入此值，页面不会回显历史内容。",
            secret=True,
            input_type="password",
            default_value="",
        ),
        DeployFieldSpec(
            "OMNI_AGENT_CLIENT_AI_BASE_URL",
            "AI Base URL",
            "自建网关或第三方兼容接口时填写。",
            input_type="url",
        ),
    ),
    "gateway": (
        DeployFieldSpec(
            "DATABASE_URL",
            "数据库连接",
            "支持 PostgreSQL 连接串或可挂载的 sqlite 路径。",
            required=True,
            secret=True,
            input_type="password",
            default_value="",
        ),
        DeployFieldSpec(
            "OMNI_AGENT_JWT_SECRET",
            "JWT 密钥",
            "用于 Dashboard 与 App 的登录签名。",
            required=True,
            secret=True,
            input_type="password",
            default_value="",
        ),
        DeployFieldSpec(
            "OMNI_AGENT_ADMIN_USERNAME",
            "管理员账号",
            "Dashboard 与 App 登录账号。",
            required=True,
            default_value="operator",
        ),
        DeployFieldSpec(
            "OMNI_AGENT_ADMIN_PASSWORD",
            "管理员密码",
            "只写入生成工件，不会在页面读回。",
            required=True,
            secret=True,
            input_type="password",
            default_value="",
        ),
        DeployFieldSpec(
            "DEPLOY_NETWORK_PROFILE",
            "网络档位",
            "切换镜像源与 Dockerfile 方案，兼容 Global 与 CN 两种构建链路。",
            required=True,
            input_type="select",
            default_value="global",
        ),
        DeployFieldSpec(
            "GATEWAY_PORT",
            "Gateway 端口",
            "容器或进程对外暴露的 HTTP 端口。",
            default_value="8000",
        ),
        DeployFieldSpec(
            "GATEWAY_DOCKERFILE",
            "Gateway Dockerfile",
            "通常保持默认；切换网络档位时会自动联动。",
        ),
        DeployFieldSpec(
            "APT_MIRROR_HOST",
            "APT 镜像主机",
            "仅在需要替换系统包镜像时填写。",
        ),
        DeployFieldSpec(
            "PIP_INDEX_URL",
            "PIP 索引地址",
            "需要走镜像源时填写，例如企业内源或国内加速源。",
            input_type="url",
        ),
        DeployFieldSpec(
            "PIP_TRUSTED_HOST",
            "PIP 信任主机",
            "当 PIP 镜像使用自签证书或明文源时可补充。",
        ),
        DeployFieldSpec(
            "OMNI_AGENT_DASHBOARD_ORIGINS",
            "Dashboard 来源白名单",
            "前后端跨域部署时填写允许访问的域名，多个值用英文逗号分隔。",
        ),
        DeployFieldSpec(
            "OMNI_AGENT_GATEWAY_AI_PROVIDER",
            "默认 AI Provider",
            "需要让 Gateway 直接参与模型调用时填写。",
        ),
        DeployFieldSpec(
            "OMNI_AGENT_GATEWAY_AI_MODEL",
            "默认 AI Model",
            "与 Provider 配套填写具体模型名。",
        ),
        DeployFieldSpec(
            "OMNI_AGENT_GATEWAY_AI_API_KEY",
            "默认 AI API Key",
            "只写入生成工件，不会在页面读回。",
            secret=True,
            input_type="password",
            default_value="",
        ),
        DeployFieldSpec(
            "OMNI_AGENT_GATEWAY_AI_BASE_URL",
            "默认 AI Base URL",
            "自建网关或第三方兼容接口时填写。",
            input_type="url",
        ),
    ),
    "dashboard": (
        DeployFieldSpec(
            "VITE_GATEWAY_BASE_URL",
            "Gateway API 地址",
            "浏览器访问 Gateway 的基地址，支持子路径或完整域名。",
            required=True,
            input_type="url",
            default_value="",
        ),
        DeployFieldSpec(
            "DASHBOARD_PORT",
            "Dashboard 端口",
            "静态站点容器对外暴露的端口。",
            default_value="8080",
        ),
        DeployFieldSpec(
            "DEPLOY_NETWORK_PROFILE",
            "网络档位",
            "切换构建镜像源与 Dockerfile 方案。",
            required=True,
            input_type="select",
            default_value="global",
        ),
        DeployFieldSpec(
            "DASHBOARD_DOCKERFILE",
            "Dashboard Dockerfile",
            "通常保持默认；切换网络档位时会自动联动。",
        ),
        DeployFieldSpec(
            "DASHBOARD_NPM_REGISTRY",
            "NPM Registry",
            "需要使用镜像源构建前端时填写。",
            input_type="url",
        ),
    ),
}

MODULE_META: dict[QuickDeployModule, dict[str, str]] = {
    "client": {
        "title": "Client",
        "description": "生成可直接下发到边缘设备的部署包与 .env。",
        "artifact_label": "部署包 + .env",
    },
    "gateway": {
        "title": "Gateway",
        "description": "独立维护中转层的数据库、鉴权与网络构建参数。",
        "artifact_label": ".env",
    },
    "dashboard": {
        "title": "Dashboard",
        "description": "独立维护前端静态站点的 API 基地址与构建参数。",
        "artifact_label": ".env",
    },
}


def _module_template_text(module: QuickDeployModule) -> str:
    return MODULE_TEMPLATE_PATHS[module].read_text(encoding="utf-8")


def _field_value(spec: DeployFieldSpec) -> str:
    if spec.default_value is not None:
        return spec.default_value
    return ""


def build_quick_deploy_draft() -> dict:
    modules: dict[str, dict] = {}
    for module in QUICK_DEPLOY_MODULES:
        modules[module] = {
            **MODULE_META[module],
            "fields": [
                {
                    "key": spec.key,
                    "label": spec.label,
                    "description": spec.description,
                    "required": spec.required,
                    "secret": spec.secret,
                    "input_type": spec.input_type,
                    "value": "" if spec.secret else _field_value(spec),
                }
                for spec in FIELD_SPECS[module]
            ],
        }
    return {
        "modules": modules,
        "client_package": {
            "repo_url": "",
            "repo_ref": "main",
            "register_device": True,
        },
    }


def normalize_module_env(
    module: QuickDeployModule,
    values: dict[str, str] | None,
) -> dict[str, str]:
    raw_values = {
        key: str(value).strip()
        for key, value in (values or {}).items()
        if value is not None
    }
    normalized = {
        spec.key: raw_values.get(spec.key, _field_value(spec))
        for spec in FIELD_SPECS[module]
    }
    profile = normalized.get("DEPLOY_NETWORK_PROFILE", "").strip() or "global"
    if profile not in {"global", "cn"}:
        profile = "global"
    normalized["DEPLOY_NETWORK_PROFILE"] = profile

    defaults = CN_PROFILE_DEFAULTS if profile == "cn" else GLOBAL_PROFILE_DEFAULTS
    if module == "client":
        normalized["CLIENT_DOCKERFILE"] = normalized.get("CLIENT_DOCKERFILE") or defaults["CLIENT_DOCKERFILE"]
        normalized["APT_MIRROR_HOST"] = normalized.get("APT_MIRROR_HOST") or defaults["APT_MIRROR_HOST"]
        normalized["PIP_INDEX_URL"] = normalized.get("PIP_INDEX_URL") or defaults["PIP_INDEX_URL"]
        normalized["PIP_TRUSTED_HOST"] = normalized.get("PIP_TRUSTED_HOST") or defaults["PIP_TRUSTED_HOST"]
    elif module == "gateway":
        normalized["GATEWAY_DOCKERFILE"] = normalized.get("GATEWAY_DOCKERFILE") or defaults["GATEWAY_DOCKERFILE"]
        normalized["APT_MIRROR_HOST"] = normalized.get("APT_MIRROR_HOST") or defaults["APT_MIRROR_HOST"]
        normalized["PIP_INDEX_URL"] = normalized.get("PIP_INDEX_URL") or defaults["PIP_INDEX_URL"]
        normalized["PIP_TRUSTED_HOST"] = normalized.get("PIP_TRUSTED_HOST") or defaults["PIP_TRUSTED_HOST"]
    else:
        normalized["DASHBOARD_DOCKERFILE"] = normalized.get("DASHBOARD_DOCKERFILE") or defaults["DASHBOARD_DOCKERFILE"]
        normalized["DASHBOARD_NPM_REGISTRY"] = (
            normalized.get("DASHBOARD_NPM_REGISTRY") or defaults["DASHBOARD_NPM_REGISTRY"]
        )
    return normalized


def required_field_label(
    module: QuickDeployModule,
    values: dict[str, str],
) -> str | None:
    for spec in FIELD_SPECS[module]:
        if spec.required and not values.get(spec.key, "").strip():
            return spec.label
    return None


def render_module_env(
    module: QuickDeployModule,
    values: dict[str, str],
) -> str:
    return render_env_file(values, _module_template_text(module))


def build_quick_deploy_archive(
    *,
    targets: tuple[QuickDeployModule, ...],
    rendered_envs: dict[QuickDeployModule, str],
    client_spec: ClientPackageSpec | None = None,
) -> tuple[str, bytes]:
    entries: dict[str, str] = {
        "README.md": _render_bundle_readme(targets),
    }

    for module in targets:
        entries[f"{module}/.env"] = rendered_envs[module]

    if client_spec is not None:
        client_entries = build_client_package_entries(
            client_spec,
            env_text=rendered_envs["client"],
            package_root="client",
        )
        for path, content in client_entries.items():
            renamed_path = path.replace("client/client-package.env", "client/.env")
            entries[renamed_path] = content

    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path, content in entries.items():
            bundle.writestr(path, content)

    suffix = "-".join(targets) if targets else "bundle"
    return f"open-jarvis-quick-deploy-{suffix}.zip", payload.getvalue()


def build_package_skills(skills: list[dict]) -> tuple[PackageSkill, ...]:
    return tuple(
        PackageSkill(
            skill_id=str(skill["skill_id"]),
            name=str(skill["name"]),
            source=str(skill["source"]),
        )
        for skill in skills
    )


def _render_bundle_readme(targets: tuple[QuickDeployModule, ...]) -> str:
    target_lines = "\n".join(f"- {MODULE_META[target]['title']}" for target in targets)
    return textwrap.dedent(
        f"""\
        # 快速部署工件

        本次打包包含以下模块：

        {target_lines}

        使用方式：

        1. 按目录进入对应模块。
        2. 根据部署方式替换或补充 `.env`。
        3. Client 目录内已附带 `deploy-client.sh` 与独立 Compose 文件，可直接下发到设备。
        """
    )
