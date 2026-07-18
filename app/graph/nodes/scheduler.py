"""Scheduler / Allocator 节点：校验依赖、选择就绪任务、匹配执行器/模型/工具、控制并发和预算。

输出：Assignment[] / Send[]
"""

from __future__ import annotations


async def scheduler(state: object) -> object:
    raise NotImplementedError


__all__ = ["scheduler"]
