"""结构化模型输出的解析重试与安全诊断。"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping
from json import JSONDecodeError
from typing import Any

from langchain_core.exceptions import OutputParserException
from pydantic import ValidationError

logger = logging.getLogger(__name__)

_DEFAULT_MAX_ATTEMPTS = 3
_DEFAULT_RETRY_DELAY_SECONDS = 1.0
_PARSING_EXCEPTIONS = (OutputParserException, ValidationError, JSONDecodeError)


class StructuredOutputError(RuntimeError):
    """结构化输出经过重试后仍无法解析。"""


def _raw_diagnostics(result: object) -> tuple[str, int, str, bool, str]:
    """提取不包含 Prompt、响应正文和工具参数的安全诊断字段。"""
    if not isinstance(result, Mapping):
        return "unexpected_result", 0, "-", True, "-"

    raw = result.get("raw")
    invalid_tool_calls = getattr(raw, "invalid_tool_calls", None) or []
    response_metadata = getattr(raw, "response_metadata", None) or {}
    finish_reason = "-"
    if isinstance(response_metadata, Mapping):
        finish_reason = str(
            response_metadata.get("finish_reason")
            or response_metadata.get("stop_reason")
            or "-"
        )

    content_empty = not bool(getattr(raw, "content", None))
    parsing_error = result.get("parsing_error")
    parsing_error_type = type(parsing_error).__name__ if parsing_error else "-"

    if invalid_tool_calls:
        reason = "invalid_tool_calls"
    elif parsing_error is not None:
        reason = "parsing_error"
    elif result.get("parsed") is None:
        reason = "missing_parsed_output"
    else:
        reason = "unexpected_parsed_type"

    return (
        reason,
        len(invalid_tool_calls),
        finish_reason,
        content_empty,
        parsing_error_type,
    )


def _log_parse_failure(
    *,
    node: str,
    schema: type[object],
    attempt: int,
    max_attempts: int,
    reason: str,
    invalid_tool_calls: int,
    finish_reason: str,
    content_empty: bool,
    parsing_error_type: str,
) -> None:
    retrying = attempt < max_attempts
    log = logger.warning if retrying else logger.error
    log(
        "Structured output parsing failed node=%s schema=%s attempt=%d/%d "
        "reason=%s invalid_tool_calls=%d finish_reason=%s content_empty=%s "
        "parsing_error_type=%s retrying=%s",
        node,
        schema.__name__,
        attempt,
        max_attempts,
        reason,
        invalid_tool_calls,
        finish_reason,
        content_empty,
        parsing_error_type,
        retrying,
    )


async def ainvoke_structured_with_retry[StructuredT](
    chain: Any,
    inputs: Mapping[str, Any],
    *,
    schema: type[StructuredT],
    node: str,
    max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
    retry_delay_seconds: float = _DEFAULT_RETRY_DELAY_SECONDS,
) -> StructuredT:
    """调用 ``include_raw=True`` 的结构化链，解析失败时重新请求模型。

    DeepSeek 可能返回 ``finish_reason=tool_calls``，但工具参数不是合法 JSON。
    LangChain 会把这种结果放入 ``invalid_tool_calls`` 并令 ``parsed=None``，
    因此这里同时检查解析异常、非法工具调用和空解析结果。
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    if retry_delay_seconds < 0:
        raise ValueError("retry_delay_seconds must be non-negative")

    last_exception: BaseException | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            result = await chain.ainvoke(dict(inputs))
        except _PARSING_EXCEPTIONS as exc:
            last_exception = exc
            _log_parse_failure(
                node=node,
                schema=schema,
                attempt=attempt,
                max_attempts=max_attempts,
                reason="parser_exception",
                invalid_tool_calls=0,
                finish_reason="-",
                content_empty=True,
                parsing_error_type=type(exc).__name__,
            )
        else:
            parsed = result.get("parsed") if isinstance(result, Mapping) else None
            if isinstance(parsed, schema):
                return parsed

            (
                reason,
                invalid_tool_calls,
                finish_reason,
                content_empty,
                parsing_error_type,
            ) = _raw_diagnostics(result)
            _log_parse_failure(
                node=node,
                schema=schema,
                attempt=attempt,
                max_attempts=max_attempts,
                reason=reason,
                invalid_tool_calls=invalid_tool_calls,
                finish_reason=finish_reason,
                content_empty=content_empty,
                parsing_error_type=parsing_error_type,
            )

        if attempt < max_attempts and retry_delay_seconds:
            await asyncio.sleep(retry_delay_seconds * attempt)

    error = StructuredOutputError(
        f"{node} failed to parse {schema.__name__} after {max_attempts} attempts"
    )
    if last_exception is not None:
        raise error from last_exception
    raise error


__all__ = ["StructuredOutputError", "ainvoke_structured_with_retry"]
