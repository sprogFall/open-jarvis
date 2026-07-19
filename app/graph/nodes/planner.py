"""Planner 节点：理解目标、补全假设、生成任务 DAG 与总体验收标准；检索少量相关经验。

输出：Plan
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from langchain_core.runnables.config import RunnableConfig

from app.domain.plan import Plan, Task
from app.graph.nodes.cause_analyzer import format_task_summary
from app.graph.prompts.planner import PlannerDraft, planner_prompt, replanner_prompt, ReplannerDraft
from app.graph.safety import sanitize_user_input
from app.graph.state import RunState
from app.graph.validation import PlanValidationError, validate_plan
from app.models import ModelTier, get_model_for_run
from app.models.structured import ainvoke_structured_with_retry

logger = logging.getLogger(__name__)


def _generate_plan_id() -> str:
    return f"plan_{uuid.uuid4().hex[:8]}"

def _fallback_plan(user_request: str, issues: list[str], version: int = 1) -> Plan:
    """DAG校验失败的时候触发兜底单任务计划，保证图不卡死"""
    return Plan(
        plan_id=_generate_plan_id(),
        version=version,
        objective=user_request,
        assumptions=[f"自动规划失败，回退单步执行模式。原因：{issues}"],
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

def _build_context(state: RunState) -> dict[str, Any]:
    """从当前状态构建重规划所需的上下文"""
    plan = state["plan"]
    plan_version = state.get("plan_version", 0)
    diagnosis = state.get("diagnosis")
    return {
        "objective": plan.objective,
        "plan_version": str(plan_version),
        "fault_domain": diagnosis.fault_domain.value if diagnosis else "unknown",
        "diagnosis_evidence": "\n".join(diagnosis.evidence) if diagnosis else "（无）",
        "suggested_action": (diagnosis.suggested_action or "replan") if diagnosis else "replan",
        "task_summary": format_task_summary(state),
        "current_plan_json": plan.model_dump_json(indent=2),
    }


async def planner(state: RunState, config: RunnableConfig) -> dict[str, object]:
    """
    Planner 双模式入口。
    """
    user_request = state["user_request"]
    existing_plan = state.get("plan")
    diagnosis = state.get("diagnosis")
    plan_version = state.get("plan_version", 0)

    # 判断模式：有现有 plan 且有 diagnosis（suggested_action=replan）→ 重规划模式
    is_replan = (
        existing_plan is not None
        and diagnosis is not None
        and diagnosis.suggested_action == "replan"
    )
    model = get_model_for_run(config, ModelTier.reasoning, extra_body={"thinking": {"type": "disabled"}})
    if is_replan:
        replan_context = _build_context(state)
        chain = replanner_prompt | model.with_structured_output(
            ReplannerDraft,
            method="function_calling",
            strict=False,
            include_raw=True
        )
        new_version = plan_version + 1
        try:
            replan_draft: ReplannerDraft = await ainvoke_structured_with_retry(
                chain,
                replan_context,
                schema=ReplannerDraft,
                node="planner",
            )
        except Exception as e:
            logger.error("重新规划失败: %s", str(e))
            return {
                "plan": _fallback_plan(user_request, [f"LLM重规划失败：{str(e)}"], version=new_version),
                "plan_version": new_version,
                "diagnosis": None
            }
        plan = Plan(
            plan_id=_generate_plan_id(),
            version=new_version,
            objective=replan_draft.objective,
            assumptions=replan_draft.assumptions,
            global_success_criteria=replan_draft.global_success_criteria,
            tasks=replan_draft.tasks
        )
        # DAG校验
        try:
            validate_plan(plan)
        except PlanValidationError as e:
            plan = _fallback_plan(user_request, e.issues, version=new_version)
            return {"plan": plan, "plan_version": new_version, "diagnosis": None}

        return {"plan": plan, "plan_version": new_version, "diagnosis": None}

    else:
        # 首次规划模式
        safe_user_request = sanitize_user_input(user_request)
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
        plan_version = plan_version + 1
        # 使用 LLM 精炼后的 objective，而非原始 user_request
        plan = Plan(
            plan_id=_generate_plan_id(),
            version=plan_version,
            objective=draft.objective,
            assumptions=draft.assumptions,
            global_success_criteria=draft.global_success_criteria,
            tasks=draft.tasks
        )
        try:
            validate_plan(plan)
            return {"plan": plan, "plan_version": plan_version}
        except PlanValidationError as e:
            plan = _fallback_plan(user_request, e.issues, version=plan_version)
            return {"plan": plan, "plan_version": plan_version}


__all__ = ["planner"]
