"""LangGraph 状态定义与 reducers。

对应架构设计第 5 节核心状态与数据契约。节点间只传结构化对象，并行 Executor
不直接修改共享的 tasks 字典，只追加不可变 TaskResult。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, TypedDict

from app.domain.assignment import Assignment
from app.domain.budget import RunBudget
from app.domain.diagnosis import Diagnosis
from app.domain.plan import Plan
from app.domain.review import ReviewResult
from app.domain.task import TaskResult


def add_task_results(
    left: list[TaskResult], right: list[TaskResult]
) -> list[TaskResult]:
    """reducer：追加并行 Executor 产出的不可变 TaskResult。"""
    return [*left, *right]


class RunState(TypedDict, total=False):
    """LangGraph 运行状态。

    图负责流程，状态负责事实：路由由 LangGraph 表达，节点只读取状态并返回增量更新。
    """

    run_id: str
    user_request: str
    plan: Plan | None
    plan_version: int
    task_events: Annotated[list[TaskResult], add_task_results]
    assignments: dict[str, Assignment]
    aggregate: object | None
    review: ReviewResult | None
    diagnosis: Diagnosis | None
    budget: RunBudget
    cycle_count: int
    final_answer: object | None


__all__ = ["RunState", "add_task_results"]
