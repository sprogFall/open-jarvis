from __future__ import annotations

from client.checkpoints import CheckpointStore
from client.planner import LLMPlanner


class FakeModelClient:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.calls: list[tuple[str, str]] = []

    def generate_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        self.calls.append((system_prompt, user_prompt))
        return self.payload


def test_checkpoint_store_persists_ai_override(tmp_path):
    store = CheckpointStore(tmp_path / "client.db")

    store.save_ai_config(
        {
            "provider": "custom",
            "model": "deepseek-chat",
            "api_key": "client-secret",
            "base_url": "https://llm.example/v1/chat/completions",
        }
    )

    restarted = CheckpointStore(tmp_path / "client.db")
    assert restarted.load_ai_config() == {
        "provider": "custom",
        "model": "deepseek-chat",
        "api_key": "client-secret",
        "base_url": "https://llm.example/v1/chat/completions",
    }

    restarted.delete_ai_config()
    assert restarted.load_ai_config() is None


def test_llm_planner_uses_model_output_when_ai_config_exists():
    model_client = FakeModelClient(
        {
            "actions": [
                {
                    "name": "process.inspect_load",
                    "command": "inspect system load",
                    "args": {},
                    "requires_approval": False,
                    "reason": None,
                },
                {
                    "name": "docker.restart",
                    "command": "docker restart api-service",
                    "args": {"container": "api-service"},
                    "requires_approval": True,
                    "reason": "重启容器会影响服务可用性",
                },
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
    )

    actions = planner.plan("查看系统负载，然后重启容器 api-service")

    assert [action.name for action in actions] == [
        "process.inspect_load",
        "docker.restart",
    ]
    assert actions[1].requires_approval is True
    assert "查看系统负载" in model_client.calls[0][1]


def test_llm_planner_falls_back_to_rule_based_when_no_ai_config():
    planner = LLMPlanner(
        config_resolver=lambda: None,
        model_client_factory=lambda _config: None,
    )

    actions = planner.plan("查看系统负载，然后重启容器 api-service")

    assert [action.name for action in actions] == [
        "process.inspect_load",
        "docker.restart",
    ]
