"""任务执行结果模型。"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class TaskStatus(StrEnum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"
    skipped = "skipped"


class TaskResult(BaseModel):
    """不可变任务结果，由 Executor 追加到 RunState.task_events。"""

    task_id: str = Field(description="执行的任务 ID")
    attempt: int = Field(default=1, description="当前执行尝试次数，从 1 开始")
    status: TaskStatus = Field(description="任务执行终态：pending（待执行）、running（执行中）、completed（已完成）、failed（失败）、cancelled（已取消）、skipped（已跳过）")
    output: dict[str, Any] | None = Field(default=None, description="任务执行输出结果，None 表示无输出或执行失败")
    artifact_refs: list[str] = Field(default_factory=list, description="执行过程中产生的中间产物引用列表")
    error_code: str | None = Field(default=None, description="错误码，执行成功时为 None")
    error_message: str | None = Field(default=None, description="错误描述信息，执行成功时为 None")
    started_at: str | None = Field(default=None, description="任务开始执行的 ISO 时间戳")
    ended_at: str | None = Field(default=None, description="任务结束执行的 ISO 时间戳")
    token_usage: int | None = Field(default=None, description="本次执行消耗的 Token 数量")
    cost: float | None = Field(default=None, description="本次执行产生的费用估算")
    tools_used: list[str] = Field(default_factory=list, description="本次执行实际调用的工具列表")


__all__ = ["TaskResult", "TaskStatus"]
