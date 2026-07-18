"""审核结果模型。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ReviewResult(BaseModel):
    """对应架构设计第 5.2 节 ReviewResult。"""

    passed: bool = Field(description="是否通过审核，True 表示结果可接受")
    score: float | None = Field(default=None, description="审核评分，None 表示未评分")
    failed_task_ids: list[str] = Field(default_factory=list, description="未通过审核的任务 ID 列表")
    issues: list[str] = Field(default_factory=list, description="审核发现的问题描述列表")
    evidence_refs: list[str] = Field(default_factory=list, description="支撑审核结论的证据引用列表")
    suggested_action: str | None = Field(default=None, description="建议的后续动作：replan（重规划）、reallocate（重分配）、reaggregate（重汇总）、finalize（最终化）")


__all__ = ["ReviewResult"]
