"""Executor 节点：根据单个任务契约调用模型与工具；上报进度；只对瞬时错误做短重试。

实现为小型子图：prepare_context -> agent/model -> tool_call（可循环、有上限）-> validate_output
输出：TaskResult
"""

from __future__ import annotations

from datetime import timezone, datetime

from app.domain import TaskResult, TaskStatus
from app.graph.state import RunState


async def executor(state: RunState) -> dict:
    """
    准备本次执行上下文 -> 模型 -> 工具调用 -> 结果校验
    :param state:
    :return:
    """
    assignment = state.get("current_assignment")
    if assignment is None:
        return {}
    plan = state.get("plan")
    task = None
    if plan is not None:
        task = next((t for t in plan.tasks if t.task_id == assignment.task_id), None)
    now = datetime.now(timezone.utc).isoformat()
    result = TaskResult(
        task_id=assignment.task_id,
        attempt=assignment.attempt,
        status=TaskStatus.completed,
        output={"answer": f"已完成: {task.title if task else assignment.task_id}"},
        started_at=now,
        ended_at=now,
        token_usage=0,
        cost=0.0,
        tools_used=[]
    )
    # 执行节点只返回task_event，current_assignment不持久化
    return {"task_events": [result]}


__all__ = ["executor"]
