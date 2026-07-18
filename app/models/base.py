"""模型档位基类与工厂。"""

from __future__ import annotations

from enum import StrEnum


class ModelTier(StrEnum):
    fast = "fast"
    standard = "standard"
    reasoning = "reasoning"


__all__ = ["ModelTier"]
