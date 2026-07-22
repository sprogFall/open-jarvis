"""Reviewer 节点：按总体与逐任务验收标准检查完整性、正确性、证据和约束。

使用独立提示词；高风险场景可配置不同模型，降低同源偏差。
输出：ReviewResult
"""

from __future__ import annotations

from langchain_core.runnables.config import RunnableConfig

from app.domain import ReviewResult, TaskStatus
from app.graph.clock import format_clock_from_state
from app.graph.projection import (
    format_latest_task_results,
    format_task_contracts,
    latest_task_results,
)
from app.graph.prompts.reviewer import ReviewerDraft, reviewer_prompt
from app.graph.state import RunState
from app.models import ModelTier, get_model_for_run
from app.models.structured import ainvoke_structured_with_retry

_FAILED_STATUSES = {TaskStatus.failed, TaskStatus.cancelled}


async def reviewer(state: RunState, config: RunnableConfig) -> dict[str, object]:
    """规则预检 + LLM语义审核

    规则预检只看「当前计划版本」下每任务最新状态，避免历史 failed 永久否决。
    """
    latest = latest_task_results(state)
    failed_task_ids = [
        task_id
        for task_id, result in latest.items()
        if result.status in _FAILED_STATUSES
    ]
    # 有失败/取消任务直接判否，不调用LLM
    if failed_task_ids:
        return {"review": ReviewResult(
            passed=False,
            score=0.0,
            failed_task_ids=failed_task_ids,
            issues=[f"任务未成功：{failed_task_ids}"],
            suggested_action="replan"
        )}

    plan = state.get("plan")
    aggregate = state.get("aggregate")
    model = get_model_for_run(
        config=config,
        tier=ModelTier.reasoning,
        extra_body={"thinking": {"type": "disabled"}},
    )
    chain = reviewer_prompt | model.with_structured_output(
        ReviewerDraft,
        method="function_calling",
        strict=False,
        include_raw=True,
    )
    assumptions = "\n".join(plan.assumptions) if plan and plan.assumptions else "（无）"
    global_criteria = (
        "\n".join(plan.global_success_criteria) if plan and plan.global_success_criteria else "（无）"
    )
    draft = await ainvoke_structured_with_retry(
        chain,
        {
            "current_time": format_clock_from_state(state),
            "objective": plan.objective if plan else "",
            "assumptions": assumptions,
            "global_success_criteria": global_criteria,
            "task_contracts": format_task_contracts(plan),
            "task_results": format_latest_task_results(state),
            "candidate_answer": aggregate.candidate_answer if aggregate else "",
        },
        schema=ReviewerDraft,
        node="reviewer",
    )
    review = ReviewResult(
        passed=draft.passed,
        score=draft.score,
        failed_task_ids=[],  # 已通过规则校验无失败任务
        issues=draft.issues,
        evidence_refs=[],
        suggested_action=draft.suggested_action,
    )
    return {"review": review}


__all__ = ["reviewer"]
