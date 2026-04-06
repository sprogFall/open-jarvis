from __future__ import annotations

import re

from client.ai import coerce_ai_config, resolve_model_endpoint, StructuredModelClient
from client.models import TaskAction
from skill_catalog import SkillActionSpec, builtin_actions_for_skill_ids


def _infer_shell_command(instruction: str) -> str | None:
    normalized = instruction.strip()
    lowered = normalized.lower()

    if (
        "工作目录" in normalized
        or "当前目录" in normalized
        or "current directory" in lowered
        or "working directory" in lowered
    ):
        return "pwd"

    if (
        ("列出" in normalized or "查看" in normalized or "list" in lowered)
        and ("目录内容" in normalized or "当前目录" in normalized or "工作目录" in normalized)
    ):
        return "ls -la"

    if "当前用户" in normalized or "本机用户" in normalized or "whoami" in lowered:
        return "whoami"

    if "主机名" in normalized or "hostname" in lowered:
        return "hostname"

    if "磁盘" in normalized and ("使用" in normalized or "空间" in normalized):
        return "df -h"

    if "内存" in normalized and ("使用" in normalized or "占用" in normalized):
        return "free -h"

    return None


def _extract_docker_container(text: str) -> str | None:
    match = re.search(
        r"(?:重启容器|restart\s+container|restart\s+docker|docker\s+restart)\s+([a-zA-Z0-9_.-]+)",
        text,
        re.IGNORECASE,
    )
    return match.group(1) if match else None


def _extract_read_path(text: str) -> str | None:
    match = re.search(r"(?:读取|查看|read)\s+([/~.\w-]+)", text, re.IGNORECASE)
    if not match:
        return None
    path = match.group(1)
    return path if "/" in path else None


def _extract_search_suffix(text: str) -> str | None:
    match = re.search(r"(?:搜索|查找|search).*(\.[a-zA-Z0-9]+)", text, re.IGNORECASE)
    return match.group(1) if match else None


def _coerce_bool_flag(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _looks_like_shell_command(text: str) -> bool:
    normalized = text.strip()
    if not normalized:
        return False
    return bool(re.match(r"^[A-Za-z0-9_./-]+(?:\s+|$)", normalized))


class RuleBasedPlanner:
    """A deterministic fallback planner for the initialization phase."""

    def __init__(self, *, action_catalog_provider=None) -> None:
        self.action_catalog_provider = action_catalog_provider or _default_action_catalog

    def plan(self, instruction: str, *, task_id: str | None = None) -> list[TaskAction]:
        del task_id
        actions: list[TaskAction] = []
        available_actions = {
            action.name: action
            for action in self.action_catalog_provider()
        }

        if (
            ("负载" in instruction or "load" in instruction.lower())
            and "process.inspect_load" in available_actions
        ):
            actions.append(
                TaskAction(
                    name="process.inspect_load",
                    command="inspect system load",
                    args={},
                )
            )

        docker_match = _extract_docker_container(instruction)
        if docker_match and "docker.restart" in available_actions:
            container = docker_match
            actions.append(
                TaskAction(
                    name="docker.restart",
                    command=f"docker restart {container}",
                    args={"container": container},
                    requires_approval=True,
                    reason="重启容器会打断服务，需要人工确认",
                )
            )

        read_match = _extract_read_path(instruction)
        if (
            read_match
            and "filesystem.read_file" in available_actions
        ):
            actions.append(
                TaskAction(
                    name="filesystem.read_file",
                    command=f"read file {read_match}",
                    args={"path": read_match},
                )
            )

        search_match = _extract_search_suffix(instruction)
        if search_match and "filesystem.search_suffix" in available_actions:
            actions.append(
                TaskAction(
                    name="filesystem.search_suffix",
                    command=f"search files *{search_match}",
                    args={"suffix": search_match},
                )
            )

        if not actions:
            inferred_shell_command = _infer_shell_command(instruction)
            if inferred_shell_command and "shell.exec" in available_actions:
                actions.append(
                    TaskAction(
                        name="shell.exec",
                        command=inferred_shell_command,
                        args={"command": inferred_shell_command},
                        requires_approval=True,
                        reason="根据用户意图生成受控 Shell 命令，执行前需要人工确认",
                    )
                )
                return actions
            if "shell.exec" not in available_actions:
                raise ValueError("当前设备没有启用可执行 Skill")
            if not _looks_like_shell_command(instruction):
                raise ValueError("当前设备未配置 AI，无法把自然语言任务直接转成可执行 shell command")
            actions.append(
                TaskAction(
                    name="shell.exec",
                    command=instruction.strip(),
                    args={"command": instruction.strip()},
                    requires_approval=True,
                    reason="未命中已知技能，转为人工确认的命令执行",
                )
            )
        return actions


class LLMPlanner:
    def __init__(
        self,
        *,
        config_resolver,
        model_client_factory=None,
        action_catalog_provider=None,
        fallback_planner: RuleBasedPlanner | None = None,
        call_log_sink=None,
        device_id: str | None = None,
    ) -> None:
        self.config_resolver = config_resolver
        self.model_client_factory = model_client_factory or StructuredModelClient
        self.action_catalog_provider = action_catalog_provider or _default_action_catalog
        self.fallback_planner = fallback_planner or RuleBasedPlanner(
            action_catalog_provider=self.action_catalog_provider
        )
        self.call_log_sink = call_log_sink
        self.device_id = device_id

    def plan(self, instruction: str, *, task_id: str | None = None) -> list[TaskAction]:
        available_actions = self.action_catalog_provider()
        if not available_actions:
            raise ValueError("当前设备没有启用可执行 Skill")
        config = coerce_ai_config(self.config_resolver())
        if config is None:
            return self.fallback_planner.plan(instruction, task_id=task_id)
        system_prompt = self._system_prompt(available_actions)
        user_prompt = self._user_prompt(instruction)
        try:
            payload = self.model_client_factory(config).generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
        except Exception as exc:
            self._record_ai_call(
                config=config,
                task_id=task_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                error=str(exc),
            )
            raise
        self._record_ai_call(
            config=config,
            task_id=task_id,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response=payload,
        )
        actions = payload.get("actions")
        if not isinstance(actions, list) or not actions:
            raise ValueError("AI planner must return a non-empty actions array")
        allowed_action_names = {action.name for action in available_actions}
        action_specs = {action.name: action for action in available_actions}
        normalized_actions = [
            self._repair_action(
                self._normalize_action(action),
                instruction,
                action_specs.get(str(action.get("name", ""))),
            )
            for action in actions
        ]
        for action in normalized_actions:
            if action["name"] not in allowed_action_names:
                raise ValueError(f"AI planner returned disabled action: {action['name']}")
            self._validate_action(action)
        return [TaskAction.from_dict(action) for action in normalized_actions]

    def _record_ai_call(
        self,
        *,
        config,
        task_id: str | None,
        system_prompt: str,
        user_prompt: str,
        response: dict | None = None,
        error: str | None = None,
    ) -> None:
        if self.call_log_sink is None:
            return
        self.call_log_sink(
            {
                "source": "client_planner",
                "device_id": self.device_id,
                "task_id": task_id,
                "provider": config.provider,
                "model": config.model,
                "endpoint": resolve_model_endpoint(config),
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "response": response,
                "error": error,
            }
        )

    @staticmethod
    def _normalize_action(payload: dict) -> dict:
        return {
            "name": payload["name"],
            "command": payload["command"],
            "args": payload.get("args") or {},
            "requires_approval": bool(payload.get("requires_approval", False)),
            "reason": payload.get("reason"),
        }

    @staticmethod
    def _repair_action(
        payload: dict,
        instruction: str,
        action_spec: SkillActionSpec | None,
    ) -> dict:
        raw_args = payload.get("args") or {}
        raw_command = str(
            raw_args.get("command")
            or payload.get("command")
            or ""
        ).strip()
        name = payload["name"]
        repaired = {**payload}

        if name == "process.inspect_load":
            repaired["command"] = "inspect system load"
            repaired["args"] = {}
        elif name == "process.list_processes":
            repaired["command"] = "list busy processes"
            repaired["args"] = {}
        elif name == "docker.list_containers":
            include_all = _coerce_bool_flag(raw_args.get("include_all"))
            if not include_all and re.search(r"(全部|所有|all|stopped|已停止)", instruction, re.IGNORECASE):
                include_all = True
            repaired["command"] = "docker ps -a" if include_all else "docker ps"
            repaired["args"] = {"include_all": include_all}
        elif name == "docker.restart":
            container = str(
                raw_args.get("container")
                or _extract_docker_container(raw_command)
                or _extract_docker_container(instruction)
                or ""
            ).strip()
            if container:
                repaired["command"] = f"docker restart {container}"
                repaired["args"] = {"container": container}
        elif name == "filesystem.read_file":
            path = str(
                raw_args.get("path")
                or _extract_read_path(raw_command)
                or _extract_read_path(instruction)
                or ""
            ).strip()
            if path:
                repaired["command"] = f"read file {path}"
                repaired["args"] = {"path": path}
        elif name == "filesystem.search_suffix":
            suffix = str(
                raw_args.get("suffix")
                or _extract_search_suffix(raw_command)
                or _extract_search_suffix(instruction)
                or ""
            ).strip()
            if suffix:
                repaired["command"] = f"search files *{suffix}"
                repaired["args"] = {"suffix": suffix}
        elif name == "shell.exec":
            inferred_shell_command = _infer_shell_command(instruction)
            if (
                inferred_shell_command
                and (
                    not raw_command
                    or raw_command == instruction.strip()
                    or bool(re.search(r"[\u4e00-\u9fff]", raw_command))
                )
            ):
                repaired["command"] = inferred_shell_command
                repaired["args"] = {
                    **raw_args,
                    "command": inferred_shell_command,
                }

        if action_spec is not None:
            repaired["requires_approval"] = bool(
                payload.get("requires_approval", False) or action_spec.requires_approval
            )
            if repaired["requires_approval"] and not repaired.get("reason"):
                repaired["reason"] = action_spec.approval_reason
        return repaired

    @staticmethod
    def _validate_action(payload: dict) -> None:
        if payload["name"] != "shell.exec":
            return
        command = str(payload.get("command") or "").strip()
        if not _looks_like_shell_command(command):
            raise ValueError("AI planner returned a non-executable shell command")

    @staticmethod
    def _system_prompt(available_actions: list[SkillActionSpec]) -> str:
        action_lines = "\n".join(
            action.render_for_prompt()
            for action in available_actions
        )
        shell_guidance = ""
        if any(action.name == "shell.exec" for action in available_actions):
            shell_guidance = (
                "如果选择 shell.exec，command 和 args.command 必须是真实可执行的 Bash 命令。"
            )
        return (
            "你是 OpenJarvis 的任务规划器。"
            "你必须把用户指令拆成可执行 action 列表，并仅返回 JSON 对象。"
            "当前设备已启用的 action 如下：\n"
            f"{action_lines}\n"
            "只能从上面的 action 中选择。"
            "返回的 command 必须是标准化后的命令或内部动作描述，"
            "不能直接复述中文或自然语言请求。"
            f"{shell_guidance}"
            "返回格式："
            "{\"actions\":[{\"name\":\"...\",\"command\":\"...\",\"args\":{},"
            "\"requires_approval\":false,\"reason\":null}]}"
        )

    @staticmethod
    def _user_prompt(instruction: str) -> str:
        return f"用户指令：{instruction}"


def _default_action_catalog() -> list[SkillActionSpec]:
    return builtin_actions_for_skill_ids()
