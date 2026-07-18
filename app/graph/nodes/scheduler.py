"""Scheduler / Allocator 节点：校验依赖、选择就绪任务、匹配执行器/模型/工具、控制并发和预算。

输出：Assignment[] / Send[]
"""

from __future__ import annotations

from langgraph.types import Send

from app.domain import TaskStatus, Assignment, Task
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

async def scheduler(state: RunState) -> dict:
    """节点本体，递增cycle_count，具体的扇出操作由路由函数处理。"""
    return {"cycle_count": state.get("cycle_count", 0) + 1}

def route_after_scheduler(state: RunState) -> str | list[Send]:
    """条件路由：有就绪任务 -> Send到executor; 否则走向汇总或归因"""
    budget = state.get("budget")
    if budget is not None and budget.exhausted:
        return "finalizer"
    ready = _ready_tasks(state)
    if ready:
        plan = state.get("plan")
        sends: list[Send] = []
        for task in ready:
            assignment = Assignment(
                task_id=task.task_id,
                executor_profile="default",
                model_tier="standard",
                tool_allowlist=task.tool_allowlist,
                timeout_seconds=task.timeout_seconds,
                attempt=1
            )
            sends.append(Send("executor", {
                "current_assignment": assignment,
                "plan": plan
            }))
        return sends
    # 没有就绪任务：判断是全部成功还是阻塞
    plan = state.get("plan")
    if plan is None:
        return "cause_analyzer"
    status_map = _task_status_map(state)
    # 是否全部完成了
    all_done = all(
        status_map.get(t.task_id) == TaskStatus.completed
        for t in plan.tasks
    )
    return "aggregator" if all_done else "cause_analyzer"


__all__ = ["scheduler", "route_after_scheduler"]
