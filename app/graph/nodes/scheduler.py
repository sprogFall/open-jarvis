"""Scheduler / Allocator 节点：校验依赖、选择就绪任务、匹配执行器/模型/工具、控制并发和预算。

输出：Assignment[] / Send[]
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langgraph.types import Send

from app.domain import Assignment, Diagnosis, Task, TaskStatus
from app.domain.diagnosis import FaultDomain
from app.graph.state import RunState

logger = logging.getLogger(__name__)

_NON_SCHEDULABLE_STATUSES = (
    TaskStatus.completed,
    TaskStatus.cancelled,
    TaskStatus.skipped,
)
_RUNNING_BLOCKED_STATUSES = (
    TaskStatus.running,
    TaskStatus.failed,
)


def _task_status_map(state: RunState) -> dict[str, TaskStatus]:
    """从task_events归并出每个任务的最新状态（事件溯源）。"""
    latest: dict[str, TaskStatus] = {}
    for ev in state.get("task_events", []):
        latest[ev.task_id] = ev.status
    return latest


def _resolved_dependency_inputs(state: RunState, task: Task) -> dict[str, str]:
    """将已完成的依赖输出暴露给下游任务."""
    latest_outputs: dict[str, Any] = {}
    for event in state.get("task_events", []):
        if event.status == TaskStatus.completed and event.output is not None:
            latest_outputs[event.task_id] = event.output
    return {
        dependency_id: json.dumps(latest_outputs[dependency_id], ensure_ascii=False, default=str)
        for dependency_id in task.dependencies
        if dependency_id in latest_outputs
    }


def _ready_tasks(state: RunState) -> list[Task]:
    """计算就绪任务：依赖已全部完成且自身未完成/未失败/未运行"""
    plan = state.get("plan")
    if plan is None:
        return []
    status_map = _task_status_map(state)
    # 已有 assignments 的任务（例如 reallocator 已分配）不再重复生成
    existing_assigned = set(state.get("assignments", {}).keys())
    ready: list[Task] = []
    for task in plan.tasks:
        status = status_map.get(task.task_id)
        if status in _NON_SCHEDULABLE_STATUSES:
            continue
        # 正在运行或已失败但已有新 assignment（重分配）的任务跳过
        if status in _RUNNING_BLOCKED_STATUSES:
            if task.task_id in existing_assigned:
                continue  # reallocator 已分配，跳过自动调度
            continue
        if all(status_map.get(dep) == TaskStatus.completed for dep in task.dependencies):
            ready.append(task)
    return ready

async def scheduler(state: RunState) -> dict[str, Any]:
    """按并发上限生成 Assignment 并写入全局状态，路由函数据此做 Send 扇出。"""
    ready = _ready_tasks(state)
    budget = state.get("budget")
    max_concurrent = budget.max_concurrent_tasks if budget else 4
    cycle_count = state.get("cycle_count", 0) + 1
    max_cycles = (budget.max_review_cycles if budget else 3) * 3

    if cycle_count > max_cycles:
        logger.warning("已达到最大循环次数 %d/%d，强制终止", cycle_count, max_cycles)
        return {
            "cycle_count": cycle_count,
            "assignments": {},
            "diagnosis": Diagnosis(
                fault_domain=FaultDomain.execution_permanent,
                confidence=1.0,
                evidence=[f"已达到最大循环次数 {cycle_count}/{max_cycles}，强制终止"],
                suggested_action="finalize"
            ),
        }

    # 保留已有 assignments（如 reallocator 生成的重分配），仅补充新就绪任务
    assignments: dict[str, Assignment] = dict(state.get("assignments", {}))
    remaining_slots = max_concurrent - len(assignments)
    for task in ready[:max(remaining_slots, 0)]:
        if task.task_id not in assignments:
            assignments[task.task_id] = Assignment(
                task_id=task.task_id,
                executor_profile="default",
                model_tier="standard",
                tool_allowlist=task.tool_allowlist,
                resolved_input_refs=_resolved_dependency_inputs(state, task),
                timeout_seconds=task.timeout_seconds,
                attempt=1,
            )

    return {"cycle_count": cycle_count, "assignments": assignments}


def route_after_scheduler(state: RunState) -> str | list[Send]:
    """条件路由：有 Assignment -> Send 到 executor; 否则走向汇总或归因"""
    budget = state.get("budget")
    if budget is not None and budget.exhausted:
        return "finalizer"

    assignments = state.get("assignments", {})
    plan = state.get("plan")
    if assignments and plan is not None:
        return [
            Send("executor", {"current_assignment": assignment, "plan": plan})
            for assignment in assignments.values()
        ]

    # 没有就绪任务：判断是全部成功还是阻塞
    if plan is None:
        return "finalizer"
    status_map = _task_status_map(state)
    all_done = all(status_map.get(task.task_id) == TaskStatus.completed for task in plan.tasks)
    if all_done:
        diagnosis = state.get("diagnosis")
        if diagnosis is not None and diagnosis.suggested_action not in (None, "finalize", "reaggregate"):
            return "cause_analyzer"
        return "aggregator"                     # reaggregate 走这里，允许重新汇总
    return "cause_analyzer"


__all__ = ["scheduler", "route_after_scheduler"]
