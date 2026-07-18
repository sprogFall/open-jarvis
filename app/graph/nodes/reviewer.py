"""Reviewer 节点：按总体与逐任务验收标准检查完整性、正确性、证据和约束。

使用独立提示词；高风险场景可配置不同模型，降低同源偏差。
输出：ReviewResult
"""

from __future__ import annotations


async def reviewer(state: object) -> object:
    raise NotImplementedError


__all__ = ["reviewer"]
