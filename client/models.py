from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(slots=True)
class TaskAction:
    name: str
    command: str
    args: dict = field(default_factory=dict)
    requires_approval: bool = False
    reason: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict) -> "TaskAction":
        return cls(**payload)

