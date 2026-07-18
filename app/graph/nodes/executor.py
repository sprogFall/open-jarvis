"""Executor 节点：根据单个任务契约调用模型与工具；上报进度；只对瞬时错误做短重试。

实现为小型子图：prepare_context -> agent/model -> tool_call（可循环、有上限）-> validate_output
输出：TaskResult
"""

from __future__ import annotations

from datetime import timezone, datetime

from langchain_core.messages.ai import AIMessage
from langchain_core.runnables.config import RunnableConfig
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.domain import TaskResult, TaskStatus
from app.graph.prompts.executor import executor_prompt
from app.graph.safety import sanitize_user_input
from app.graph.state import RunState
from app.models import get_model_for_run

# 输出上限控制
_MAX_OUTPUT_LENGTH = 20000

class TransientLLMError(Exception):
    """可重试的瞬时错误：超时、限流、网络错误等"""

def _is_transient(exc: Exception) -> bool:
    """判断是否为可重试的瞬时错误"""
    msg = str(exc).lower()
    markers = [
        "timeout", "timed out", "connection", "429", "rate limit",
        "service_unavailable", "503", "502", "internal server error", "500"
    ]
    return any(m in msg for m in markers)

def _now() -> str:
    """当前时间"""
    return datetime.now(timezone.utc).isoformat()

async def _invoke_with_retry(chain, inputs: dict) -> AIMessage:
    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(3), # 1次正常+2次重试机会
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(TransientLLMError),
        reraise=True
    ):
        with attempt:
            try:
                return await chain.ainvoke(inputs)
            except Exception as e:
                if _is_transient(e):
                    raise TransientLLMError(str(e)) from e
                raise
    # 理论不可达，兜底
    raise RuntimeError("unknown error")

def _extract_text(response: AIMessage) -> str:
    # 兼容content为str或 content_block列表的情况
    content = response.content
    if isinstance(content, str):
        return content
    parts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
    return "".join(parts) if parts else str(content)

def validate_output(answer: str) -> str | None:
    """模型输出校验

    当前阶段输出为自由文本，做基本非空与长度校验。
    后续若任务定义 output_schema，在此做结构校验。
    """
    if not answer or not answer.strip():
        return "模型输出为空"
    if len(answer) > _MAX_OUTPUT_LENGTH:
        return f"模型输出过长（{len(answer)} > {_MAX_OUTPUT_LENGTH}）"
    return None

def _extract_token(response: AIMessage) -> int:
    usage = getattr(response, "usage_metadata", None)
    if isinstance(usage, dict):
        return int(usage.get("total_tokens", 0))
    meta = getattr(response, "response_metadata", None) or {}
    token_usage = meta.get("token_usage") or meta.get("usage")
    if isinstance(token_usage, dict):
        return int(token_usage.get("token_tokens", 0))
    return 0


async def executor(state: RunState, config: RunnableConfig) -> dict:
    """
    准备本次执行上下文 -> 模型 -> 工具调用 -> 结果校验
    """
    assignment = state.get("current_assignment")
    if assignment is None:
        return {}
    plan = state.get("plan")
    task = None
    if plan is not None:
        task = next((t for t in plan.tasks if t.task_id == assignment.task_id), None)

    if task is None:
        now = _now()
        return {"task_events": [TaskResult(
            task_id=assignment.task_id,
            attempt=assignment.attempt,
            status=TaskStatus.failed,
            error_code="task_not_fount",
            error_message=f"计划中找不到任务 {assignment.task_id}",
            started_at=now,
            ended_at=now
        )]}
    model = get_model_for_run(config, assignment.model_tier)
    chain = executor_prompt | model
    started_at = _now()
    try:
        response: AIMessage = await _invoke_with_retry(chain, {
            "objective": sanitize_user_input(plan.objective),
            "task_title": task.title,
            "instruction": sanitize_user_input(task.instruction),
            "success_criteria": "\n".join(task.success_criteria) or "（无显式标准）",
        })
        answer = _extract_text(response)

        validate_error = validate_output(answer)
        if validate_error is None:
            # 任务正常完成返回
            task_result = TaskResult(
                task_id=assignment.task_id,
                attempt=assignment.attempt,
                status=TaskStatus.completed,
                output={"answer": answer},
                started_at=started_at,
                ended_at=_now(),
                token_usage=_extract_token(response),
                cost=0.0,
                tools_used=[]
            )
        else:
            # 被validate_output拦截
            task_result = TaskResult(
                task_id=assignment.task_id,
                attempt=assignment.attempt,
                status=TaskStatus.failed,
                error_code="output_validation_failed",
                error_message=validate_error,
                started_at=started_at,
                ended_at=_now()
            )

    except TransientLLMError as e:
        # 重试耗尽仍失败：瞬时错误，可由图级重分配重试
        task_result = TaskResult(
            task_id=assignment.task_id,
            attempt=assignment.attempt,
            status=TaskStatus.failed,
            error_code="llm_transient",
            error_message=f"重试耗尽：{e}",
            started_at=started_at,
            ended_at=_now(),
        )
    except Exception as e:  # noqa: BLE001 - 非瞬时错误：语义/权限/参数，交还图级归因
        task_result = TaskResult(
            task_id=assignment.task_id,
            attempt=assignment.attempt,
            status=TaskStatus.failed,
            error_code="llm_error",
            error_message=str(e),
            started_at=started_at,
            ended_at=_now(),
        )
    return {"task_events": [task_result]}


__all__ = ["executor", "validate_output"]
