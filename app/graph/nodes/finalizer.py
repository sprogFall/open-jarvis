"""Finalizer 节点：生成最终响应；预算耗尽时明确已完成内容、失败项和原因。

输出：FinalAnswer
"""

from __future__ import annotations


async def finalizer(state: object) -> object:
    raise NotImplementedError


__all__ = ["finalizer"]
