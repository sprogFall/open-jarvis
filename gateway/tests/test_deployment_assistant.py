from __future__ import annotations

import os
import subprocess
from pathlib import Path

from jarvisctl import (
    build_compose_command,
    build_effective_env,
    collect_config_issues,
    parse_env_text,
    render_env_file,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
JARVISCTL_PATH = PROJECT_ROOT / "jarvisctl"


def _read(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def test_build_effective_env_syncs_device_contract_between_gateway_and_client():
    template = parse_env_text(_read(".env.example"))
    current = {
        "OMNI_AGENT_DEVICE_KEYS": "device-alpha=alpha-secret",
        "OMNI_AGENT_DEVICE_ID": "device-beta",
        "OMNI_AGENT_DEVICE_KEY": "beta-secret",
    }

    effective = build_effective_env(current, template)

    assert effective["OMNI_AGENT_DEVICE_ID"] == "device-beta"
    assert effective["OMNI_AGENT_DEVICE_KEY"] == "beta-secret"
    assert effective["OMNI_AGENT_DEVICE_KEYS"] == (
        "device-alpha=alpha-secret,device-beta=beta-secret"
    )


def test_build_effective_env_derives_client_device_pair_from_gateway_registry_when_missing():
    effective = build_effective_env(
        {"OMNI_AGENT_DEVICE_KEYS": "device-beta=beta-secret,device-alpha=alpha-secret"},
        {},
    )

    assert effective["OMNI_AGENT_DEVICE_ID"] == "device-beta"
    assert effective["OMNI_AGENT_DEVICE_KEY"] == "beta-secret"


def test_collect_config_issues_flags_example_defaults_for_sensitive_values():
    issues = {
        issue.key: issue.reason
        for issue in collect_config_issues(
            {
                "POSTGRES_PASSWORD": "jarvis",
                "OMNI_AGENT_JWT_SECRET": "change-me-change-me-change-me-1234",
                "OMNI_AGENT_ADMIN_USERNAME": "operator",
                "OMNI_AGENT_ADMIN_PASSWORD": "passw0rd",
                "OMNI_AGENT_DEVICE_KEYS": "device-alpha=device-secret",
                "OMNI_AGENT_DEVICE_ID": "device-alpha",
                "OMNI_AGENT_DEVICE_KEY": "device-secret",
            }
        )
    }

    assert issues["POSTGRES_PASSWORD"] == "example_default"
    assert issues["OMNI_AGENT_JWT_SECRET"] == "example_default"
    assert issues["OMNI_AGENT_ADMIN_PASSWORD"] == "example_default"
    assert issues["OMNI_AGENT_DEVICE_KEY"] == "example_default"


def test_collect_config_issues_only_requires_client_contract_for_client_targets():
    issues = {
        issue.key: issue.reason
        for issue in collect_config_issues(
            {
                "POSTGRES_PASSWORD": "pg-secret",
                "OMNI_AGENT_JWT_SECRET": "jwt-secret",
                "OMNI_AGENT_ADMIN_USERNAME": "operator",
                "OMNI_AGENT_ADMIN_PASSWORD": "admin-secret",
            },
            targets=("gateway",),
        )
    }

    assert "OMNI_AGENT_DEVICE_KEYS" not in issues
    assert "OMNI_AGENT_DEVICE_ID" not in issues
    assert "OMNI_AGENT_DEVICE_KEY" not in issues


def test_render_env_file_preserves_template_order_and_appends_unknown_keys():
    rendered = render_env_file(
        {"POSTGRES_DB": "prod", "OMNI_AGENT_ADMIN_USERNAME": "alice", "EXTRA_FLAG": "1"},
        "POSTGRES_DB=jarvis\n# comment\nOMNI_AGENT_ADMIN_USERNAME=operator\n",
    )

    assert rendered.splitlines() == [
        "POSTGRES_DB=prod",
        "# comment",
        "OMNI_AGENT_ADMIN_USERNAME=alice",
        "",
        "EXTRA_FLAG=1",
    ]


def test_build_compose_command_targets_full_stack_services():
    assert build_compose_command("deploy") == [
        "docker",
        "compose",
        "up",
        "-d",
        "--build",
        "postgres",
        "gateway",
        "client",
        "dashboard",
    ]
    assert build_compose_command("logs") == [
        "docker",
        "compose",
        "logs",
        "-f",
        "gateway",
        "client",
        "dashboard",
    ]


def test_build_compose_command_can_target_selected_services():
    assert build_compose_command("deploy", ("gateway",)) == [
        "docker",
        "compose",
        "up",
        "-d",
        "--build",
        "postgres",
        "gateway",
    ]
    assert build_compose_command("deploy", ("dashboard",)) == [
        "docker",
        "compose",
        "up",
        "-d",
        "--build",
        "postgres",
        "gateway",
        "dashboard",
    ]
    assert build_compose_command("deploy", ("client",)) == [
        "docker",
        "compose",
        "up",
        "-d",
        "--build",
        "postgres",
        "gateway",
        "client",
    ]
    assert build_compose_command("logs", ("dashboard",)) == [
        "docker",
        "compose",
        "logs",
        "-f",
        "dashboard",
    ]


def test_shell_script_is_linux_friendly_and_contains_compose_actions():
    script = JARVISCTL_PATH.read_text(encoding="utf-8")

    assert script.startswith("#!/usr/bin/env bash")
    assert "COMPOSE_CMD=(docker compose up -d --build" in script
    assert "usage: ./jarvisctl [menu|config|deploy|status|logs|stop] [targets...]" in script
    assert "检查并补全 .env" in script
    assert "python3 \"$SCRIPT_DIR/jarvisctl.py\"" not in script


def test_shell_script_can_fill_missing_env_file_from_prompts_for_gateway_only(
    tmp_path: Path,
):
    template_path = tmp_path / ".env.example"
    env_path = tmp_path / ".env"
    template_path.write_text(_read(".env.example"), encoding="utf-8")

    answers = "\n".join(
        [
            "pg-secret-001",
            "jwt-secret-001",
            "admin-pass-001",
        ]
    )

    env = os.environ | {
        "JARVISCTL_ENV_FILE": str(env_path),
        "JARVISCTL_ENV_TEMPLATE": str(template_path),
        "TERM": "dumb",
    }
    result = subprocess.run(
        [str(JARVISCTL_PATH), "config", "gateway"],
        input=answers + "\n",
        text=True,
        capture_output=True,
        cwd=PROJECT_ROOT,
        env=env,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    rendered = env_path.read_text(encoding="utf-8")
    assert "POSTGRES_PASSWORD=pg-secret-001" in rendered
    assert "OMNI_AGENT_JWT_SECRET=jwt-secret-001" in rendered
    assert "OMNI_AGENT_ADMIN_PASSWORD=admin-pass-001" in rendered
    assert "OMNI_AGENT_DEVICE_KEY=device-secret" in rendered
    assert "OMNI_AGENT_DEVICE_KEYS=device-alpha=device-secret" in rendered


def test_shell_script_can_resolve_selected_deploy_targets_in_dry_run(tmp_path: Path):
    template_path = tmp_path / ".env.example"
    env_path = tmp_path / ".env"
    template_path.write_text(_read(".env.example"), encoding="utf-8")
    env_path.write_text(
        "\n".join(
            [
                "POSTGRES_PASSWORD=pg-secret-001",
                "OMNI_AGENT_JWT_SECRET=jwt-secret-001",
                "OMNI_AGENT_ADMIN_USERNAME=operator",
                "OMNI_AGENT_ADMIN_PASSWORD=admin-pass-001",
                "OMNI_AGENT_DEVICE_KEYS=device-alpha=device-secret",
                "OMNI_AGENT_DEVICE_ID=device-alpha",
                "OMNI_AGENT_DEVICE_KEY=device-secret",
                "",
            ]
        ),
        encoding="utf-8",
    )

    env = os.environ | {
        "JARVISCTL_ENV_FILE": str(env_path),
        "JARVISCTL_ENV_TEMPLATE": str(template_path),
        "JARVISCTL_DRY_RUN": "1",
        "TERM": "dumb",
    }
    result = subprocess.run(
        [str(JARVISCTL_PATH), "deploy", "dashboard"],
        text=True,
        capture_output=True,
        cwd=PROJECT_ROOT,
        env=env,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "docker compose up -d --build postgres gateway dashboard" in result.stdout


def test_fastapi_requirement_uses_mirror_friendly_lower_bound():
    assert "fastapi>=0.115,<1" in _read("requirements.txt")
    assert "fastapi>=0.115,<1" in _read("gateway/requirements.txt")
    assert "fastapi>=0.135,<1" not in _read("requirements.txt")
    assert "fastapi>=0.135,<1" not in _read("gateway/requirements.txt")



def test_deployment_assistant_scripts_and_docs_exist():
    assert (PROJECT_ROOT / "jarvisctl").exists()
    assert "./jarvisctl" in _read("README.md")
    assert "./jarvisctl" in _read("dashboard/DEPLOYMENT.md")
