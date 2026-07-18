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

    task_id: str
    attempt: int = 1
    status: TaskStatus
    output: dict[str, Any] | None = None
    artifact_refs: list[str] = Field(default_factory=list)
    error_code: str | None = None
    error_message: str | None = None
    started_at: str | None = None
    ended_at: str | None = None
    token_usage: int | None = None
    cost: float | None = None
    tools_used: list[str] = Field(default_factory=list)


__all__ = ["TaskResult", "TaskStatus"]
