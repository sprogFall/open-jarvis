"""Aggregator 节点：去重、排序、解析引用并确定性合并任务产物；必要时生成面向审核的候选答案。

输出：AggregateResult
"""

from __future__ import annotations

from typing import Any

from app.domain import AggregateResult, TaskStatus
from app.graph.state import RunState


async def aggregator(state: RunState) -> dict[str, Any]:
    task_events = state.get("task_events", [])
    budget = state.get("budget")
    if budget is not None:
        updated_budget = budget.model_copy()
        # 只统计尚未计入预算的事件，避免重复累加导致消耗虚假膨胀
        counted = budget.counted_event_count
        new_events = task_events[counted:]
        for ev in new_events:
            # 统计所有事件的消耗（完成和失败都消耗了 token/调用）
            updated_budget.used_model_calls += 1
            updated_budget.used_tokens += (ev.token_usage or 0)
            updated_budget.used_cost += (ev.cost or 0)
        updated_budget.counted_event_count = len(task_events)
    else:
        updated_budget = None

    # 每任务只取最新成功事件（event 追加顺序保证最新在后）
    latest: dict[str, dict[str, Any]] = {}
    for ev in task_events:
        if ev.status == TaskStatus.completed and ev.output is not None:
            latest[ev.task_id] = ev.output

    # 按计划任务顺序输出，确保确定性
    plan = state.get("plan")
    task_order = [t.task_id for t in plan.tasks] if plan else list(latest.keys())
    outputs: dict[str, Any] = {}
    parts: list[str] = []
    for tid in task_order:
        output = latest.get(tid)
        if output is not None:
            outputs[tid] = output
            if "answer" in output:
                parts.append(str(output["answer"]))

    candidate = "\n".join(parts) if parts else "(无任务输出)"
    result: dict[str, Any] = {
        "aggregate": AggregateResult(candidate_answer=candidate, task_outputs=outputs)
    }
    if updated_budget is not None:
        result["budget"] = updated_budget
    return result


__all__ = ["aggregator"]
