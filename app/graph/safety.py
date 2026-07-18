"""输入安全：用户输入、工具返回均视为不可信数据，防止 Prompt 注入。

ChatPromptTemplate 已把 system / user 分离，这是第一道防线；
本模块做第二道防线：截断 + 注入标记中和。
"""

from __future__ import annotations

import re

# 截断上限，防止上下文爆炸与成本失控
_MAX_INPUT_LENGTH = 8000

# 潜在 Prompt 注入模式：角色覆盖、指令劫持
_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"<\s*/?\s*system\s*>", re.IGNORECASE),
    re.compile(r"<\s*/?\s*im_(start|end)\s*>", re.IGNORECASE),
    re.compile(r"##\s*system\s*instruction", re.IGNORECASE),
    re.compile(r"ignore\s+(?:all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"你(?:现在)?(?:是|扮演)(?:一个)?(?:新|不同|管理员|开发者)", re.IGNORECASE),
]


def sanitize_user_input(text: str) -> str:
    """对用户输入做最小化脱敏：截断 + 注入标记中和。

    不删除语义内容，只中和可能的角色覆盖标记，保留可审计痕迹。
    """
    if not text:
        return ""
    truncated = text[:_MAX_INPUT_LENGTH]
    if len(text) > _MAX_INPUT_LENGTH:
        truncated += "…[已截断]"
    for pattern in _INJECTION_PATTERNS:
        truncated = pattern.sub("[已中和]", truncated)
    return truncated


__all__ = ["sanitize_user_input"]