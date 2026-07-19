"""Cause Analyzer 节点：根据错误、轨迹和审核意见进行结构化归因，选择下一动作。

先使用规则证据，再让 LLM 处理语义歧义，禁止仅凭模型猜测。
输出：Diagnosis
"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.runnables.config import RunnableConfig

from app.domain import Diagnosis, TaskResult, TaskStatus
from app.domain.diagnosis import FaultDomain
from app.graph.prompts.cause_analyzer import cause_analyzer_prompt, CauseAnalyzerDraft
from app.graph.state import RunState
from app.models import get_model_for_run, ModelTier
from app.models.structured import ainvoke_structured_with_retry


def _collect_rule_evidence(state: RunState) -> tuple[list[str], str | None]:
    """
    收集确定性规则证据并返回
    """
    evidence: list[str] = []
    certain_action: str | None = None

    # 1.预算耗尽的情况
    budget = state.get("budget")
    if budget is not None and budget.exhausted:
        evidence.append("预算已耗尽(Token/费用/调用次数达到上限")
        return evidence, "finalize"

    # 2.包含取消任务
    events: list[TaskResult] = state.get("task_events", [])
    cancelled = [ev.task_id for ev in events if ev.status == TaskStatus.cancelled]
    if cancelled:
        evidence.append(f"任务已被取消:{cancelled}")
        return evidence, "finalize"
    # 3.任务全部成功，但是审核未通过
    if events:
        all_ok = all(ev.status == TaskStatus.completed for ev in events)
        if all_ok:
            evidence.append("所有任务执行成功，但是审核未通过")
            return evidence, "reaggregate"

    # 剩余情况按错误码分类
    transient_ids = [
        ev.task_id for ev in events
        # 重试耗尽或任务超时
        if ev.error_code in ("llm_transient", "task_timeout")
    ]

    permanent_ids = [
        ev.task_id for ev in events
        if ev.error_code in ("llm_error", "output_validation_failed", "task_not_found")
    ]

    if transient_ids:
        evidence.append(f"瞬时错误任务(可重分配): {transient_ids}")
    if permanent_ids:
        evidence.append(f"永久错误任务: {permanent_ids}")

    # 纯瞬时任务：建议重分配
    if transient_ids and not permanent_ids:
        certain_action = "reallocate"

    return evidence, certain_action


def _format_task_summary(state: RunState) -> str:
    """任务执行信息"""
    events = state.get("task_events", [])
    if not events:
        return "（无任务结果）"
    rows: list[dict[str, Any]] = []
    for ev in events:
        rows.append({
            "task_id": ev.task_id,
            "status": ev.status.value,
            "error_code": ev.error_code,
            "error_message": (ev.error_message or "")[:200],
            "attempt": ev.attempt,
        })
    return json.dumps(rows, ensure_ascii=False, indent=2)

def format_task_summary(state: RunState) -> str:
    return _format_task_summary(state)


def _format_review_summary(state: RunState) -> str:
    """检查结果"""
    review = state.get("review")
    if review is None:
        return "（未审核）"
    return json.dumps({
        "passed": review.passed,
        "score": review.score,
        "issues": review.issues,
        "suggested_action": review.suggested_action,
    }, ensure_ascii=False, indent=2)


def _format_budget_status(state: RunState) -> str:
    """预算信息"""
    budget = state.get("budget")
    if budget is None:
        return "（无预算信息）"
    return json.dumps({
        "exhausted": budget.exhausted,
        "used_tokens": budget.used_tokens,
        "max_tokens": budget.max_tokens,
        "used_model_calls": budget.used_model_calls,
        "max_model_calls": budget.max_model_calls,
        "cycle_count": state.get("cycle_count", 0),
        "plan_version": state.get("plan_version", 0),
    }, ensure_ascii=False, indent=2)


async def cause_analyzer(state: RunState, config: RunnableConfig) -> dict[str, Any]:
    # 优先通过代码规则判断错误原因与重试路线
    rule_evidence, certain_action = _collect_rule_evidence(state)
    if certain_action is not None:
        # 代表可以通过规则确定动作，则直接跳过LLM判别
        domain = {
            "reallocate": FaultDomain.execution_transient,
            "replan": FaultDomain.planning,
            "reaggregate": FaultDomain.review,
            "finalize": FaultDomain.execution_permanent
        }.get(certain_action, FaultDomain.execution_permanent)
        return {"diagnosis": Diagnosis(
            fault_domain=domain,
            confidence=1.0,
            evidence=rule_evidence,
            suggested_action=certain_action
        )}

    # 规则无法确定的，需要LLM判断归因
    model = get_model_for_run(config, ModelTier.fast)
    chain = cause_analyzer_prompt | model.with_structured_output(
        CauseAnalyzerDraft,
        method="function_calling",
        include_raw=True,
    )
    plan = state.get("plan")
    try:
        draft: CauseAnalyzerDraft = await ainvoke_structured_with_retry(
            chain,
            {
                "objective": plan.objective if plan else "未知",
                "task_count": len(plan.tasks) if plan else 0,
                "rule_evidence": "\n".join(rule_evidence) if rule_evidence else "（无确定性证据）",
                "task_summary": _format_task_summary(state),
                "review_summary": _format_review_summary(state),
                "budget_status": _format_budget_status(state),
            },
            schema=CauseAnalyzerDraft,
            node="cause_analyzer"
        )
    except Exception as e:
        print(f"归因失败： {str(e)}")
        return {"diagnosis": Diagnosis(
            fault_domain=FaultDomain.execution_permanent,
            confidence=0.0,
            evidence=rule_evidence + ["LLM归因失败，兜底终止"],
            suggested_action="finalize"
        )}

    return {"diagnosis": Diagnosis(
        fault_domain=draft.fault_domain,
        confidence=draft.confidence,
        evidence=rule_evidence + draft.additional_evidence,
        suggested_action=draft.suggested_action,
    )}


__all__ = ["cause_analyzer", "format_task_summary"]
