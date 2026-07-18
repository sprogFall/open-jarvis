"""工具层：工具注册、权限、执行与适配器。

对应架构设计第 6 节。工具统一注册为 ToolSpec，执行前同时校验计划白名单、
执行器白名单和运行身份权限。
"""

from app.tools.base import ToolSpec
from app.tools.registry import ToolRegistry, tool_registry

__all__ = ["ToolRegistry", "ToolSpec", "tool_registry"]
