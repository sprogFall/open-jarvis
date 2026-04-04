from __future__ import annotations

import argparse
import getpass
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env"
ENV_TEMPLATE_FILE = ROOT / ".env.example"
FULL_STACK_SERVICES = ("postgres", "gateway", "client", "dashboard")
RUNTIME_SERVICES = ("gateway", "client", "dashboard")
VALID_TARGETS = FULL_STACK_SERVICES
CN_PROFILE_DEFAULTS = {
    "GATEWAY_DOCKERFILE": "gateway/Dockerfile.cn",
    "CLIENT_DOCKERFILE": "client/Dockerfile.cn",
    "DASHBOARD_DOCKERFILE": "dashboard/Dockerfile.cn",
    "APT_MIRROR_HOST": "mirrors.tuna.tsinghua.edu.cn",
    "PIP_INDEX_URL": "https://pypi.tuna.tsinghua.edu.cn/simple",
    "PIP_TRUSTED_HOST": "pypi.tuna.tsinghua.edu.cn",
    "DASHBOARD_NPM_REGISTRY": "https://registry.npmmirror.com",
}
GLOBAL_PROFILE_DEFAULTS = {
    "GATEWAY_DOCKERFILE": "gateway/Dockerfile",
    "CLIENT_DOCKERFILE": "client/Dockerfile",
    "DASHBOARD_DOCKERFILE": "dashboard/Dockerfile",
    "APT_MIRROR_HOST": "",
    "PIP_INDEX_URL": "",
    "PIP_TRUSTED_HOST": "",
    "DASHBOARD_NPM_REGISTRY": "",
}

PLACEHOLDER_DEFAULTS = {
    "POSTGRES_PASSWORD": "jarvis",
    "OMNI_AGENT_JWT_SECRET": "change-me-change-me-change-me-1234",
    "OMNI_AGENT_ADMIN_PASSWORD": "passw0rd",
    "OMNI_AGENT_DEVICE_KEY": "device-secret",
}

ISSUE_ORDER = [
    "DATABASE_URL",
    "POSTGRES_PASSWORD",
    "OMNI_AGENT_JWT_SECRET",
    "OMNI_AGENT_ADMIN_USERNAME",
    "OMNI_AGENT_ADMIN_PASSWORD",
    "VITE_GATEWAY_BASE_URL",
    "OMNI_AGENT_GATEWAY_URL",
    "OMNI_AGENT_DEVICE_KEYS",
    "OMNI_AGENT_DEVICE_ID",
    "OMNI_AGENT_DEVICE_KEY",
]

FIELD_META = {
    "DATABASE_URL": {
        "label": "Gateway 数据库连接",
        "service": "gateway",
        "secret": True,
        "help": "单独部署 Gateway 时填写。支持 PostgreSQL 连接串或 sqlite:///data/gateway/gateway.db。",
    },
    "POSTGRES_PASSWORD": {
        "label": "PostgreSQL 密码",
        "service": "postgres",
        "secret": True,
        "help": "内置 PostgreSQL 使用的密码。",
    },
    "OMNI_AGENT_JWT_SECRET": {
        "label": "JWT 密钥",
        "service": "gateway",
        "secret": True,
        "help": "Gateway 与 Dashboard/App 登录签名密钥。",
    },
    "OMNI_AGENT_ADMIN_USERNAME": {
        "label": "管理员账号",
        "service": "gateway",
        "secret": False,
        "help": "Dashboard 与 App 登录账号。",
    },
    "OMNI_AGENT_ADMIN_PASSWORD": {
        "label": "管理员密码",
        "service": "gateway",
        "secret": True,
        "help": "Dashboard 与 App 登录密码。",
    },
    "VITE_GATEWAY_BASE_URL": {
        "label": "Dashboard API 基地址",
        "service": "dashboard",
        "secret": False,
        "help": "单独部署 Dashboard 时填写浏览器可访问的 Gateway 地址，例如 https://gw.example.com/jarvis/api。",
    },
    "OMNI_AGENT_GATEWAY_URL": {
        "label": "Client Gateway 地址",
        "service": "client",
        "secret": False,
        "help": "单独部署 Client 时填写容器内可访问的 Gateway 地址，例如 http://192.168.1.10:8000。",
    },
    "OMNI_AGENT_DEVICE_KEYS": {
        "label": "设备注册表",
        "service": "gateway/client",
        "secret": False,
        "help": "格式：device-a=secret-a,device-b=secret-b",
    },
    "OMNI_AGENT_DEVICE_ID": {
        "label": "客户端设备 ID",
        "service": "client",
        "secret": False,
        "help": "Client 容器启动时使用的设备标识。",
    },
    "OMNI_AGENT_DEVICE_KEY": {
        "label": "客户端设备密钥",
        "service": "client",
        "secret": True,
        "help": "必须与 Gateway 注册表中的同名设备密钥一致。",
    },
}

MENU_ACTIONS = {
    "1": "config",
    "2": "deploy",
    "3": "status",
    "4": "logs",
    "5": "stop",
    "q": "quit",
    "quit": "quit",
    "exit": "quit",
}


@dataclass(frozen=True, slots=True)
class ConfigIssue:
    key: str
    reason: str
    prompt: str
    service: str
    secret: bool = False
    help_text: str | None = None


class UserAbort(Exception):
    pass


def normalize_targets(
    targets: tuple[str, ...] | list[str] | None = None,
    default_targets: tuple[str, ...] = FULL_STACK_SERVICES,
) -> tuple[str, ...]:
    if not targets:
        return default_targets

    normalized: list[str] = []
    for target in targets:
        for item in str(target).split(","):
            candidate = item.strip()
            if not candidate:
                continue
            if candidate == "all":
                return default_targets
            if candidate not in VALID_TARGETS:
                raise ValueError(f"Unsupported target: {candidate}")
            if candidate not in normalized:
                normalized.append(candidate)
    return tuple(normalized) or default_targets


def resolve_deploy_services(targets: tuple[str, ...] | list[str] | None = None) -> tuple[str, ...]:
    return normalize_targets(targets, default_targets=FULL_STACK_SERVICES)


def should_skip_compose_dependencies(targets: tuple[str, ...]) -> bool:
    return len(targets) == 1 and targets[0] in {"gateway", "client", "dashboard"}


def is_absolute_http_url(raw_value: str) -> bool:
    parsed = urlparse(raw_value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def has_compose_only_hostname(raw_value: str, hostnames: set[str]) -> bool:
    parsed = urlparse(raw_value)
    hostname = (parsed.hostname or "").lower()
    return hostname in hostnames


def database_url_needs_external_dependency(raw_value: str) -> bool:
    value = raw_value.strip()
    if not value:
        return True
    parsed = urlparse(value)
    if parsed.scheme.startswith("postgres") and (parsed.hostname or "").lower() == "postgres":
        return True
    return False


def apply_network_profile_defaults(
    effective: dict[str, str], current: Mapping[str, str] | None = None
) -> dict[str, str]:
    profile = effective.get("DEPLOY_NETWORK_PROFILE", "").strip() or "global"
    if profile not in {"global", "cn"}:
        profile = "global"
    effective["DEPLOY_NETWORK_PROFILE"] = profile

    source = dict(current or {})
    defaults = CN_PROFILE_DEFAULTS if profile == "cn" else GLOBAL_PROFILE_DEFAULTS
    inverse_defaults = GLOBAL_PROFILE_DEFAULTS if profile == "cn" else CN_PROFILE_DEFAULTS

    for key, default_value in defaults.items():
        existing = effective.get(key, "")
        current_value = source.get(key, "")
        if not current_value or existing == inverse_defaults[key] or existing == default_value:
            effective[key] = default_value
    return effective


def parse_env_text(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in raw_line:
            continue
        key, value = raw_line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def parse_device_keys(raw_value: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    seen: set[str] = set()
    for chunk in raw_value.split(","):
        item = chunk.strip()
        if not item:
            continue
        if "=" not in item:
            raise ValueError(f"Invalid device pair: {item}")
        device_id, device_key = item.split("=", 1)
        device_id = device_id.strip()
        device_key = device_key.strip()
        if not device_id or not device_key:
            raise ValueError(f"Invalid device pair: {item}")
        if device_id in seen:
            pairs = [(key, value) for key, value in pairs if key != device_id]
        pairs.append((device_id, device_key))
        seen.add(device_id)
    return pairs


def serialize_device_keys(pairs: list[tuple[str, str]]) -> str:
    return ",".join(f"{device_id}={device_key}" for device_id, device_key in pairs)


def build_effective_env(
    current: Mapping[str, str], template: Mapping[str, str] | None = None
) -> dict[str, str]:
    effective: dict[str, str] = dict(template or {})
    effective.update(dict(current))
    effective = apply_network_profile_defaults(effective, current=current)

    raw_registry = effective.get("OMNI_AGENT_DEVICE_KEYS", "")
    try:
        registry = parse_device_keys(raw_registry) if raw_registry.strip() else []
    except ValueError:
        registry = []

    device_id = effective.get("OMNI_AGENT_DEVICE_ID", "").strip()
    device_key = effective.get("OMNI_AGENT_DEVICE_KEY", "").strip()

    if device_id and device_key:
        registry = [(key, value) for key, value in registry if key != device_id]
        registry.append((device_id, device_key))
    elif device_id and not device_key:
        matched = next((value for key, value in registry if key == device_id), "")
        if matched:
            effective["OMNI_AGENT_DEVICE_KEY"] = matched
            device_key = matched
    elif not device_id and registry:
        first_device_id, first_device_key = registry[0]
        effective["OMNI_AGENT_DEVICE_ID"] = first_device_id
        effective["OMNI_AGENT_DEVICE_KEY"] = first_device_key
        device_id = first_device_id
        device_key = first_device_key
    elif device_id or device_key:
        if device_id and device_key:
            registry.append((device_id, device_key))

    if registry:
        effective["OMNI_AGENT_DEVICE_KEYS"] = serialize_device_keys(registry)

    return effective


def collect_config_issues(
    values: Mapping[str, str], targets: tuple[str, ...] | list[str] | None = None
) -> list[ConfigIssue]:
    issues: list[ConfigIssue] = []
    normalized_targets = normalize_targets(targets, default_targets=FULL_STACK_SERVICES)
    deploys_postgres = "postgres" in normalized_targets
    deploys_gateway = "gateway" in normalized_targets
    deploys_client = "client" in normalized_targets
    deploys_dashboard = "dashboard" in normalized_targets
    uses_external_database = deploys_gateway and "postgres" not in normalized_targets
    uses_remote_gateway_for_client = deploys_client and "gateway" not in normalized_targets
    uses_remote_gateway_for_dashboard = deploys_dashboard and "gateway" not in normalized_targets

    def add_issue(key: str, reason: str) -> None:
        meta = FIELD_META[key]
        issues.append(
            ConfigIssue(
                key=key,
                reason=reason,
                prompt=meta["label"],
                service=meta["service"],
                secret=bool(meta.get("secret", False)),
                help_text=meta.get("help"),
            )
        )

    if deploys_postgres:
        password = values.get("POSTGRES_PASSWORD", "").strip()
        if not password:
            add_issue("POSTGRES_PASSWORD", "missing")
        elif password == PLACEHOLDER_DEFAULTS["POSTGRES_PASSWORD"]:
            add_issue("POSTGRES_PASSWORD", "example_default")

    if uses_external_database and database_url_needs_external_dependency(
        values.get("DATABASE_URL", "")
    ):
        add_issue("DATABASE_URL", "standalone_dependency")

    if deploys_gateway:
        jwt_secret = values.get("OMNI_AGENT_JWT_SECRET", "").strip()
        if not jwt_secret:
            add_issue("OMNI_AGENT_JWT_SECRET", "missing")
        elif jwt_secret == PLACEHOLDER_DEFAULTS["OMNI_AGENT_JWT_SECRET"]:
            add_issue("OMNI_AGENT_JWT_SECRET", "example_default")

        if not values.get("OMNI_AGENT_ADMIN_USERNAME", "").strip():
            add_issue("OMNI_AGENT_ADMIN_USERNAME", "missing")

        admin_password = values.get("OMNI_AGENT_ADMIN_PASSWORD", "").strip()
        if not admin_password:
            add_issue("OMNI_AGENT_ADMIN_PASSWORD", "missing")
        elif admin_password == PLACEHOLDER_DEFAULTS["OMNI_AGENT_ADMIN_PASSWORD"]:
            add_issue("OMNI_AGENT_ADMIN_PASSWORD", "example_default")

    if uses_remote_gateway_for_dashboard:
        dashboard_gateway_url = values.get("VITE_GATEWAY_BASE_URL", "").strip()
        if not dashboard_gateway_url or not is_absolute_http_url(dashboard_gateway_url):
            add_issue("VITE_GATEWAY_BASE_URL", "standalone_dependency")
        elif has_compose_only_hostname(dashboard_gateway_url, {"gateway"}):
            add_issue("VITE_GATEWAY_BASE_URL", "standalone_dependency")

    if uses_remote_gateway_for_client:
        client_gateway_url = values.get("OMNI_AGENT_GATEWAY_URL", "").strip()
        if not client_gateway_url or not is_absolute_http_url(client_gateway_url):
            add_issue("OMNI_AGENT_GATEWAY_URL", "standalone_dependency")
        elif has_compose_only_hostname(client_gateway_url, {"gateway", "localhost"}):
            add_issue("OMNI_AGENT_GATEWAY_URL", "standalone_dependency")

    if deploys_client:
        registry_raw = values.get("OMNI_AGENT_DEVICE_KEYS", "").strip()
        registry: list[tuple[str, str]] = []
        if not uses_remote_gateway_for_client:
            if not registry_raw:
                add_issue("OMNI_AGENT_DEVICE_KEYS", "missing")
            else:
                try:
                    registry = parse_device_keys(registry_raw)
                except ValueError:
                    add_issue("OMNI_AGENT_DEVICE_KEYS", "invalid")

        device_id = values.get("OMNI_AGENT_DEVICE_ID", "").strip()
        if not device_id:
            add_issue("OMNI_AGENT_DEVICE_ID", "missing")

        device_key = values.get("OMNI_AGENT_DEVICE_KEY", "").strip()
        if not device_key:
            add_issue("OMNI_AGENT_DEVICE_KEY", "missing")
        elif device_key == PLACEHOLDER_DEFAULTS["OMNI_AGENT_DEVICE_KEY"]:
            add_issue("OMNI_AGENT_DEVICE_KEY", "example_default")

        if not uses_remote_gateway_for_client and device_id and device_key and registry:
            registry_map = dict(registry)
            if registry_map.get(device_id) != device_key:
                add_issue("OMNI_AGENT_DEVICE_KEYS", "contract_mismatch")

    ordered = sorted(issues, key=lambda issue: ISSUE_ORDER.index(issue.key))
    deduped: list[ConfigIssue] = []
    seen: set[str] = set()
    for issue in ordered:
        if issue.key in seen:
            continue
        deduped.append(issue)
        seen.add(issue.key)
    return deduped


def render_env_file(values: Mapping[str, str], template_text: str) -> str:
    lines: list[str] = []
    emitted: set[str] = set()

    for raw_line in template_text.splitlines():
        stripped = raw_line.strip()
        if stripped and not stripped.startswith("#") and "=" in raw_line:
            key, _ = raw_line.split("=", 1)
            key = key.strip()
            lines.append(f"{key}={values.get(key, '')}")
            emitted.add(key)
        else:
            lines.append(raw_line)

    extras = [key for key in values if key not in emitted]
    if extras:
        if lines and lines[-1] != "":
            lines.append("")
        for key in extras:
            lines.append(f"{key}={values[key]}")

    return "\n".join(lines).rstrip("\n") + "\n"


def build_compose_command(
    action: str, targets: tuple[str, ...] | list[str] | None = None
) -> list[str]:
    if action == "deploy":
        selected_targets = resolve_deploy_services(targets)
        command = ["docker", "compose", "up", "-d", "--build"]
        if should_skip_compose_dependencies(selected_targets):
            command.append("--no-deps")
        return [*command, *selected_targets]
    if action == "status":
        selected_targets = normalize_targets(targets, default_targets=FULL_STACK_SERVICES)
        return ["docker", "compose", "ps", *selected_targets]
    if action == "logs":
        selected_targets = normalize_targets(targets, default_targets=RUNTIME_SERVICES)
        return ["docker", "compose", "logs", "-f", *selected_targets]
    if action == "stop":
        selected_targets = normalize_targets(targets, default_targets=FULL_STACK_SERVICES)
        return ["docker", "compose", "stop", *selected_targets]
    raise ValueError(f"Unsupported action: {action}")


def load_env_state() -> tuple[dict[str, str], dict[str, str], str]:
    if not ENV_TEMPLATE_FILE.exists():
        raise FileNotFoundError(f"Missing template file: {ENV_TEMPLATE_FILE}")
    template_text = ENV_TEMPLATE_FILE.read_text(encoding="utf-8")
    template_values = parse_env_text(template_text)
    current_values = {}
    if ENV_FILE.exists():
        current_values = parse_env_text(ENV_FILE.read_text(encoding="utf-8"))
    effective = build_effective_env(current_values, template_values)
    return effective, template_values, template_text


def reason_text(reason: str) -> str:
    return {
        "missing": "未配置",
        "example_default": "仍是示例默认值",
        "invalid": "格式无效",
        "contract_mismatch": "与 Client/Gateway 协议不一致",
        "standalone_dependency": "当前为独立部署，请填写外部依赖地址",
    }.get(reason, reason)


def prompt_for_value(issue: ConfigIssue, current_value: str) -> tuple[str, bool]:
    note = reason_text(issue.reason)
    default_hint = "<已设置>" if issue.secret and current_value else current_value or "<空>"
    print()
    print(f"[{issue.service}] {issue.prompt} · {note}")
    if issue.help_text:
        print(f"提示：{issue.help_text}")
    if issue.reason == "example_default":
        print("说明：当前值还是示例值，建议现在改掉；直接回车可暂时保留。")
    if issue.reason == "contract_mismatch":
        print("说明：脚本会把 Gateway 设备注册表与 Client 设备身份自动对齐。")
    if issue.reason == "standalone_dependency":
        print("说明：当前目标未部署本地依赖，必须填写一个可直接连接的外部地址。")

    prompt = f"请输入（当前 {default_hint}）: "
    while True:
        try:
            raw_value = getpass.getpass(prompt) if issue.secret else input(prompt)
        except (EOFError, KeyboardInterrupt) as exc:
            raise UserAbort from exc
        if raw_value.strip():
            return raw_value.strip(), False
        if issue.reason == "example_default" and current_value:
            return current_value, issue.reason == "example_default"
        print("当前值仍不满足部署要求，请重新输入。")


def write_env(values: Mapping[str, str], template_text: str) -> None:
    ENV_FILE.write_text(render_env_file(values, template_text), encoding="utf-8")


def run_config_wizard(targets: tuple[str, ...] | list[str] | None = None) -> dict[str, str]:
    values, template_values, template_text = load_env_state()
    skipped_example_defaults: set[str] = set()
    print_header()
    print(f"配置文件：{ENV_FILE.relative_to(ROOT)}")
    if not ENV_FILE.exists():
        print("检测到 .env 不存在，将基于 .env.example 自动生成。")

    while True:
        values = build_effective_env(values, template_values)
        issues = [
            issue
            for issue in collect_config_issues(values, targets=targets)
            if not (issue.reason == "example_default" and issue.key in skipped_example_defaults)
        ]
        if not issues:
            write_env(values, template_text)
            print("\n✅ 配置检查通过，已写入 .env")
            return values

        print("\n待处理配置项：")
        for issue in issues:
            print(f"- {issue.key}: {reason_text(issue.reason)}")

        issue = issues[0]
        current_value = values.get(issue.key, "")
        new_value, skipped = prompt_for_value(issue, current_value)
        if skipped:
            skipped_example_defaults.add(issue.key)
        else:
            skipped_example_defaults.discard(issue.key)
        values[issue.key] = new_value
        values = build_effective_env(values, template_values)
        write_env(values, template_text)
        print("已更新 .env，继续检查剩余配置…")


def print_header() -> None:
    print("╔══════════════════════════════╗")
    print("║   OpenJarvis 部署助手 v1    ║")
    print("╚══════════════════════════════╝")


def print_access_summary(
    values: Mapping[str, str], targets: tuple[str, ...] | list[str] | None = None
) -> None:
    selected_targets = normalize_targets(targets, default_targets=FULL_STACK_SERVICES)
    dashboard_port = values.get("DASHBOARD_PORT", "8080") or "8080"
    gateway_port = values.get("GATEWAY_PORT", "8000") or "8000"
    print("\n访问入口：")
    if "dashboard" in selected_targets:
        print(f"- Dashboard: http://localhost:{dashboard_port}/jarvis/dashboard/")
    if "gateway" in selected_targets:
        print(f"- Gateway 健康检查: http://localhost:{gateway_port}/health")
    if selected_targets == ("client",):
        print(f"- Client 远端 Gateway: {values.get('OMNI_AGENT_GATEWAY_URL', '<未配置>')}")


def require_docker() -> None:
    if shutil.which("docker") is None:
        raise SystemExit("未检测到 docker，请先安装 Docker / Docker Compose。")
    probe = subprocess.run(
        ["docker", "compose", "version"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if probe.returncode != 0:
        raise SystemExit("检测不到 `docker compose`，请确认 Docker Compose 已可用。")


def run_compose_action(
    action: str, targets: tuple[str, ...] | list[str] | None = None
) -> int:
    require_docker()
    command = build_compose_command(action, targets=targets)
    print(f"\n$ {' '.join(command)}")
    result = subprocess.run(command, cwd=ROOT, check=False)
    return result.returncode


def interactive_menu() -> int:
    while True:
        try:
            values, template_values, _ = load_env_state()
        except FileNotFoundError as exc:
            print(str(exc))
            return 1
        values = build_effective_env(values, template_values)
        issues = collect_config_issues(values)

        print_header()
        status_line = (
            f"当前配置状态：待处理 {len(issues)} 项" if issues else "当前配置状态：已就绪"
        )
        print(status_line)
        print()
        print("1) 检查并补全 .env")
        print("2) 更新并启动 postgres / gateway / client / dashboard")
        print("3) 查看服务状态")
        print("4) 跟踪实时日志")
        print("5) 停止目标容器")
        print("q) 退出")
        try:
            choice = input("\n请选择操作: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return 130

        action = MENU_ACTIONS.get(choice)
        if action is None:
            print("无效选择，请输入 1/2/3/4/5/q。\n")
            continue
        if action == "quit":
            return 0
        if action == "config":
            try:
                run_config_wizard()
            except UserAbort:
                print("\n已取消配置。")
            print()
            continue
        if action == "deploy":
            try:
                values = run_config_wizard()
            except UserAbort:
                print("\n已取消部署。")
                return 130
            return_code = run_compose_action("deploy")
            if return_code == 0:
                print_access_summary(values)
            return return_code
        return run_compose_action(action)


def run_non_interactive(
    action: str, targets: tuple[str, ...] | list[str] | None = None
) -> int:
    if action == "config":
        try:
            run_config_wizard(targets=targets)
            return 0
        except UserAbort:
            return 130
    if action == "deploy":
        try:
            values = run_config_wizard(targets=targets)
        except UserAbort:
            return 130
        return_code = run_compose_action("deploy", targets=targets)
        if return_code == 0:
            print_access_summary(values, targets=targets)
        return return_code
    return run_compose_action(action, targets=targets)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="OpenJarvis 一站式部署助手：检查 .env、补全配置并按需更新 postgres/gateway/client/dashboard。"
    )
    parser.add_argument(
        "action",
        nargs="?",
        choices=("menu", "config", "deploy", "status", "logs", "stop"),
        default="menu",
        help="默认进入交互式 TUI 菜单。",
    )
    parser.add_argument(
        "targets",
        nargs="*",
        help="可选目标：postgres / gateway / client / dashboard / all",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.action == "menu":
            return interactive_menu()
        return run_non_interactive(args.action, targets=tuple(args.targets))
    except UserAbort:
        print("\n已取消。")
        return 130


if __name__ == "__main__":
    sys.exit(main())
