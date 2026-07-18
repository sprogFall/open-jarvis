"""运行预算模型。

对应架构设计第 10.1 节默认保护阈值，阈值全部配置化。
"""

from __future__ import annotations

from pydantic import BaseModel


class RunBudget(BaseModel):
    """单次运行的资源预算，任一维度耗尽即进入降级汇总。"""

    max_plan_versions: int = 3
    max_review_cycles: int = 3
    max_task_attempts: int = 2
    max_concurrent_tasks: int = 4
    max_total_seconds: int = 900  # 15 分钟
    max_model_calls: int | None = None
    max_tokens: int | None = None
    max_cost: float | None = None

    # 已消耗
    used_model_calls: int = 0
    used_tokens: int = 0
    used_cost: float = 0.0

    @property
    def exhausted(self) -> bool:
        return (
            self.used_model_calls >= (self.max_model_calls or float("inf"))
            or self.used_tokens >= (self.max_tokens or float("inf"))
            or self.used_cost >= (self.max_cost or float("inf"))
        )


__all__ = ["RunBudget"]
