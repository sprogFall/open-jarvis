"""Finalizer 节点：生成最终响应；预算耗尽时明确已完成内容、失败项和原因。

输出：FinalAnswer
"""

from __future__ import annotations

from langchain_core.messages.ai import AIMessage
from langchain_core.runnables.config import RunnableConfig

from app.domain import RunStatus, FinalAnswer
from app.graph.prompts.finalizer import finalizer_prompt
from app.graph.safety import sanitize_user_input
from app.graph.state import RunState
from app.models import get_model_for_run, ModelTier


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
