"""归因诊断模型。"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class FaultDomain(StrEnum):
    planning = "planning"
    allocation = "allocation"
    execution_transient = "execution_transient"
    execution_permanent = "execution_permanent"
    data = "data"
    review = "review"


class Diagnosis(BaseModel):
    """对应架构设计第 4.3 节与第 5.2 节 Diagnosis。"""

    fault_domain: FaultDomain
    confidence: float = 0.0
    evidence: list[str] = Field(default_factory=list)
    suggested_action: str | None = None  # replan / reallocate / reaggregate / finalize
    reusable_success_task_ids: list[str] = Field(default_factory=list)
    experience_ids: list[str] = Field(default_factory=list)


__all__ = ["Diagnosis", "FaultDomain"]
