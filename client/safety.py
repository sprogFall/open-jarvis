from __future__ import annotations

import re


class UnsafeCommandError(ValueError):
    """Raised when a command violates the local safety policy."""


class CommandSafetyFilter:
    def __init__(self) -> None:
        self._blocked_patterns = [
            re.compile(r"(^|\s)rm\s+-rf\s+/($|\s)"),
            re.compile(r":\(\)\s*\{\s*:\|:&\s*;\s*\};:"),
            re.compile(r"(^|\s)mkfs(\.|$|\s)"),
            re.compile(r"dd\s+if=.*\s+of=/dev/"),
        ]

    def ensure_safe(self, command: str) -> str:
        for pattern in self._blocked_patterns:
            if pattern.search(command):
                raise UnsafeCommandError(f"Blocked unsafe command: {command}")
        return command

