from __future__ import annotations

import re

from client.ai import coerce_ai_config, StructuredModelClient
from client.models import TaskAction
from skill_catalog import SkillActionSpec, builtin_actions_for_skill_ids


class RuleBasedPlanner:
    """A deterministic fallback planner for the initialization phase."""

    def __init__(self, *, action_catalog_provider=None) -> None:
        self.action_catalog_provider = action_catalog_provider or _default_action_catalog

    def plan(self, instruction: str) -> list[TaskAction]:
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

        docker_match = re.search(
            r"(?:重启容器|restart\s+container|restart\s+docker)\s+([a-zA-Z0-9_.-]+)",
            instruction,
            re.IGNORECASE,
        )
        if docker_match and "docker.restart" in available_actions:
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
        if (
            read_match
            and "/" in read_match.group(1)
            and "filesystem.read_file" in available_actions
        ):
            actions.append(
                TaskAction(
                    name="filesystem.read_file",
                    command=f"read file {read_match.group(1)}",
                    args={"path": read_match.group(1)},
                )
            )

        search_match = re.search(r"(?:搜索|查找).*(\.[a-zA-Z0-9]+)", instruction)
        if search_match and "filesystem.search_suffix" in available_actions:
            actions.append(
                TaskAction(
                    name="filesystem.search_suffix",
                    command=f"search files *{search_match.group(1)}",
                    args={"suffix": search_match.group(1)},
                )
            )

        if not actions:
            if "shell.exec" not in available_actions:
                raise ValueError("当前设备没有启用可执行 Skill")
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
    ) -> None:
        self.config_resolver = config_resolver
        self.model_client_factory = model_client_factory or StructuredModelClient
        self.action_catalog_provider = action_catalog_provider or _default_action_catalog
        self.fallback_planner = fallback_planner or RuleBasedPlanner(
            action_catalog_provider=self.action_catalog_provider
        )

    def plan(self, instruction: str) -> list[TaskAction]:
        available_actions = self.action_catalog_provider()
        if not available_actions:
            raise ValueError("当前设备没有启用可执行 Skill")
        config = coerce_ai_config(self.config_resolver())
        if config is None:
            return self.fallback_planner.plan(instruction)
        payload = self.model_client_factory(config).generate_json(
            system_prompt=self._system_prompt(available_actions),
            user_prompt=self._user_prompt(instruction),
        )
        actions = payload.get("actions")
        if not isinstance(actions, list) or not actions:
            raise ValueError("AI planner must return a non-empty actions array")
        allowed_action_names = {action.name for action in available_actions}
        normalized_actions = [self._normalize_action(action) for action in actions]
        for action in normalized_actions:
            if action["name"] not in allowed_action_names:
                raise ValueError(f"AI planner returned disabled action: {action['name']}")
        return [TaskAction.from_dict(action) for action in normalized_actions]

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
    def _system_prompt(available_actions: list[SkillActionSpec]) -> str:
        action_lines = "\n".join(
            action.render_for_prompt()
            for action in available_actions
        )
        return (
            "你是 OpenJarvis 的任务规划器。"
            "你必须把用户指令拆成可执行 action 列表，并仅返回 JSON 对象。"
            "当前设备已启用的 action 如下：\n"
            f"{action_lines}\n"
            "只能从上面的 action 中选择。"
            "返回格式："
            "{\"actions\":[{\"name\":\"...\",\"command\":\"...\",\"args\":{},"
            "\"requires_approval\":false,\"reason\":null}]}"
        )

    @staticmethod
    def _user_prompt(instruction: str) -> str:
        return f"用户指令：{instruction}"


def _default_action_catalog() -> list[SkillActionSpec]:
    return builtin_actions_for_skill_ids()
