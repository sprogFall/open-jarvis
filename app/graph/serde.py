"""Checkpoint 序列化配置：自定义类型白名单。

LangGraph 的 JsonPlusSerializer 默认只允许内置类型反序列化，项目中的 Pydantic
domain 模型（Plan/Task/ReviewResult/...）需注册到 allowed_msgpack_modules 才能
在 Checkpoint 中正确 round-trip。MemorySaver 与 AsyncPostgresSaver 共用此配置。
"""

from __future__ import annotations

from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

# 注册所有可能在 checkpoint 中序列化的自定义类型到 msgpack 白名单
ALLOWED_MSGPACK_TYPES: list[tuple[str, ...]] = [
    ("app.domain.plan", "Plan"),
    ("app.domain.plan", "Task"),
    ("app.domain.task", "TaskStatus"),
    ("app.domain.task", "TaskResult"),
    ("app.domain.aggregate", "AggregateResult"),
    ("app.domain.review", "ReviewResult"),
    ("app.domain.budget", "RunBudget"),
    ("app.domain.final_answer", "RunStatus"),
    ("app.domain.final_answer", "FinalAnswer"),
    ("app.domain.assignment", "Assignment"),
    ("app.domain.diagnosis", "Diagnosis"),
    ("app.domain.diagnosis", "FaultDomain"),
]


def make_serde() -> JsonPlusSerializer:
    """构造带自定义类型白名单的序列化器。"""
    return JsonPlusSerializer(allowed_msgpack_modules=ALLOWED_MSGPACK_TYPES)


__all__ = ["ALLOWED_MSGPACK_TYPES", "make_serde"]
