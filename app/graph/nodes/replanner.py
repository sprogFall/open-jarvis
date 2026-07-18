"""Experience Replanner 节点：保留仍有效的成功结果，修订任务、依赖或验收条件，递增计划版本。

输出：新 Plan
"""

from __future__ import annotations


async def replanner(state: object) -> object:
    raise NotImplementedError


__all__ = ["replanner"]
