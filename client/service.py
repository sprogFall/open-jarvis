from __future__ import annotations

import json
import subprocess
import time

from pathlib import Path

from client.checkpoints import CheckpointStore
from client.config import ClientConfig
from client.planner import LLMPlanner
from client.security import build_device_signature
from client.skill_runtime import GatewaySkillArchiveFetcher, SkillWorkspaceManager
from client.skills import DockerSkill, FileSystemSkill, IoTSkill, ProcessSkill
from skill_catalog import BUILTIN_SKILLS, builtin_skill_ids

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


def _build_ai_call_sink(transport, device_id: str):
    def sink(payload: dict) -> None:
        transport.send(
            {
                "type": "AI_CALL_LOG",
                "device_id": device_id,
                **payload,
            }
        )

    return sink


def merge_skill_config(
    skill_id: str,
    skill_config: dict,
    assignment_config: dict,
    client_config: ClientConfig,
) -> dict:
    """
    合并skill配置，优先级：assignment_config > skill_config > env > defaults
    """
    merged = {}

    if skill_id == "builtin-filesystem":
        roots = (
            assignment_config.get("allowed_roots")
            or skill_config.get("allowed_roots")
            or client_config.allowed_roots
        )
        if isinstance(roots, str):
            roots = [Path(r.strip()) for r in roots.split(",") if r.strip()]
        merged["allowed_roots"] = roots

    elif skill_id == "builtin-iot":
        merged["base_url"] = (
            assignment_config.get("base_url")
            or skill_config.get("base_url")
            or client_config.iot_base_url
        )
        merged["token"] = (
            assignment_config.get("token")
            or skill_config.get("token")
            or client_config.iot_token
        )

    return merged


def build_default_registry(
    config: ClientConfig,
    device_skills: list[dict] | None = None,
    *,
    enable_builtin_by_default: bool = True,
):
    from client.runtime import ActionRegistry

    skill_configs = {}
    if device_skills:
        for skill in device_skills:
            if skill.get("source") == "builtin":
                merged = merge_skill_config(
                    skill_id=skill["skill_id"],
                    skill_config=skill.get("skill_config") or {},
                    assignment_config=skill.get("config") or {},
                    client_config=config,
                )
                skill_configs[skill["skill_id"]] = merged

    registry = ActionRegistry(
        enabled_skill_ids=set(builtin_skill_ids()) if enable_builtin_by_default else set()
    )
    fs_config = skill_configs.get("builtin-filesystem", {})
    filesystem = FileSystemSkill(
        allowed_roots=fs_config.get("allowed_roots", config.allowed_roots)
    )
    process = ProcessSkill()
    docker = DockerSkill()
    iot_config = skill_configs.get("builtin-iot", {})
    iot = IoTSkill(
        base_url=iot_config.get("base_url", config.iot_base_url),
        token=iot_config.get("token", config.iot_token),
    )
    action_handlers = {
        "filesystem.read_file": lambda action: filesystem.read_file(action.args["path"]),
        "filesystem.search_suffix": lambda action: filesystem.search_suffix(action.args["suffix"]),
        "process.inspect_load": lambda _action: process.inspect_load(),
        "process.list_processes": lambda _action: process.list_processes(),
        "docker.list_containers": lambda action: docker.list_containers(
            action.args.get("include_all", False)
        ),
        "docker.restart": lambda action: docker.restart_container(action.args["container"]),
        "shell.exec": _build_shell_handler(),
    }

    for skill in BUILTIN_SKILLS:
        for action_spec in skill.actions:
            registry.register(
                action_spec.name,
                action_handlers[action_spec.name],
                action_spec=action_spec,
            )
    registry.register(
        "iot.set_state",
        lambda action: iot.set_device_state(action.args["entity_id"], action.args["state"]),
    )
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
    def __init__(
        self,
        runner,
        transport,
        config: ClientConfig,
        skill_workspace=None,
        ai_config_store=None,
        skill_registry=None,
    ) -> None:
        self.runner = runner
        self.transport = transport
        self.config = config
        self.skill_workspace = skill_workspace
        self.ai_config_store = ai_config_store
        self.skill_registry = skill_registry

    def handle_gateway_message(self, payload: dict) -> None:
        message_type = payload.get("type")
        if message_type == "TASK_ASSIGNED":
            task = payload["task"]
            self.runner.handle_assignment(task["task_id"], task["instruction"])
        elif message_type == "APPROVAL_DECISION":
            self.runner.handle_approval(payload["task_id"], bool(payload["approved"]))
        elif message_type == "DEVICE_SKILLS_SYNC":
            skills = payload.get("skills", [])
            if self.skill_registry is not None:
                self.skill_registry.sync_skills(skills)
                self._rebuild_registry(skills)
            if self.skill_workspace is not None:
                self.skill_workspace.sync(skills)
        elif message_type == "DEVICE_AI_CONFIG_SYNC" and self.ai_config_store is not None:
            config = payload.get("config")
            if config:
                self.ai_config_store.save_ai_config(config)
            else:
                self.ai_config_store.delete_ai_config()

    def _rebuild_registry(self, skills: list[dict]) -> None:
        """重建registry以应用新的skill配置"""
        new_registry = build_default_registry(
            self.config,
            device_skills=skills,
            enable_builtin_by_default=False,
        )
        self.skill_registry._handlers = new_registry._handlers
        self.skill_registry._action_specs = new_registry._action_specs


def create_default_service(config: ClientConfig | None = None) -> ClientService:
    from client.runtime import TaskRunner

    config = config or ClientConfig.from_env()
    checkpoint_store = CheckpointStore(config.checkpoint_path, ai_scope=config.device_id)
    registry = build_default_registry(config, enable_builtin_by_default=False)
    transport = NullTransport()
    skill_workspace = SkillWorkspaceManager(
        workspace_root=config.skills_workspace,
        archive_fetcher=GatewaySkillArchiveFetcher(config),
    )
    runner = TaskRunner(
        planner=LLMPlanner(
            config_resolver=lambda: checkpoint_store.load_ai_config() or config.ai_config(),
            action_catalog_provider=registry.available_actions,
            device_id=config.device_id,
            call_log_sink=_build_ai_call_sink(transport, config.device_id),
        ),
        registry=registry,
        transport=transport,
        checkpoints=checkpoint_store,
        workflow_store_path=config.workflow_store_path,
    )
    return ClientService(
        runner=runner,
        transport=transport,
        config=config,
        skill_workspace=skill_workspace,
        ai_config_store=checkpoint_store,
        skill_registry=registry,
    )


def run_forever(config: ClientConfig | None = None) -> None:
    from client.runtime import TaskRunner

    config = config or ClientConfig.from_env()
    if ws_connect is None:
        raise RuntimeError("websockets is required to run the client service")

    checkpoint_store = CheckpointStore(config.checkpoint_path, ai_scope=config.device_id)
    registry = build_default_registry(config, enable_builtin_by_default=False)
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
                planner = LLMPlanner(
                    config_resolver=lambda: checkpoint_store.load_ai_config() or config.ai_config(),
                    action_catalog_provider=registry.available_actions,
                    device_id=config.device_id,
                    call_log_sink=_build_ai_call_sink(transport, config.device_id),
                )
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
                        config=config,
                        skill_workspace=skill_workspace,
                        ai_config_store=checkpoint_store,
                        skill_registry=registry,
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
