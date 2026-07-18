"""Cause Analyzer 节点：根据错误、轨迹和审核意见进行结构化归因，选择下一动作。

先使用规则证据，再让 LLM 处理语义歧义，禁止仅凭模型猜测。
输出：Diagnosis
"""

from __future__ import annotations


async def cause_analyzer(state: object) -> object:
    raise NotImplementedError


__all__ = ["cause_analyzer"]
