"""Experience Reallocator
节点：不改变目标和任务语义，调整模型、工具、执行器、上下文或重试策略。

输出：新 Assignment
"""

from __future__ import annotations

from typing import Any

from app.domain import Diagnosis, TaskStatus, Assignment
from app.domain.diagnosis import FaultDomain
from app.graph.state import RunState


def _none_diagnosis() -> dict[str, Any]:
    """返回空诊断信息"""
    return {"diagnosis": None}

async def reallocator(state: RunState) -> dict[str, Any]:
    """根据Diagnosis调整失败任务的程序策略

    """
    diagnosis: Diagnosis | None = state.get("diagnosis")
    if diagnosis is None:
        return _none_diagnosis()
    if diagnosis.fault_domain == FaultDomain.planning:
        return {}
    plan = state.get("plan")
    if plan is None:
        return _none_diagnosis()

    events = state.get("task_events", [])
    failed_task_ids: set[str] = {
        ev.task_id for ev in events if ev.status == TaskStatus.failed
    }
    if not failed_task_ids:
        return _none_diagnosis()
    old_assignments = state.get("assignments", {})

    assignments: dict[str, Assignment] = {}
    for task in plan.tasks:
        if task.task_id not in failed_task_ids:
            continue
        old = old_assignments.get(task.task_id)
        next_attempt = (old.attempt + 1) if old else 1
        if diagnosis.fault_domain in (
            FaultDomain.allocation,
            FaultDomain.execution_permanent
        ):
            assignments[task.task_id] = Assignment(
                task_id=task.task_id,
                executor_profile="default",
                model_tier=(
                    "reasoning" if (old and old.model_tier != "reasoning")
                    else "standard"
                ),
                tool_allowlist=[],
                timeout_seconds=task.timeout_seconds * 2 if task.timeout_seconds is not None else None,
                attempt=next_attempt
            )
        else:
            assignments[task.task_id] = Assignment(
                task_id=task.task_id,
                executor_profile="default",
                model_tier=old.model_tier if old else "standard",
                tool_allowlist=[],
                timeout_seconds=task.timeout_seconds,
                attempt=next_attempt
            )

    return {"assignments": assignments, "diagnosis": None}


__all__ = ["reallocator"]
