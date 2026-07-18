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

    fault_domain: FaultDomain = Field(description="故障归属域，标识错误发生在哪个阶段")
    confidence: float = Field(default=0.0, description="诊断结论的置信度，范围 0.0~1.0")
    evidence: list[str] = Field(default_factory=list, description="支撑诊断结论的证据列表")
    suggested_action: str | None = Field(default=None, description="建议的恢复动作：replan（重规划）、reallocate（重分配）、reaggregate（重汇总）、finalize（最终化）")
    reusable_success_task_ids: list[str] = Field(default_factory=list, description="可复用的已成功任务 ID 列表，避免重复执行")
    experience_ids: list[str] = Field(default_factory=list, description="关联的经验记录 ID 列表")


__all__ = ["Diagnosis", "FaultDomain"]
