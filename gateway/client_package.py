from __future__ import annotations

import io
import re
import textwrap
import zipfile
from dataclasses import dataclass


WORKSPACE_SKILL_IDS = {"builtin-filesystem", "builtin-shell"}
DOCKER_SOCKET_SKILL_IDS = {"builtin-docker"}
CLIENT_NETWORK_PROFILE_DEFAULTS = {
    "global": {
        "CLIENT_DOCKERFILE": "client/Dockerfile",
        "APT_MIRROR_HOST": "",
        "PIP_INDEX_URL": "",
        "PIP_TRUSTED_HOST": "",
    },
    "cn": {
        "CLIENT_DOCKERFILE": "client/Dockerfile.cn",
        "APT_MIRROR_HOST": "mirrors.tuna.tsinghua.edu.cn",
        "PIP_INDEX_URL": "https://pypi.tuna.tsinghua.edu.cn/simple",
        "PIP_TRUSTED_HOST": "pypi.tuna.tsinghua.edu.cn",
    },
}


@dataclass(frozen=True, slots=True)
class PackageSkill:
    skill_id: str
    name: str
    source: str


@dataclass(frozen=True, slots=True)
class ClientPackageSpec:
    device_id: str
    device_name: str
    device_key: str
    gateway_url: str
    repo_url: str
    repo_ref: str
    network_profile: str
    skills: tuple[PackageSkill, ...]


@dataclass(frozen=True, slots=True)
class MountPlan:
    needs_workspace: bool
    needs_docker_socket: bool

    @property
    def mount_count(self) -> int:
        return int(self.needs_workspace) + int(self.needs_docker_socket)


def build_client_package_entries(
    spec: ClientPackageSpec,
    *,
    env_text: str | None = None,
    package_root: str | None = None,
) -> dict[str, str]:
    resolved_root = package_root or _package_root(spec.device_id)
    mount_plan = build_mount_plan(skill.skill_id for skill in spec.skills)
    entries = {
        f"{resolved_root}/deploy-client.sh": _render_deploy_script(spec),
        f"{resolved_root}/client-package.env": env_text or _render_env_file(spec, mount_plan),
        f"{resolved_root}/docker-compose.client.generated.yml": _render_client_compose(mount_plan),
        f"{resolved_root}/README.md": _render_readme(spec, mount_plan),
    }
    if mount_plan.needs_workspace:
        entries[f"{resolved_root}/workspace/README.md"] = _render_workspace_readme(spec)
    return entries


def build_client_package(spec: ClientPackageSpec, *, env_text: str | None = None) -> tuple[str, bytes]:
    package_root = _package_root(spec.device_id)
    entries = build_client_package_entries(spec, env_text=env_text, package_root=package_root)

    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path, content in entries.items():
            bundle.writestr(path, content)
    return f"{package_root}.zip", payload.getvalue()


def build_mount_plan(skill_ids: list[str] | tuple[str, ...] | set[str] | object) -> MountPlan:
    normalized = {str(skill_id) for skill_id in skill_ids}
    return MountPlan(
        needs_workspace=bool(normalized & WORKSPACE_SKILL_IDS),
        needs_docker_socket=bool(normalized & DOCKER_SOCKET_SKILL_IDS),
    )


def _package_root(device_id: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", device_id).strip("-").lower() or "client"
    return f"open-jarvis-client-{slug}"


def _render_env_file(spec: ClientPackageSpec, mount_plan: MountPlan) -> str:
    profile_defaults = CLIENT_NETWORK_PROFILE_DEFAULTS[spec.network_profile]
    allowed_roots = "/workspace" if mount_plan.needs_workspace else "/data/client"
    lines = [
        f"DEPLOY_NETWORK_PROFILE={spec.network_profile}",
        f"CLIENT_DOCKERFILE={profile_defaults['CLIENT_DOCKERFILE']}",
        f"APT_MIRROR_HOST={profile_defaults['APT_MIRROR_HOST']}",
        f"PIP_INDEX_URL={profile_defaults['PIP_INDEX_URL']}",
        f"PIP_TRUSTED_HOST={profile_defaults['PIP_TRUSTED_HOST']}",
        "",
        f"OMNI_AGENT_GATEWAY_URL={spec.gateway_url.rstrip('/')}",
        f"OMNI_AGENT_DEVICE_ID={spec.device_id}",
        f"OMNI_AGENT_DEVICE_KEY={spec.device_key}",
        "OMNI_AGENT_CHECKPOINT_DB=/data/client/client.db",
        "OMNI_AGENT_LANGGRAPH_DB=/data/client/langgraph.db",
        "OMNI_AGENT_SKILLS_WORKSPACE=/data/client/skills-runtime",
        f"OMNI_AGENT_ALLOWED_ROOTS={allowed_roots}",
        "OMNI_AGENT_IOT_BASE_URL=",
        "OMNI_AGENT_IOT_TOKEN=",
        "OMNI_AGENT_CLIENT_AI_PROVIDER=",
        "OMNI_AGENT_CLIENT_AI_MODEL=",
        "OMNI_AGENT_CLIENT_AI_API_KEY=",
        "OMNI_AGENT_CLIENT_AI_BASE_URL=",
        "",
    ]
    return "\n".join(lines)


def _render_client_compose(mount_plan: MountPlan) -> str:
    volume_lines = ["      - client_data:/data/client"]
    if mount_plan.needs_workspace:
        volume_lines.append("      - ./client-package-workspace:/workspace:ro")
    if mount_plan.needs_docker_socket:
        volume_lines.append("      - /var/run/docker.sock:/var/run/docker.sock")
    lines = [
        "services:",
        "  client:",
        "    build:",
        "      context: .",
        "      dockerfile: ${CLIENT_DOCKERFILE:-client/Dockerfile}",
        "      args:",
        "        APT_MIRROR_HOST: ${APT_MIRROR_HOST:-}",
        "        PIP_INDEX_URL: ${PIP_INDEX_URL:-}",
        "        PIP_TRUSTED_HOST: ${PIP_TRUSTED_HOST:-}",
        "    environment:",
        "      OMNI_AGENT_GATEWAY_URL: ${OMNI_AGENT_GATEWAY_URL:-http://127.0.0.1:8000}",
        "      OMNI_AGENT_DEVICE_ID: ${OMNI_AGENT_DEVICE_ID:-device-alpha}",
        "      OMNI_AGENT_DEVICE_KEY: ${OMNI_AGENT_DEVICE_KEY:-device-secret}",
        "      OMNI_AGENT_CHECKPOINT_DB: ${OMNI_AGENT_CHECKPOINT_DB:-/data/client/client.db}",
        "      OMNI_AGENT_LANGGRAPH_DB: ${OMNI_AGENT_LANGGRAPH_DB:-/data/client/langgraph.db}",
        "      OMNI_AGENT_SKILLS_WORKSPACE: ${OMNI_AGENT_SKILLS_WORKSPACE:-/data/client/skills-runtime}",
        "      OMNI_AGENT_ALLOWED_ROOTS: ${OMNI_AGENT_ALLOWED_ROOTS:-/data/client}",
        "      OMNI_AGENT_IOT_BASE_URL: ${OMNI_AGENT_IOT_BASE_URL:-}",
        "      OMNI_AGENT_IOT_TOKEN: ${OMNI_AGENT_IOT_TOKEN:-}",
        "      OMNI_AGENT_CLIENT_AI_PROVIDER: ${OMNI_AGENT_CLIENT_AI_PROVIDER:-}",
        "      OMNI_AGENT_CLIENT_AI_MODEL: ${OMNI_AGENT_CLIENT_AI_MODEL:-}",
        "      OMNI_AGENT_CLIENT_AI_API_KEY: ${OMNI_AGENT_CLIENT_AI_API_KEY:-}",
        "      OMNI_AGENT_CLIENT_AI_BASE_URL: ${OMNI_AGENT_CLIENT_AI_BASE_URL:-}",
        "    volumes:",
        *volume_lines,
        "    restart: unless-stopped",
        "",
        "volumes:",
        "  client_data:",
        "",
    ]
    return "\n".join(lines)


def _render_deploy_script(spec: ClientPackageSpec) -> str:
    repo_dir_name = _package_root(spec.device_id)
    return textwrap.dedent(
        f"""\
        #!/usr/bin/env bash
        set -euo pipefail

        PACKAGE_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
        REPO_URL="{spec.repo_url}"
        REPO_REF="{spec.repo_ref}"
        REPO_DIR="${{REPO_DIR:-$PACKAGE_DIR/{repo_dir_name}}}"
        COMPOSE_FILE="$REPO_DIR/docker-compose.client.generated.yml"
        WORKSPACE_DIR="$REPO_DIR/client-package-workspace"
        ENV_FILE="$REPO_DIR/.env"
        BACKUP_ENV_FILE="$REPO_DIR/.env.client-package.backup"

        require_cmd() {{
          command -v "$1" >/dev/null 2>&1 || {{
            echo "缺少命令: $1" >&2
            exit 1
          }}
        }}

        sync_repo() {{
          if [[ -d "$REPO_DIR/.git" ]]; then
            git -C "$REPO_DIR" remote set-url origin "$REPO_URL"
            git -C "$REPO_DIR" fetch --depth 1 origin "$REPO_REF"
            if ! git -C "$REPO_DIR" checkout "$REPO_REF"; then
              git -C "$REPO_DIR" checkout -B "$REPO_REF" "origin/$REPO_REF"
            fi
            git -C "$REPO_DIR" pull --ff-only origin "$REPO_REF"
          else
            git clone --depth 1 --branch "$REPO_REF" "$REPO_URL" "$REPO_DIR"
          fi
        }}

        install_package_files() {{
          if [[ -f "$ENV_FILE" && ! -f "$BACKUP_ENV_FILE" ]]; then
            cp "$ENV_FILE" "$BACKUP_ENV_FILE"
          fi

          cp "$PACKAGE_DIR/client-package.env" "$ENV_FILE"
          cp "$PACKAGE_DIR/docker-compose.client.generated.yml" "$COMPOSE_FILE"

          if [[ -d "$PACKAGE_DIR/workspace" ]]; then
            mkdir -p "$WORKSPACE_DIR"
            cp -R "$PACKAGE_DIR/workspace/." "$WORKSPACE_DIR/"
          fi
        }}

        main() {{
          require_cmd git
          require_cmd docker

          sync_repo
          install_package_files

          chmod +x "$REPO_DIR/jarvisctl"

          (
            cd "$REPO_DIR"
            JARVISCTL_COMPOSE_FILE="$COMPOSE_FILE" ./jarvisctl deploy client
          )

          echo "Client 部署完成。"
          echo "仓库目录: $REPO_DIR"
          if [[ -f "$BACKUP_ENV_FILE" ]]; then
            echo "已备份原始环境文件: $BACKUP_ENV_FILE"
          fi
        }}

        main "$@"
        """
    )


def _render_readme(spec: ClientPackageSpec, mount_plan: MountPlan) -> str:
    package_name = _package_root(spec.device_id)
    skill_lines = "\n".join(
        f"- {skill.name} (`{skill.skill_id}`)"
        for skill in spec.skills
    ) or "- 本次未预分配 Skill"
    mount_lines: list[str] = []
    if mount_plan.needs_workspace:
        mount_lines.append("- 已生成 `client-package-workspace -> /workspace` 只读挂载。")
    if mount_plan.needs_docker_socket:
        mount_lines.append("- 已生成 Docker Socket 挂载。")
    if not mount_lines:
        mount_lines.append("- 本次部署包不追加宿主机挂载。")
    mount_summary = "\n".join(mount_lines)
    return "\n".join(
        [
            "# Client 部署包",
            "",
            f"目标设备：`{spec.device_name}` (`{spec.device_id}`)",
            "",
            "这个压缩包会在本地执行以下流程：",
            "",
            f"1. 拉取或更新 `{spec.repo_ref}` 分支代码",
            "2. 覆盖生成专用 `.env`",
            "3. 写入独立的 Client Compose 文件",
            "4. 通过官方 `jarvisctl` 脚本部署 `client`",
            "",
            "已分配 Skill：",
            "",
            skill_lines,
            "",
            "挂载策略：",
            "",
            mount_summary,
            "",
            "使用方式：",
            "",
            "```bash",
            f"unzip {package_name}.zip",
            f"cd {package_name}",
            "chmod +x deploy-client.sh",
            "./deploy-client.sh",
            "```",
            "",
            f"Gateway 地址：`{spec.gateway_url.rstrip('/')}`",
            f"代码仓库：`{spec.repo_url}`",
            "",
        ]
    )


def _render_workspace_readme(spec: ClientPackageSpec) -> str:
    return textwrap.dedent(
        f"""\
        # Client Workspace

        这个目录会在部署时挂载到 `/workspace`。

        设备：`{spec.device_id}`
        建议把需要给文件系统或 Shell Skill 读取的内容放到这里，再重新执行 `./deploy-client.sh`。
        """
    )
