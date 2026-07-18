"""执行分配模型。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Assignment(BaseModel):
    """Scheduler 为就绪任务生成的执行分配。

    对应架构设计第 5.2 节。
    """

    task_id: str
    executor_profile: str = "default"
    model_tier: str = "standard"  # fast / standard / reasoning
    tool_allowlist: list[str] = Field(default_factory=list)
    resolved_input_refs: dict[str, str] = Field(default_factory=dict)
    timeout_seconds: int | None = None
    attempt: int = 1


__all__ = ["Assignment"]
