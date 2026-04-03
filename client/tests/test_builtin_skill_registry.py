from __future__ import annotations

import pytest

from client.config import ClientConfig
from client.models import TaskAction
from client.planner import LLMPlanner
from client.service import build_default_registry


class FakeModelClient:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.calls: list[tuple[str, str]] = []

    def generate_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        self.calls.append((system_prompt, user_prompt))
        return self.payload


def test_llm_planner_only_exposes_enabled_builtin_actions(tmp_path):
    registry = build_default_registry(
        ClientConfig(allowed_roots=[tmp_path]),
        enable_builtin_by_default=False,
    )
    registry.sync_skills(
        [
            {
                "skill_id": "builtin-docker",
                "source": "builtin",
            }
        ]
    )
    model_client = FakeModelClient(
        {
            "actions": [
                {
                    "name": "docker.restart",
                    "command": "docker restart api-service",
                    "args": {"container": "api-service"},
                    "requires_approval": True,
                    "reason": "重启容器会影响服务可用性",
                }
            ]
        }
    )
    planner = LLMPlanner(
        config_resolver=lambda: {
            "provider": "custom",
            "model": "qwen-max",
            "api_key": "client-secret",
            "base_url": "https://llm.example/v1/chat/completions",
        },
        model_client_factory=lambda _config: model_client,
        action_catalog_provider=registry.available_actions,
    )

    planner.plan("重启容器 api-service")

    system_prompt = model_client.calls[0][0]
    assert "docker.restart" in system_prompt
    assert "docker.list_containers" in system_prompt
    assert "shell.exec" not in system_prompt
    assert "filesystem.read_file" not in system_prompt


def test_registry_rejects_action_from_disabled_builtin_skill(tmp_path):
    registry = build_default_registry(
        ClientConfig(allowed_roots=[tmp_path]),
        enable_builtin_by_default=False,
    )
    registry.sync_skills(
        [
            {
                "skill_id": "builtin-docker",
                "source": "builtin",
            }
        ]
    )

    with pytest.raises(PermissionError):
        registry.execute(
            TaskAction(
                name="shell.exec",
                command="pwd",
                args={"command": "pwd"},
                requires_approval=True,
                reason="manual shell fallback",
            )
        )
