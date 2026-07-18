"""汇总结果模型。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AggregateResult(BaseModel):
    """Aggregator 产出的合并结果。"""

    candidate_answer: str = Field(description="汇总后生成的候选答案文本，经过多任务结果整合后产出")
    task_outputs: dict[str, Any] = Field(default_factory=dict, description="各任务 ID 到其输出结果的映射，用于追溯和引用")
    artifact_refs: list[str] = Field(default_factory=list, description="汇总过程中引用的中间产物引用列表")


__all__ = ["AggregateResult"]