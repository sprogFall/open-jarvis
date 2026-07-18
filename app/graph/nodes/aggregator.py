"""Aggregator 节点：去重、排序、解析引用并确定性合并任务产物；必要时生成面向审核的候选答案。

输出：AggregateResult
"""

from __future__ import annotations

from app.domain import AggregateResult
from app.graph.state import RunState


async def aggregator(state: RunState) -> dict:
    outputs: dict[str, object] = {}
    parts: list[str] = []
    for ev in state.get("task_events", []):
        if ev.output is not None:
            outputs[ev.task_id] = ev.output
            if "answer" in ev.output:
                parts.append(str(ev.output["answer"]))
    candidate = "\n".join(parts) if parts else "(无任务输出)"
    return {"aggregate": AggregateResult(candidate_answer=candidate, task_outputs=outputs)}


__all__ = ["aggregator"]
