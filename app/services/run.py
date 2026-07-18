"""Run 服务：创建运行、状态流转、取消。"""

from __future__ import annotations

import uuid

from langgraph.graph.state import CompiledStateGraph

from app.domain import RunBudget
from app.graph.builder import build_graph
from app.graph.state import RunState

_graph: CompiledStateGraph[RunState] | None = None


def get_graph() -> CompiledStateGraph[RunState]:
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


async def create_run(user_request: str) -> str:
    """创建运行并驱动图执行。

    目前是 await 同步跑完，后续替换为 Redis 队列 + 独立 Worker 消费。
    """
    run_id = f"run_{uuid.uuid4().hex[:12]}"
    initial_state: RunState = {
        "run_id": run_id,
        "user_request": user_request,
        "plan": None,
        "plan_version": 0,
        "task_events": [],
        "assignments": {},
        "current_assignment": None,
        "aggregate": None,
        "review": None,
        "diagnosis": None,
        "budget": RunBudget(),
        "cycle_count": 0,
        "final_answer": None,
    }

    config = {"configurable": {"thread_id": run_id}}
    graph = get_graph()
    await graph.ainvoke(initial_state, config=config)
    return run_id


async def get_run_result(run_id: str) -> dict | None:
    """通过 Checkpointer 查询运行最终状态。"""
    config = {"configurable": {"thread_id": run_id}}
    graph = get_graph()
    snapshot = await graph.aget_state(config)
    if snapshot is None:
        return None
    return snapshot.values


__all__ = ["create_run", "get_run_result", "get_graph"]