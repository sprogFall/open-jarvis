from client.config import ClientConfig
from client.service import ClientService


class RecordingRunner:
    def __init__(self) -> None:
        self.assignments: list[tuple[str, str]] = []
        self.approvals: list[tuple[str, bool]] = []

    def handle_assignment(self, task_id: str, instruction: str) -> None:
        self.assignments.append((task_id, instruction))

    def handle_approval(self, task_id: str, approved: bool) -> None:
        self.approvals.append((task_id, approved))


class RecordingSkillWorkspace:
    def __init__(self) -> None:
        self.syncs: list[list[dict]] = []

    def sync(self, skills: list[dict]) -> None:
        self.syncs.append(skills)


class RecordingAIConfigStore:
    def __init__(self) -> None:
        self.saved: list[dict] = []
        self.deleted = 0

    def save_ai_config(self, payload: dict) -> None:
        self.saved.append(payload)

    def delete_ai_config(self) -> None:
        self.deleted += 1


def test_service_routes_gateway_messages_to_runner():
    runner = RecordingRunner()
    workspace = RecordingSkillWorkspace()
    config = ClientConfig()
    service = ClientService(runner=runner, transport=None, config=config, skill_workspace=workspace)

    service.handle_gateway_message(
        {
            "type": "TASK_ASSIGNED",
            "task": {
                "task_id": "task-1",
                "instruction": "查看系统负载",
            },
        }
    )
    service.handle_gateway_message(
        {
            "type": "APPROVAL_DECISION",
            "task_id": "task-1",
            "approved": True,
        }
    )

    assert runner.assignments == [("task-1", "查看系统负载")]
    assert runner.approvals == [("task-1", True)]
    assert workspace.syncs == []


def test_service_routes_skill_sync_messages_to_workspace():
    runner = RecordingRunner()
    workspace = RecordingSkillWorkspace()
    config = ClientConfig()
    service = ClientService(runner=runner, transport=None, config=config, skill_workspace=workspace)

    service.handle_gateway_message(
        {
            "type": "DEVICE_SKILLS_SYNC",
            "device_id": "device-alpha",
            "skills": [
                {
                    "skill_id": "incident-kit",
                    "config": {"workspace": ".codex/skills"},
                    "archive_sha256": "abc123",
                    "archive_ready": True,
                    "download_path": "/client/skills/incident-kit/archive",
                }
            ],
        }
    )

    assert runner.assignments == []
    assert runner.approvals == []
    assert workspace.syncs == [
        [
            {
                "skill_id": "incident-kit",
                "config": {"workspace": ".codex/skills"},
                "archive_sha256": "abc123",
                "archive_ready": True,
                "download_path": "/client/skills/incident-kit/archive",
            }
        ]
    ]


def test_service_routes_ai_config_sync_messages_to_store():
    runner = RecordingRunner()
    workspace = RecordingSkillWorkspace()
    ai_config_store = RecordingAIConfigStore()
    config = ClientConfig()
    service = ClientService(
        runner=runner,
        transport=None,
        config=config,
        skill_workspace=workspace,
        ai_config_store=ai_config_store,
    )

    service.handle_gateway_message(
        {
            "type": "DEVICE_AI_CONFIG_SYNC",
            "device_id": "device-alpha",
            "config": {
                "provider": "custom",
                "model": "qwen-max",
                "api_key": "client-secret",
                "base_url": "https://llm.example/v1/chat/completions",
            },
        }
    )
    service.handle_gateway_message(
        {
            "type": "DEVICE_AI_CONFIG_SYNC",
            "device_id": "device-alpha",
            "config": None,
        }
    )

    assert runner.assignments == []
    assert runner.approvals == []
    assert workspace.syncs == []
    assert ai_config_store.saved == [
        {
            "provider": "custom",
            "model": "qwen-max",
            "api_key": "client-secret",
            "base_url": "https://llm.example/v1/chat/completions",
        }
    ]
    assert ai_config_store.deleted == 1
