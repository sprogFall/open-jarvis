"""经验模型。

对应架构设计第 7 节。经验不是整段历史对话，而是一次已审核运行沉淀出的结构化记录。
经验只能辅助决策：必须可追溯、可降权、可失效，不能覆盖当前事实或用户约束。
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ExperienceScope(StrEnum):
    planning = "planning"
    execution = "execution"
    review = "review"


class Experience(BaseModel):
    """结构化经验记录。"""

    experience_id: str
    scope: ExperienceScope
    problem_fingerprint: str
    task_pattern: str | None = None
    fault_domain: str | None = None
    symptoms: list[str] = Field(default_factory=list)
    root_cause: str | None = None
    successful_action: str | None = None
    constraints: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    source_run_id: str | None = None
    confidence: float = 0.5
    success_count: int = 0
    failure_count: int = 0
    created_at: datetime | None = None
    last_used_at: datetime | None = None
    expires_at: datetime | None = None


__all__ = ["Experience", "ExperienceScope"]
