"""模型调用日志回调，不记录 Prompt、响应正文或密钥。"""

from __future__ import annotations

import logging
import time
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID

from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult

logger = logging.getLogger(__name__)


def _safe_endpoint(url: str) -> str:
    """只保留服务地址，移除用户信息、查询参数和 fragment。"""
    if not url:
        return "https://api.openai.com/v1"
    parsed = urlsplit(url)
    hostname = parsed.hostname or "unknown-host"
    if ":" in hostname:
        hostname = f"[{hostname}]"
    port = f":{parsed.port}" if parsed.port is not None else ""
    path = parsed.path.rstrip("/")
    return f"{parsed.scheme or 'https'}://{hostname}{port}{path}"


def _one_line(value: object) -> str:
    return " ".join(str(value).split())


def _error_chain(error: BaseException) -> str:
    parts: list[str] = []
    seen: set[int] = set()
    current: BaseException | None = error
    while current is not None and id(current) not in seen and len(parts) < 5:
        seen.add(id(current))
        detail = _one_line(current) or "<no message>"
        parts.append(f"{type(current).__name__}: {detail}")
        current = current.__cause__ or current.__context__
    return " <- ".join(parts)


def _usage(response: LLMResult) -> tuple[int, int, int]:
    usage: Mapping[str, Any] = {}
    if isinstance(response.llm_output, Mapping):
        candidate = response.llm_output.get("token_usage") or response.llm_output.get("usage")
        if isinstance(candidate, Mapping):
            usage = candidate

    input_tokens = int(usage.get("prompt_tokens", usage.get("input_tokens", 0)) or 0)
    output_tokens = int(usage.get("completion_tokens", usage.get("output_tokens", 0)) or 0)
    total_tokens = int(usage.get("total_tokens", input_tokens + output_tokens) or 0)
    return input_tokens, output_tokens, total_tokens


class ModelLoggingCallback(AsyncCallbackHandler):
    """为每次 LangChain ChatModel 调用输出可关联、可诊断的生命周期日志。"""

    def __init__(self, *, tier: str, model: str, endpoint: str, sdk_max_retries: int) -> None:
        self.tier = tier
        self.model = model
        self.endpoint = _safe_endpoint(endpoint)
        self.sdk_max_retries = sdk_max_retries
        self._started_at: dict[UUID, float] = {}

    async def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[BaseMessage]],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        del serialized, parent_run_id, tags, kwargs
        self._started_at[run_id] = time.perf_counter()
        context = metadata or {}
        logger.info(
            "LLM call started llm_run_id=%s workflow_run_id=%s node=%s "
            "tier=%s model=%s endpoint=%s messages=%d sdk_max_retries=%d",
            run_id,
            context.get("workflow_run_id", "-"),
            context.get("langgraph_node", "-"),
            self.tier,
            self.model,
            self.endpoint,
            sum(len(batch) for batch in messages),
            self.sdk_max_retries,
        )

    async def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        del parent_run_id, tags, kwargs
        input_tokens, output_tokens, total_tokens = _usage(response)
        logger.info(
            "LLM call succeeded llm_run_id=%s tier=%s model=%s duration_ms=%d "
            "input_tokens=%d output_tokens=%d total_tokens=%d",
            run_id,
            self.tier,
            self.model,
            self._duration_ms(run_id),
            input_tokens,
            output_tokens,
            total_tokens,
        )

    async def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        del parent_run_id, tags, kwargs
        status_code = getattr(error, "status_code", None) or "-"
        request_id = getattr(error, "request_id", None) or "-"
        logger.error(
            "LLM call failed llm_run_id=%s tier=%s model=%s endpoint=%s duration_ms=%d "
            "error_type=%s status_code=%s request_id=%s error_chain=%r",
            run_id,
            self.tier,
            self.model,
            self.endpoint,
            self._duration_ms(run_id),
            type(error).__name__,
            status_code,
            request_id,
            _error_chain(error),
        )

    def _duration_ms(self, run_id: UUID) -> int:
        started_at = self._started_at.pop(run_id, None)
        if started_at is None:
            return 0
        return round((time.perf_counter() - started_at) * 1000)


__all__ = ["ModelLoggingCallback"]
