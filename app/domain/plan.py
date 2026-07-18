"""计划模型。

对应架构设计第 5.1 节。任务 ID 在同一计划版本内稳定；重规划时记录旧、新任务映射；
仅当输入和验收条件仍兼容时复用已成功结果。
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Task(BaseModel):
    """单个任务契约。"""

    task_id: str
    title: str
    instruction: str
    dependencies: list[str] = Field(default_factory=list)
    required_capabilities: list[str] = Field(default_factory=list)
    tool_allowlist: list[str] = Field(default_factory=list)
    input_refs: list[str] = Field(default_factory=list)
    output_schema: dict | None = None
    success_criteria: list[str] = Field(default_factory=list)
    timeout_seconds: int | None = None
    max_attempts: int = 2


class Plan(BaseModel):
    """任务 DAG 计划。"""

    plan_id: str
    version: int = 1
    objective: str
    assumptions: list[str] = Field(default_factory=list)
    global_success_criteria: list[str] = Field(default_factory=list)
    tasks: list[Task] = Field(default_factory=list)


__all__ = ["Plan", "Task"]
