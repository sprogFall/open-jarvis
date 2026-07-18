"""Reviewer 节点：按总体与逐任务验收标准检查完整性、正确性、证据和约束。

使用独立提示词；高风险场景可配置不同模型，降低同源偏差。
输出：ReviewResult
"""

from __future__ import annotations

import json

from langchain_core.runnables.config import RunnableConfig

from app.domain import ReviewResult
from app.graph.prompts.reviewer import ReviewerDraft, reviewer_prompt
from app.graph.state import RunState
from app.models import ModelTier, get_model_for_run

_FAILED_STATUSES = {"failed", "cancelled"}

def _format_task_result(state: RunState) -> str:
    """把task_event转换为给LLM看的紧凑文本"""
    events = state.get("task_events", [])
    if not events:
        return "（无任务结果）"
    rows = []
    for ev in events:
        answer = ""
        if ev.output and "answer" in ev.output:
            answer = str(ev.output["answer"])[:500]
        rows.append({
            "task_id": ev.task_id,
            "status": ev.status.value,
            "answer": answer,
            "error": ev.error_message
        })
    return json.dumps(rows, ensure_ascii=False, indent=2)

async def reviewer(state: RunState, config: RunnableConfig) -> dict:
    """规则预检 + LLM语义审核"""
    events = state.get("task_events", [])
    failed_task_id = [
        ev.task_id for ev in events if ev.status.value in _FAILED_STATUSES
    ]
    # 有的任务直接判否，不调用LLM
    if failed_task_id:
        return {"review": ReviewResult(
            passed=False,
            score=0.0,
            failed_task_ids=failed_task_id,
            issues=[f"任务未成功：{failed_task_id}"],
            suggested_action="replan"
        )}
    plan = state.get("plan")
    aggregate = state.get("aggregate")
    model = get_model_for_run(config, ModelTier.standard)
    # 使用 ReviewerDraft 限定 LLM 只输出评分、问题和动作，任务 ID 等事实由代码维护
    chain = reviewer_prompt | model.with_structured_output(ReviewerDraft)
    # 调用LLM，送入参数 获取review结果
    draft: ReviewerDraft = await chain.ainvoke({
        "objective": plan.objective if plan else "",
        "global_success_criteria": "\n".join(plan.global_success_criteria) if plan else "（无）",
        "task_results": _format_task_result(state),
        "candidate_answer": aggregate.candidate_answer if aggregate else ""
    })
    review = ReviewResult(
        passed=draft.passed,
        score=draft.score,
        failed_task_ids=[], # 已通过规则校验无失败任务
        issues=draft.issues,
        evidence_refs=[],   # 证据引用留到经验/审计步骤
        suggested_action=draft.suggested_action
    )
    return {"review": review}


__all__ = ["reviewer"]
