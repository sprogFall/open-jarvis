"""运行预算模型。

对应架构设计第 10.1 节默认保护阈值，阈值全部配置化。
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RunBudget(BaseModel):
    """单次运行的资源预算，任一维度耗尽即进入降级汇总。"""

    max_plan_versions: int = Field(default=3, description="允许的最大计划重规划版本数")
    max_review_cycles: int = Field(default=3, description="允许的最大审核循环次数")
    max_task_attempts: int = Field(default=2, description="单个任务的最大重试次数")
    max_concurrent_tasks: int = Field(default=4, description="最大并发执行任务数")
    max_total_seconds: int = Field(default=900, description="单次运行总时间上限（秒），默认 15 分钟")
    max_model_calls: int = Field(default=50, description="允许的最大模型调用次数")
    max_tokens: int = Field(default=200_000, description="允许的最大 Token 消耗量")
    max_cost: float | None = Field(default=None, description="允许的最大费用上限，None 表示不限制")

    used_model_calls: int = Field(default=0, description="已消耗的模型调用次数")
    used_tokens: int = Field(default=0, description="已消耗的 Token 数量")
    used_cost: float = Field(default=0.0, description="已消耗的费用")
    counted_event_count: int = Field(default=0, description="已计入预算的 task_events 数量，用于避免重复累加")

    @property
    def exhausted(self) -> bool:
        return (
            (self.max_model_calls is not None and self.used_model_calls >= self.max_model_calls)
            or (self.max_tokens is not None and self.used_tokens >= self.max_tokens)
            or (self.max_cost is not None and self.used_cost >= self.max_cost)
        )


__all__ = ["RunBudget"]
