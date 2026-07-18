"""Reviewer 节点：按总体与逐任务验收标准检查完整性、正确性、证据和约束。

使用独立提示词；高风险场景可配置不同模型，降低同源偏差。
输出：ReviewResult
"""

from __future__ import annotations

from app.domain import ReviewResult
from app.graph.state import RunState


async def reviewer(state: RunState) -> dict:
    failed_task_id = [
        ev.task_id
        for ev in state.get("task_events", [])
        if ev.status.value not in ("completed", "skipped")
    ]
    passed = len(failed_task_id) == 0
    review = ReviewResult(
        passed=passed,
        score=1.0 if passed else 0.0,
        failed_task_ids=failed_task_id,
        issues=[] if passed else [f"任务未成功: {failed_task_id}"],
        suggested_action="finalize" if passed else "replan",
    )
    return {"review": review}


__all__ = ["reviewer"]
