"""Aggregator 节点：去重、排序、解析引用并确定性合并任务产物；必要时生成面向审核的候选答案。

输出：AggregateResult
"""

from __future__ import annotations


async def aggregator(state: object) -> object:
    raise NotImplementedError


__all__ = ["aggregator"]
