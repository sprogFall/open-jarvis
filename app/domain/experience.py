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

    experience_id: str = Field(description="经验记录的唯一标识符")
    scope: ExperienceScope = Field(description="经验适用范围：planning（规划）、execution（执行）、review（审核）")
    problem_fingerprint: str = Field(description="问题特征的指纹哈希，用于相似问题匹配")
    task_pattern: str | None = Field(default=None, description="匹配的任务模式描述，None 表示不限定任务类型")
    fault_domain: str | None = Field(default=None, description="关联的故障域类型，None 表示通用经验")
    symptoms: list[str] = Field(default_factory=list, description="问题表现的症状描述列表")
    root_cause: str | None = Field(default=None, description="根因分析结果")
    successful_action: str | None = Field(default=None, description="经过验证的成功处理方案")
    constraints: list[str] = Field(default_factory=list, description="经验适用的约束条件列表")
    evidence_refs: list[str] = Field(default_factory=list, description="支撑此经验的证据引用列表")
    source_run_id: str | None = Field(default=None, description="产生此经验的源运行 ID")
    confidence: float = Field(default=0.5, description="经验的置信度权重，范围 0.0~1.0，初始值 0.5")
    success_count: int = Field(default=0, description="此经验被成功应用的次数")
    failure_count: int = Field(default=0, description="此经验应用失败的次数")
    created_at: datetime | None = Field(default=None, description="经验创建时间")
    last_used_at: datetime | None = Field(default=None, description="经验最近一次被使用的时间")
    expires_at: datetime | None = Field(default=None, description="经验过期时间，None 表示永不过期")


__all__ = ["Experience", "ExperienceScope"]
