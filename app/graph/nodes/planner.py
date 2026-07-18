"""Planner 节点：理解目标、补全假设、生成任务 DAG 与总体验收标准；检索少量相关经验。

输出：Plan
"""

from __future__ import annotations


async def planner(state: object) -> object:
    raise NotImplementedError


__all__ = ["planner"]
