"""Experience Reallocator 节点：不改变目标和任务语义，调整模型、工具、执行器、上下文或重试策略。

输出：新 Assignment
"""

from __future__ import annotations


async def reallocator(state: object) -> object:
    raise NotImplementedError


__all__ = ["reallocator"]
