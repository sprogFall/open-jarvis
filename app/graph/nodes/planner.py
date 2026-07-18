"""Planner 节点：理解目标、补全假设、生成任务 DAG 与总体验收标准；检索少量相关经验。

输出：Plan
"""

from __future__ import annotations

import uuid

from app.graph.state import RunState
from app.domain.plan import Task, Plan


async def planner(state: RunState) -> dict:
    """
    读取user_request，生成任务DAG
    :param state:
    :return:
    """

    # 单个任务信息 后续需要替换成LLM结构化输出
    user_request = state["user_request"]
    task = Task(
        task_id="t1",
        title="处理用户请求",
        instruction=user_request,
        dependencies=[],
        required_capabilities=["default"],
        tool_allowlist=[],
        success_criteria=["产出与用户请求相关的问题"],
        timeout_seconds=60,
        max_attempts=2,
    )
    plan_version = 1
    plan = Plan(
        plan_id=f"plan_{uuid.uuid4().hex[:8]}",
        version=plan_version,
        objective=user_request,
        assumptions=["用户请求明确，无需澄清"],
        global_success_criteria=["回答内容与用户请求相关且完整"],
        tasks=[task]
    )
    return {"plan": plan, "plan_version": plan_version}


__all__ = ["planner"]
