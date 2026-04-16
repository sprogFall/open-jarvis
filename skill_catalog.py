from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SkillActionSpec:
    skill_id: str
    name: str
    description: str
    args_schema: dict[str, str]
    requires_approval: bool = False
    approval_reason: str | None = None

    def render_for_prompt(self) -> str:
        suffix = ""
        if self.requires_approval:
            suffix = " requires_approval=true"
            if self.approval_reason:
                suffix += f" reason={json.dumps(self.approval_reason, ensure_ascii=False)}"
        return (
            f"- {self.name} args={json.dumps(self.args_schema, ensure_ascii=False)}"
            f"{suffix} // {self.description}"
        )


@dataclass(frozen=True, slots=True)
class SkillDefinition:
    skill_id: str
    name: str
    description: str
    actions: tuple[SkillActionSpec, ...]

    @property
    def action_names(self) -> list[str]:
        return [action.name for action in self.actions]


BUILTIN_SKILLS: tuple[SkillDefinition, ...] = (
    SkillDefinition(
        skill_id="builtin-filesystem",
        name="文件系统",
        description="读取允许目录中的文件，并按后缀搜索本地文件。",
        actions=(
            SkillActionSpec(
                skill_id="builtin-filesystem",
                name="filesystem.read_file",
                description="读取允许目录中的 UTF-8 文本文件内容。",
                args_schema={"path": "绝对路径或相对允许目录的路径"},
            ),
            SkillActionSpec(
                skill_id="builtin-filesystem",
                name="filesystem.search_suffix",
                description="在允许目录中搜索指定后缀的文件。",
                args_schema={"suffix": "例如 .log 或 .yaml"},
            ),
        ),
    ),
    SkillDefinition(
        skill_id="builtin-process",
        name="进程监控",
        description="查看系统负载与当前高占用进程。",
        actions=(
            SkillActionSpec(
                skill_id="builtin-process",
                name="process.inspect_load",
                description="查看当前 1/5/15 分钟系统负载。",
                args_schema={},
            ),
            SkillActionSpec(
                skill_id="builtin-process",
                name="process.list_processes",
                description="列出当前 CPU 占用较高的进程。",
                args_schema={},
            ),
        ),
    ),
    SkillDefinition(
        skill_id="builtin-docker",
        name="Docker 运维",
        description="查看本机 Docker 容器并执行受控重启。",
        actions=(
            SkillActionSpec(
                skill_id="builtin-docker",
                name="docker.list_containers",
                description="查看本机 Docker 容器状态。",
                args_schema={"include_all": "是否包含已停止容器，true 或 false"},
            ),
            SkillActionSpec(
                skill_id="builtin-docker",
                name="docker.restart",
                description="重启指定 Docker 容器。",
                args_schema={"container": "容器名称或 ID"},
                requires_approval=True,
                approval_reason="重启容器会打断服务，需要人工确认",
            ),
        ),
    ),
    SkillDefinition(
        skill_id="builtin-shell",
        name="Shell 执行",
        description="在 Linux Shell 中执行命令，始终需要人工审批。",
        actions=(
            SkillActionSpec(
                skill_id="builtin-shell",
                name="shell.exec",
                description="执行一个未命中其他技能的 Bash 命令。",
                args_schema={"command": "待执行的 bash 命令"},
                requires_approval=True,
                approval_reason="Shell 命令存在环境副作用，需要人工确认",
            ),
        ),
    ),
)

_BUILTIN_SKILL_MAP = {skill.skill_id: skill for skill in BUILTIN_SKILLS}
_BUILTIN_ACTIONS = [
    action
    for skill in BUILTIN_SKILLS
    for action in skill.actions
]
_BUILTIN_ACTION_MAP = {action.name: action for action in _BUILTIN_ACTIONS}


def builtin_skill_ids() -> list[str]:
    return [skill.skill_id for skill in BUILTIN_SKILLS]


def builtin_skill(skill_id: str) -> SkillDefinition | None:
    return _BUILTIN_SKILL_MAP.get(skill_id)


def builtin_action(name: str) -> SkillActionSpec | None:
    return _BUILTIN_ACTION_MAP.get(name)


def builtin_actions_for_skill_ids(skill_ids: set[str] | None = None) -> list[SkillActionSpec]:
    if skill_ids is None:
        return list(_BUILTIN_ACTIONS)
    return [action for action in _BUILTIN_ACTIONS if action.skill_id in skill_ids]
