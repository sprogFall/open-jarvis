"""结构化日志配置。

使用 structlog 输出统一关联字段。密钥不进入日志。
"""

from __future__ import annotations

import logging
import re
import sys
from typing import cast

import structlog


class _SensitiveDataFilter(logging.Filter):
    """对第三方 SDK 日志中常见的凭据字段做兜底脱敏。"""

    _PATTERNS = (
        re.compile(
            r"(?i)((?:authorization|api[_-]?key|x-api-key|set-cookie)"
            r"['\"]?\s*[:=]\s*)(?:['\"][^'\"]*['\"]|[^,\s}\]]+)"
        ),
        re.compile(r"(?i)([?&](?:api_key|key|token)=)([^&\s]+)"),
        re.compile(r"(?i)(https?://)([^/@\s:]+):([^/@\s]+)@"),
    )

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for index, pattern in enumerate(self._PATTERNS):
            replacement = r"\1***:***@" if index == 2 else r"\1***"
            message = pattern.sub(replacement, message)
        record.msg = message
        record.args = ()
        return True


def configure_logging(level: str = "INFO", llm_sdk_level: str = "DEBUG") -> None:
    app_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=app_level,
    )
    logging.getLogger().setLevel(app_level)

    # OpenAI SDK 的 INFO 只有“准备重试”，DEBUG 才包含触发重试的异常或 HTTP 状态。
    openai_logger = logging.getLogger("openai")
    openai_logger.setLevel(getattr(logging, llm_sdk_level.upper(), logging.DEBUG))
    sensitive_filter = _SensitiveDataFilter()
    if not any(isinstance(item, _SensitiveDataFilter) for item in openai_logger.filters):
        openai_logger.addFilter(sensitive_filter)
    # Logger filter 不会自动过滤子 logger 的传播记录，因此根 handler 也要挂载。
    for handler in logging.getLogger().handlers:
        if not any(isinstance(item, _SensitiveDataFilter) for item in handler.filters):
            handler.addFilter(sensitive_filter)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(app_level),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return cast(structlog.stdlib.BoundLogger, structlog.get_logger(name))


__all__ = ["configure_logging", "get_logger"]
