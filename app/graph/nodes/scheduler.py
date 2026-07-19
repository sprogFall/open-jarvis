"""Scheduler / Allocator 节点：校验依赖、选择就绪任务、匹配执行器/模型/工具、控制并发和预算。

输出：Assignment[] / Send[]
"""

from __future__ import annotations

from typing import Any

from langgraph.types import Send

from app.domain import Assignment, Task, TaskStatus
from app.graph.state import RunState

_TERMINAL_STATUSES = (
    TaskStatus.completed,
    TaskStatus.running,
    TaskStatus.failed,
    TaskStatus.cancelled,
    TaskStatus.skipped,
)

def _task_status_map(state: RunState) -> dict[str, TaskStatus]:
    """从task_events归并出每个任务的最新状态（事件溯源）。"""
    latest: dict[str, TaskStatus] = {}
    for ev in (state.get("task_events", [])):
        latest[ev.task_id] = ev.status
    return latest

def _ready_tasks(state: RunState) -> list[Task]:
    """计算就绪任务：依赖已经全部completed且自身未完成/未运行"""
    plan = state.get("plan")
    if plan is None:
        return []
    status_map = _task_status_map(state)
    ready = []
    for task in plan.tasks:
        if status_map.get(task.task_id) in _TERMINAL_STATUSES:
            # 如果任务已完成/运行中 不做处理
            # 这里是【任务状态】
            continue
        # 当前task下的依赖是否已经全部完成
        # 这里是任务下的【依赖状态】
        deps_ok = all(
            status_map.get(dep) == TaskStatus.completed
            for dep in task.dependencies
        )
        if deps_ok:
            ready.append(task)
    # 返回本轮就绪的task列表
    return ready

async def scheduler(state: RunState) -> dict[str, Any]:
    """按并发上限生成 Assignment 并写入全局状态，路由函数据此做 Send 扇出。"""
    ready = _ready_tasks(state)
    budget = state.get("budget")
    max_concurrent = budget.max_concurrent_tasks if budget else 4
    cycle_count = state.get("cycle_count", 0) + 1
    max_cycles = (budget.max_review_cycles if budget else 3) * 3

    if cycle_count > max_cycles:
        return {
            "cycle_count": cycle_count,
            "assignments": {},
            "diagnosis": state.get("diagnosis"),
        }

    assignments: dict[str, Assignment] = {}
    for task in ready[:max_concurrent]:
        assignments[task.task_id] = Assignment(
            task_id=task.task_id,
            executor_profile="default",
            model_tier="standard",
            tool_allowlist=task.tool_allowlist,
            timeout_seconds=task.timeout_seconds,
            attempt=1,
        )

    return {
        "cycle_count": state.get("cycle_count", 0) + 1,
        "assignments": assignments,
    }


def route_after_scheduler(state: RunState) -> str | list[Send]:
    """条件路由：有 Assignment -> Send 到 executor; 否则走向汇总或归因"""
    budget = state.get("budget")
    if budget is not None and budget.exhausted:
        return "finalizer"

    assignments = state.get("assignments", {})
    plan = state.get("plan")
    if assignments and plan is not None:
        sends: list[Send] = []
        for _task_id, assignment in assignments.items():
            sends.append(Send("executor", {
                "current_assignment": assignment,
                "plan": plan,
            }))
        return sends

    # 没有就绪任务：判断是全部成功还是阻塞
    if plan is None:
        return "cause_analyzer"
    status_map = _task_status_map(state)
    # 是否全部完成了
    all_done = all(
        status_map.get(t.task_id) == TaskStatus.completed
        for t in plan.tasks
    )
    if all_done:
        diagnosis = state.get("diagnosis")
        if diagnosis is not None and diagnosis.suggested_action not in (None, "finalize", "reaggregate"):
            return "cause_analyzer"
        return "aggregator"                     # reaggregate 走这里，允许重新汇总
    return "cause_analyzer"


__all__ = ["scheduler", "route_after_scheduler"]
