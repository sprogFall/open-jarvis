from __future__ import annotations

import re


class LogRedactor:
    def __init__(self) -> None:
        self._patterns = [
            re.compile(r"(password=)[^\s]+", re.IGNORECASE),
            re.compile(r"(token=)[^\s]+", re.IGNORECASE),
            re.compile(r"(Authorization:\s+Bearer\s+)[^\s]+", re.IGNORECASE),
        ]

    def redact(self, text: str) -> str:
        sanitized = text
        for pattern in self._patterns:
            sanitized = pattern.sub(r"\1***", sanitized)
        return sanitized

