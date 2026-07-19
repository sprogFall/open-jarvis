"""Planner 节点：理解目标、补全假设、生成任务 DAG 与总体验收标准；检索少量相关经验。

输出：Plan
"""

from __future__ import annotations

import uuid

from langchain_core.runnables.config import RunnableConfig

from app.domain.plan import Plan, Task
from app.graph.prompts.planner import PlannerDraft, planner_prompt
from app.graph.safety import sanitize_user_input
from app.graph.state import RunState
from app.graph.validation import PlanValidationError, validate_plan
from app.models import ModelTier, get_model_for_run
from app.models.structured import ainvoke_structured_with_retry


def _fallback_plan(user_request: str, issues: list[str]) -> Plan:
    """DAG校验失败的时候触发兜底单任务计划，保证图不卡死"""
    return Plan(
        plan_id=f"plan_{uuid.uuid4().hex[:8]}",
        version=1,
        objective=user_request,
        assumptions=[f"LLM生成的计划未通过DAG校验：{issues}; 已退回为单任务"],
        global_success_criteria=['产出与用户请求相关的回答'],
        tasks=[Task(
            task_id="t1",
            title="处理用户请求",
            instruction=user_request,
            dependencies=[],
            required_capabilities=["default"],
            tool_allowlist=[],
            success_criteria=["回答与用户请求相关"],
            timeout_seconds=60,
            max_attempts=2
        )]
    )

async def planner(state: RunState, config: RunnableConfig) -> dict[str, object]:
    """
    读取user_request，生成任务DAG
    """

    # 单个任务信息 后续需要替换成LLM结构化输出
    user_request = state["user_request"]
    safe_user_request = sanitize_user_input(user_request)
    model = get_model_for_run(config, ModelTier.reasoning, extra_body={"thinking": {"type": "disabled"}})
    chain = planner_prompt | model.with_structured_output(
        PlannerDraft,
        method="function_calling",
        strict=False,
        include_raw=True,
    )
    draft = await ainvoke_structured_with_retry(
        chain,
        {"user_request": safe_user_request},
        schema=PlannerDraft,
        node="planner",
    )
    plan_version = 1
    plan = Plan(
        plan_id=f"plan_{uuid.uuid4().hex[:8]}",
        version=plan_version,
        objective=user_request,
        assumptions=draft.assumptions,
        global_success_criteria=draft.global_success_criteria,
        tasks=draft.tasks
    )
    try:
        # 计划DAG检验与回退
        validate_plan(plan)
    except PlanValidationError as e:
        plan = _fallback_plan(user_request, e.issues)

    return {"plan": plan, "plan_version": plan_version}


__all__ = ["planner"]
