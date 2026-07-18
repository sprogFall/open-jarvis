"""LangGraph 状态定义与 reducers。

节点间只传结构化对象，并行 Executor不直接修改共享的 tasks 字典，只追加不可变 TaskResult。
"""

from __future__ import annotations

from typing import Annotated, TypedDict

from app.domain.aggregate import AggregateResult
from app.domain.assignment import Assignment
from app.domain.budget import RunBudget
from app.domain.diagnosis import Diagnosis
from app.domain.final_answer import FinalAnswer
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

    run_id: str  # 运行唯一标识符
    user_request: str  # 用户原始请求文本
    plan: Plan | None  # 当前执行计划，None 表示尚未生成
    plan_version: int  # 计划版本号，每次重规划自增
    task_events: Annotated[list[TaskResult], add_task_results]  # 任务执行事件列表，并行 Executor 通过 reducer 追加不可变结果
    assignments: dict[str, Assignment]  # 任务 ID 到执行分配的映射
    current_assignment: Assignment | None  # Send 注入的当前分支执行分配，Executor 通过此字段获知应处理哪个任务；不持久化回全局状态
    aggregate: AggregateResult | None  # 汇总结果，None 表示尚未汇总
    review: ReviewResult | None  # 审核结果，None 表示尚未审核
    diagnosis: Diagnosis | None  # 归因诊断结果，None 表示尚未诊断
    budget: RunBudget  # 运行资源预算与已消耗统计
    cycle_count: int  # 当前 Review → (Re)Plan 循环次数
    final_answer: FinalAnswer | None  # 最终用户响应，None 表示尚未生成


__all__ = ["RunState", "add_task_results"]
