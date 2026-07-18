"""Run 服务：创建运行、状态流转、取消。

当前阶段：图以进程内 asyncio 后台任务执行，create_run 立即返回 run_id，
前端通过 GET /runs/{run_id} 轮询状态。
TODO（持久化步）：替换为 Redis run_queue + 独立 Worker 进程消费，
避免 API 重启导致运行中任务丢失（架构设计第 3、8.2 节）。
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph

from app.domain import RunBudget
from app.graph.builder import build_graph
from app.graph.state import RunState

logger = logging.getLogger(__name__)

_graph: CompiledStateGraph[RunState] | None = None


async def get_graph() -> CompiledStateGraph[RunState]:
    """惰性构建并缓存编译后的图。

    生产环境注入 AsyncPostgresSaver（PostgreSQL Checkpointer，架构第 8.1 节）；
    测试中可直接覆盖 _graph 为 fake graph 绕过本方法。
    """
    global _graph
    if _graph is None:
        # 延迟导入：避免健康检查等不触图场景在 import 阶段拉起 psycopg
        from app.graph.checkpointer import get_checkpointer

        checkpointer = await get_checkpointer()
        _graph = build_graph(checkpointer)
    return _graph


# 运行中的后台任务注册表：run_id -> asyncio.Task
# 单事件循环内 dict 读写安全；进程重启后丢失，持久化步将替换为 Redis。
running_tasks: dict[str, asyncio.Task[None]] = {}


async def _execute_run(run_id: str, initial_state: RunState, config: RunnableConfig) -> None:
    """后台驱动图执行，异常记录到日志避免被静默吞没。

    任务结束后仍保留在 _running_tasks 中，便于 get_run_result 读取 done/failed
    终态；持久化步替换为 Redis 后此注册表自然失效。
    """
    try:
        graph = await get_graph()
        await graph.ainvoke(initial_state, config=config)
    except Exception:
        logger.exception("run %s 执行失败", run_id)
        raise


def _on_run_done(task: asyncio.Task[None]) -> None:
    """消费后台任务异常，避免未捕获异常被静默丢弃。"""
    try:
        task.result()
    except asyncio.CancelledError:
        pass
    except Exception:
        # 已在 _execute_run 中记录日志，此处仅消费避免未检索异常告警
        pass


async def create_run(user_request: str) -> str:
    """创建运行并立即返回 run_id，图在后台异步执行。

    状态通过 get_run_result(run_id) 查询（读取 Checkpointer 快照 + 任务注册表）。
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

    config: RunnableConfig = {
        "configurable": {"thread_id": run_id},
        "metadata": {"workflow_run_id": run_id},
    }
    task = asyncio.create_task(_execute_run(run_id, initial_state, config), name=f"run-{run_id}")
    task.add_done_callback(_on_run_done)
    running_tasks[run_id] = task
    return run_id


def _resolve_status(run_id: str, values: dict[str, Any]) -> str:
    """结合任务注册表与图状态推断运行状态。

    优先级：后台任务异常 > 任务仍在运行 > final_answer 终态 > 兜底 running。
    """
    task = running_tasks.get(run_id)
    if task is not None and task.done() and task.exception() is not None:
        return "failed"
    if task is not None and not task.done():
        return "running"
    final = values.get("final_answer")
    if final is not None:
        return str(final.status.value)
    if task is not None and task.done():
        return "done"
    return "running"


async def get_run_result(run_id: str) -> dict[str, Any] | None:
    """查询运行状态：Checkpointer 快照 + 后台任务注册表。

    返回的 dict 额外带 ``status`` 字段（running / done / failed / success /
    partial / cancelled），便于前端轮询。运行失败时附带 ``error``。
    """
    task = running_tasks.get(run_id)
    config: RunnableConfig = {"configurable": {"thread_id": run_id}}
    graph = await get_graph()
    snapshot = await graph.aget_state(config)

    # 既无快照也无后台任务：确实不存在
    if snapshot is None and task is None:
        return None

    # LangGraph 对未知 thread_id 可能返回空快照（非 None），需二次判断
    if task is None and (snapshot is None or snapshot.values is None or not snapshot.values):
        return None

    values: dict[str, Any] = dict(snapshot.values) if snapshot and snapshot.values else {}
    status = _resolve_status(run_id, values)
    values["status"] = status

    if status == "failed" and task is not None and task.exception() is not None:
        values["error"] = str(task.exception())

    return values


__all__ = ["create_run", "get_run_result", "get_graph", "running_tasks"]
