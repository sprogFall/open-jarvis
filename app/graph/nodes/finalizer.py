"""Finalizer 节点：生成最终响应；预算耗尽时明确已完成内容、失败项和原因。

输出：FinalAnswer
"""

from __future__ import annotations

from alembic.util import status

from app.domain import RunStatus, FinalAnswer
from app.graph.state import RunState


async def finalizer(state: RunState) -> dict:
    aggregate = state.get("aggregate")
    review = state.get("review")

    if aggregate is not None:
        content = aggregate.candidate_answer
        result_status = RunStatus.success if review.passed else RunStatus.partial
    else:
        content = "未能完成任务。"
        result_status = RunStatus.failed
    return {"final_answer": FinalAnswer(content=content, status=result_status)}


__all__ = ["finalizer"]
