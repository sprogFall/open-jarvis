from __future__ import annotations

import re

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

