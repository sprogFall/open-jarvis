"""Executor 节点：根据单个任务契约调用模型与工具；上报进度；只对瞬时错误做短重试。

实现为小型子图：prepare_context -> agent/model -> tool_call（可循环、有上限）-> validate_output
输出：TaskResult
"""

from __future__ import annotations


async def executor(state: object) -> object:
    raise NotImplementedError


__all__ = ["executor"]
