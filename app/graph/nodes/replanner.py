"""Experience Replanner 节点：保留仍有效的成功结果，修订任务、依赖或验收条件，递增计划版本。

输出：新 Plan
"""

from __future__ import annotations

from app.graph.state import RunState


async def replanner(state: RunState) -> dict:
    plan = state.get("plan")
    if plan is None:
        return {}
    new_version = state.get("plan_version", 1) + 1
    return {
        "plan_version": new_version,
        "plan": plan.model_copy(update={"version": new_version})
    }


__all__ = ["replanner"]
