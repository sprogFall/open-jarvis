from __future__ import annotations

import json
import subprocess
import time

from client.checkpoints import CheckpointStore
from client.config import ClientConfig
from client.planner import LLMPlanner
from client.security import build_device_signature
from client.skill_runtime import GatewaySkillArchiveFetcher, SkillWorkspaceManager
from client.skills import DockerSkill, FileSystemSkill, IoTSkill, ProcessSkill

try:
    from websockets.sync.client import connect as ws_connect
except Exception:  # pragma: no cover - optional runtime dependency during tests
    ws_connect = None


class WebSocketTransport:
    def __init__(self, connection) -> None:
        self.connection = connection

    def send(self, payload: dict) -> None:
        self.connection.send(json.dumps(payload, ensure_ascii=False))


class NullTransport:
    def send(self, payload: dict) -> None:
        del payload


def build_default_registry(config: ClientConfig):
    from client.runtime import ActionRegistry

    registry = ActionRegistry()
    filesystem = FileSystemSkill(config.allowed_roots)
    process = ProcessSkill()
    docker = DockerSkill()
    iot = IoTSkill(config.iot_base_url, config.iot_token)

    registry.register("filesystem.read_file", lambda action: filesystem.read_file(action.args["path"]))
    registry.register(
        "filesystem.search_suffix",
        lambda action: filesystem.search_suffix(action.args["suffix"]),
    )
    registry.register("process.inspect_load", lambda _action: process.inspect_load())
    registry.register("process.list_processes", lambda _action: process.list_processes())
    registry.register(
        "docker.list_containers",
        lambda action: docker.list_containers(action.args.get("include_all", False)),
    )
    registry.register(
        "docker.restart",
        lambda action: docker.restart_container(action.args["container"]),
    )
    registry.register(
        "iot.set_state",
        lambda action: iot.set_device_state(action.args["entity_id"], action.args["state"]),
    )
    registry.register("shell.exec", _build_shell_handler())
    return registry


def _build_shell_handler():
    def execute_shell(action) -> str:
        result = subprocess.run(
            ["bash", "-lc", action.args["command"]],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"Command failed: {action.command}")
        return result.stdout.strip() or result.stderr.strip() or "Command completed"

    return execute_shell


class ClientService:
    def __init__(self, runner, transport, skill_workspace=None, ai_config_store=None) -> None:
        self.runner = runner
        self.transport = transport
        self.skill_workspace = skill_workspace
        self.ai_config_store = ai_config_store

    def handle_gateway_message(self, payload: dict) -> None:
        message_type = payload.get("type")
        if message_type == "TASK_ASSIGNED":
            task = payload["task"]
            self.runner.handle_assignment(task["task_id"], task["instruction"])
        elif message_type == "APPROVAL_DECISION":
            self.runner.handle_approval(payload["task_id"], bool(payload["approved"]))
        elif message_type == "DEVICE_SKILLS_SYNC" and self.skill_workspace is not None:
            self.skill_workspace.sync(payload.get("skills", []))
        elif message_type == "DEVICE_AI_CONFIG_SYNC" and self.ai_config_store is not None:
            config = payload.get("config")
            if config:
                self.ai_config_store.save_ai_config(config)
            else:
                self.ai_config_store.delete_ai_config()


def create_default_service(config: ClientConfig | None = None) -> ClientService:
    from client.runtime import TaskRunner

    config = config or ClientConfig.from_env()
    checkpoint_store = CheckpointStore(config.checkpoint_path)
    registry = build_default_registry(config)
    transport = NullTransport()
    skill_workspace = SkillWorkspaceManager(
        workspace_root=config.skills_workspace,
        archive_fetcher=GatewaySkillArchiveFetcher(config),
    )
    runner = TaskRunner(
        planner=LLMPlanner(
            config_resolver=lambda: checkpoint_store.load_ai_config() or config.ai_config(),
        ),
        registry=registry,
        transport=transport,
        checkpoints=checkpoint_store,
        workflow_store_path=config.workflow_store_path,
    )
    return ClientService(
        runner=runner,
        transport=transport,
        skill_workspace=skill_workspace,
        ai_config_store=checkpoint_store,
    )


def run_forever(config: ClientConfig | None = None) -> None:
    from client.runtime import TaskRunner

    config = config or ClientConfig.from_env()
    if ws_connect is None:
        raise RuntimeError("websockets is required to run the client service")

    checkpoint_store = CheckpointStore(config.checkpoint_path)
    registry = build_default_registry(config)
    planner = LLMPlanner(
        config_resolver=lambda: checkpoint_store.load_ai_config() or config.ai_config(),
    )
    skill_workspace = SkillWorkspaceManager(
        workspace_root=config.skills_workspace,
        archive_fetcher=GatewaySkillArchiveFetcher(config),
    )

    while True:
        timestamp = int(time.time())
        signature = build_device_signature(config.device_id, timestamp, config.device_key)
        ws_url = (
            f"{config.gateway_ws_url}/ws/client"
            f"?device_id={config.device_id}&timestamp={timestamp}&signature={signature}"
        )
        try:
            with ws_connect(ws_url, open_timeout=5) as connection:
                transport = WebSocketTransport(connection)
                runner = TaskRunner(
                    planner=planner,
                    registry=registry,
                    transport=transport,
                    checkpoints=checkpoint_store,
                    workflow_store_path=config.workflow_store_path,
                )
                try:
                    service = ClientService(
                        runner=runner,
                        transport=transport,
                        skill_workspace=skill_workspace,
                        ai_config_store=checkpoint_store,
                    )
                    for raw_message in connection:
                        service.handle_gateway_message(json.loads(raw_message))
                finally:
                    runner.close()
        except KeyboardInterrupt:
            raise
        except Exception:
            time.sleep(2)


if __name__ == "__main__":
    run_forever()
