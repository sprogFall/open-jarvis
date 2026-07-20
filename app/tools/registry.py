"""工具注册表。"""

from __future__ import annotations

import logging

from app.tools.base import ToolSpec
logger = logging.getLogger(__name__)

class ToolRegistry:
    """工具注册中心，负责校验白名单与权限。"""

    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        logger.info(f"注册Tool成功：{spec.name}")
        self._tools[spec.name] = spec

    def get(self, name: str) -> ToolSpec | None:
        return self._tools.get(name)

    def all(self) -> list[ToolSpec]:
        return list(self._tools.values())

    def filter_by_allowlist(self, allowlist: list[str]) -> list[ToolSpec]:
        return [self._tools[n] for n in allowlist if n in self._tools]


# 全局默认注册表实例
tool_registry = ToolRegistry()


__all__ = ["ToolRegistry", "tool_registry"]
