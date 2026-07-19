"""Finalizer 节点：生成最终响应；预算耗尽时明确已完成内容、失败项和原因。

输出：FinalAnswer
"""

from __future__ import annotations

from langchain_core.messages.ai import AIMessage
from langchain_core.runnables.config import RunnableConfig

from app.domain import FinalAnswer, RunStatus, TaskStatus
from app.graph.prompts.finalizer import finalizer_prompt
from app.graph.safety import sanitize_user_input
from app.graph.state import RunState
from app.models import ModelTier, get_model_for_run


def _extract_text(response: AIMessage) -> str:
    content = response.content
    if isinstance(content, str):
        return content
    parts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
    return "".join(parts) if parts else str(content)

async def finalizer(state: RunState, config: RunnableConfig) -> dict:
    aggregate = state.get("aggregate")
    review = state.get("review")

    if aggregate is None:
        # 失败路径在 Aggregator 前结束：从 task_events 中提取已完成任务的部分结果（按 task_id 去重）
        task_events = state.get("task_events", [])
        latest_outputs: dict[str, str] = {}
        for ev in task_events:
            if ev.status == TaskStatus.completed and ev.output and "answer" in ev.output:
                latest_outputs[ev.task_id] = str(ev.output["answer"])
        if latest_outputs:
            return {"final_answer": FinalAnswer(
                content="\n".join(latest_outputs.values()),
                status=RunStatus.partial,
                warnings=["任务未全部完成，以下为已完成任务的部分结果"]
            )}
        return {"final_answer": FinalAnswer(
            content="未能完成任务。",
            status=RunStatus.failed
        )}
    model = get_model_for_run(config, ModelTier.standard)
    chain = finalizer_prompt | model
    response: AIMessage = await chain.ainvoke({
        "user_request": sanitize_user_input(state.get("user_request", "")),
        "candidate_answer": aggregate.candidate_answer,
        "review_passed": str(review.passed) if review else "False",
        "review_issues": "\n".join(review.issues) if review else "（无）"
    })
    status = RunStatus.success if (review and review.passed) else RunStatus.partial
    return {"final_answer": FinalAnswer(
        content=_extract_text(response),
        status=status,
        artifact_refs=aggregate.artifact_refs
    )}


__all__ = ["finalizer"]
