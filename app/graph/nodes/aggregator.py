"""Aggregator 节点：去重、排序、解析引用并确定性合并任务产物；必要时生成面向审核的候选答案。

输出：AggregateResult
"""

from __future__ import annotations

from typing import Any

from app.domain import AggregateResult, TaskStatus, TaskResult
from app.graph.projection import format_structured_candidate, latest_task_results
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

    # 仅投影当前计划版本的最新成功输出
    latest_results = latest_task_results(state)
    latest_outputs: dict[str, Any] = {}
    for task_id, result in latest_results.items():
        if result.status == TaskStatus.completed and result.output is not None:
            latest_outputs[task_id] = result.output

    plan = state.get("plan")
    # 按计划任务顺序组装 outputs
    task_order = [t.task_id for t in plan.tasks] if plan else list(latest_outputs.keys())
    outputs: dict[str, Any] = {
        tid: latest_outputs[tid] for tid in task_order if tid in latest_outputs
    }
    candidate = format_structured_candidate(plan, outputs)

    result: dict[str, Any] = {
        "aggregate": AggregateResult(candidate_answer=candidate, task_outputs=outputs)
    }
    if updated_budget is not None:
        result["budget"] = updated_budget
    return result


__all__ = ["aggregator"]
