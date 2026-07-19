"""工具规格基类。

对应架构设计第 6 节：名称、说明、JSON Schema、权限等级、超时、是否幂等、结果大小上限。
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class PermissionLevel(StrEnum):
    read = "read"
    write = "write"
    network = "network"
    code_exec = "code_exec"


class ToolSpec(BaseModel):
    """工具规格定义。"""

    name: str
    description: str
    parameters_schema: dict[str, Any]
    permission_level: PermissionLevel = PermissionLevel.read
    timeout_seconds: int = 30
    idempotent: bool = True
    max_result_size: int = 16_384


__all__ = ["PermissionLevel", "ToolSpec"]
