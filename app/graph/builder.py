"""StateGraph 构建与条件路由。

对应架构设计第 4 节 LangGraph 工作流：
START -> Planner -> Scheduler -> Executor x N -> Aggregator -> Reviewer -> Finalizer -> END
失败路径进入 Cause Analyzer，再决定重规划 / 重分配 / 终止。
"""

from __future__ import annotations

from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.constants import END, START
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.graph.nodes.aggregator import aggregator
from app.graph.nodes.cause_analyzer import cause_analyzer
from app.graph.nodes.finalizer import finalizer
from app.graph.nodes.reviewer import reviewer
from app.graph.nodes.executor import executor
from app.graph.nodes.planner import planner
from app.graph.nodes.reallocator import reallocator
from app.graph.nodes.scheduler import scheduler, route_after_scheduler
from app.graph.serde import make_serde
from app.graph.state import RunState

def _route_after_reviewer(state: RunState) -> str:
    """reviewer节点后的路由"""
    review = state.get("review")
    if review is not None and review.passed:
        return "finalizer"
    return "cause_analyzer"

def _route_after_cause_analyzer(state: RunState) -> str:
    """根因分析后的路由"""
    diagnosis = state.get("diagnosis")
    if diagnosis is None:
        return "finalizer"
    action = diagnosis.suggested_action
    if action == "replan":
        return "planner"
    if action == "reallocate":
        return "reallocator"
    if action == "reaggregate":
        # 走 scheduler 保证 cycle_count 递增，有终止条件
        return "scheduler"
    return "finalizer"


def build_graph(checkpointer: BaseCheckpointSaver[Any] | None = None) -> CompiledStateGraph[RunState]:
    """构建并编译 LangGraph 工作流。

    checkpointer 为 None 时回退到 MemorySaver（便于单元测试）；
    生产环境由 services/run.get_graph() 注入 AsyncPostgresSaver。
    """
    builder = StateGraph(RunState)

    # 注册全部节点
    builder.add_node("planner", planner)
    builder.add_node("scheduler", scheduler)
    builder.add_node("executor", executor)
    builder.add_node("reviewer", reviewer)
    builder.add_node("aggregator", aggregator)
    builder.add_node("cause_analyzer", cause_analyzer)
    builder.add_node("reallocator", reallocator)
    builder.add_node("finalizer", finalizer)

    # 固定边
    builder.add_edge(START, "planner")
    builder.add_edge("planner", "scheduler")
    builder.add_edge("executor", "scheduler")  # 执行结果汇合后回到调度
    builder.add_edge("aggregator", "reviewer")
    builder.add_edge("reallocator", "scheduler")
    builder.add_edge("finalizer", END)

    # 条件边
    builder.add_conditional_edges("scheduler", route_after_scheduler)
    builder.add_conditional_edges("reviewer", _route_after_reviewer)
    builder.add_conditional_edges("cause_analyzer", _route_after_cause_analyzer)

    if checkpointer is None:
        checkpointer = MemorySaver(serde=make_serde())
    return builder.compile(checkpointer=checkpointer)

__all__ = ["build_graph"]
