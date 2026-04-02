from __future__ import annotations

import re

from client.ai import coerce_ai_config, StructuredModelClient
from client.models import TaskAction


class RuleBasedPlanner:
    """A deterministic fallback planner for the initialization phase."""

    def plan(self, instruction: str) -> list[TaskAction]:
        actions: list[TaskAction] = []

        if "负载" in instruction or "load" in instruction.lower():
            actions.append(
                TaskAction(
                    name="process.inspect_load",
                    command="inspect system load",
                    args={},
                )
            )

        docker_match = re.search(
            r"(?:重启容器|restart\s+container|restart\s+docker)\s+([a-zA-Z0-9_.-]+)",
            instruction,
            re.IGNORECASE,
        )
        if docker_match:
            container = docker_match.group(1)
            actions.append(
                TaskAction(
                    name="docker.restart",
                    command=f"docker restart {container}",
                    args={"container": container},
                    requires_approval=True,
                    reason="重启容器会打断服务，需要人工确认",
                )
            )

        read_match = re.search(r"(?:读取|查看)\s+([/~.\w-]+)", instruction)
        if read_match and "/" in read_match.group(1):
            actions.append(
                TaskAction(
                    name="filesystem.read_file",
                    command=f"read file {read_match.group(1)}",
                    args={"path": read_match.group(1)},
                )
            )

        search_match = re.search(r"(?:搜索|查找).*(\.[a-zA-Z0-9]+)", instruction)
        if search_match:
            actions.append(
                TaskAction(
                    name="filesystem.search_suffix",
                    command=f"search files *{search_match.group(1)}",
                    args={"suffix": search_match.group(1)},
                )
            )

        if not actions:
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
        fallback_planner: RuleBasedPlanner | None = None,
    ) -> None:
        self.config_resolver = config_resolver
        self.model_client_factory = model_client_factory or StructuredModelClient
        self.fallback_planner = fallback_planner or RuleBasedPlanner()

    def plan(self, instruction: str) -> list[TaskAction]:
        config = coerce_ai_config(self.config_resolver())
        if config is None:
            return self.fallback_planner.plan(instruction)
        payload = self.model_client_factory(config).generate_json(
            system_prompt=self._system_prompt(),
            user_prompt=self._user_prompt(instruction),
        )
        actions = payload.get("actions")
        if not isinstance(actions, list) or not actions:
            raise ValueError("AI planner must return a non-empty actions array")
        return [TaskAction.from_dict(self._normalize_action(action)) for action in actions]

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
    def _system_prompt() -> str:
        return (
            "你是 OpenJarvis 的任务规划器。"
            "你必须把用户指令拆成可执行 action 列表，并仅返回 JSON 对象。"
            "可用 action 如下：\n"
            "- process.inspect_load args={}\n"
            "- process.list_processes args={}\n"
            "- docker.list_containers args={\"include_all\": boolean}\n"
            "- docker.restart args={\"container\": string} requires_approval=true\n"
            "- filesystem.read_file args={\"path\": string}\n"
            "- filesystem.search_suffix args={\"suffix\": string}\n"
            "- iot.set_state args={\"entity_id\": string, \"state\": string}\n"
            "- shell.exec args={\"command\": string} requires_approval=true\n"
            "如果没有明确匹配的技能，退化为 shell.exec，且必须要求审批。"
            "返回格式："
            "{\"actions\":[{\"name\":\"...\",\"command\":\"...\",\"args\":{},"
            "\"requires_approval\":false,\"reason\":null}]}"
        )

    @staticmethod
    def _user_prompt(instruction: str) -> str:
        return f"用户指令：{instruction}"
