from __future__ import annotations

from client.ai import AIModelConfig
from client.checkpoints import CheckpointStore
from client.planner import LLMPlanner


class FakeModelClient:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.calls: list[tuple[str, str]] = []

    def generate_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        self.calls.append((system_prompt, user_prompt))
        return self.payload


def test_ai_model_config_ignores_none_fields():
    assert AIModelConfig.from_dict(
        {"provider": None, "model": None, "api_key": None}
    ) is None


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


def test_checkpoint_store_isolates_ai_overrides_by_scope_when_sharing_one_database(tmp_path):
    database_path = tmp_path / "shared-client.db"
    alpha_store = CheckpointStore(database_path, ai_scope="device-alpha")
    beta_store = CheckpointStore(database_path, ai_scope="device-beta")

    alpha_store.save_ai_config(
        {
            "provider": "custom",
            "model": "qwen-max",
            "api_key": "alpha-secret",
            "base_url": "https://alpha.example/v1/chat/completions",
        }
    )
    beta_store.save_ai_config(
        {
            "provider": "custom",
            "model": "deepseek-chat",
            "api_key": "beta-secret",
            "base_url": "https://beta.example/v1/chat/completions",
        }
    )

    assert alpha_store.load_ai_config() == {
        "provider": "custom",
        "model": "qwen-max",
        "api_key": "alpha-secret",
        "base_url": "https://alpha.example/v1/chat/completions",
    }
    assert beta_store.load_ai_config() == {
        "provider": "custom",
        "model": "deepseek-chat",
        "api_key": "beta-secret",
        "base_url": "https://beta.example/v1/chat/completions",
    }

    alpha_store.delete_ai_config()

    assert alpha_store.load_ai_config() is None
    assert beta_store.load_ai_config() == {
        "provider": "custom",
        "model": "deepseek-chat",
        "api_key": "beta-secret",
        "base_url": "https://beta.example/v1/chat/completions",
    }


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


def test_llm_planner_normalizes_shell_intent_into_real_command():
    model_client = FakeModelClient(
        {
            "actions": [
                {
                    "name": "shell.exec",
                    "command": "查看本机工作目录",
                    "args": {"command": "查看本机工作目录"},
                    "requires_approval": True,
                    "reason": "需要在终端查看当前目录",
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
    )

    actions = planner.plan("查看本机工作目录")

    assert [action.name for action in actions] == ["shell.exec"]
    assert actions[0].command == "pwd"
    assert actions[0].args == {"command": "pwd"}


def test_llm_planner_normalizes_docker_command_instead_of_preserving_chinese():
    model_client = FakeModelClient(
        {
            "actions": [
                {
                    "name": "docker.restart",
                    "command": "重启容器 api-service",
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
    )

    actions = planner.plan("重启容器 api-service")

    assert [action.name for action in actions] == ["docker.restart"]
    assert actions[0].command == "docker restart api-service"
    assert actions[0].args == {"container": "api-service"}


def test_llm_planner_rejects_natural_language_shell_command_from_model():
    model_client = FakeModelClient(
        {
            "actions": [
                {
                    "name": "shell.exec",
                    "command": "帮我查看一下服务器状态",
                    "args": {"command": "帮我查看一下服务器状态"},
                    "requires_approval": True,
                    "reason": "需要进入终端查看",
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
    )

    try:
        planner.plan("帮我查看一下服务器状态")
    except ValueError as exc:
        assert "shell command" in str(exc)
    else:
        raise AssertionError("expected planner to reject non-executable shell command")
