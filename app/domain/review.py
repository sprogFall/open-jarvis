"""审核结果模型。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ReviewResult(BaseModel):
    """对应架构设计第 5.2 节 ReviewResult。"""

    passed: bool
    score: float | None = None
    failed_task_ids: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    suggested_action: str | None = None  # replan / reallocate / reaggregate / finalize


__all__ = ["ReviewResult"]
