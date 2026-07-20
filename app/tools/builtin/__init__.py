"""内置工具集合。

新增工具只需在 BUILTIN_TOOLS 列表里追加一行。
"""

from __future__ import annotations

from app.tools.base import ToolSpec
from app.tools.builtin.web_search import web_search_spec

# 所有内置工具规格集中声明在此
BUILTIN_TOOLS: list[ToolSpec] = [
    web_search_spec,
    # 新增工具只需追加：
    # from app.tools.builtin.xxx import xxx_spec
]


def register_builtin_tools() -> None:
    """将所有内置工具注册到全局 tool_registry。

    应在应用启动时显式调用（logging 配置之后），保证日志可见。
    """
    from app.tools.registry import tool_registry

    for spec in BUILTIN_TOOLS:
        tool_registry.register(spec)


__all__ = ["BUILTIN_TOOLS", "register_builtin_tools"]