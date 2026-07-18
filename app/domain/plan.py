"""计划模型。

对应架构设计第 5.1 节。任务 ID 在同一计划版本内稳定；重规划时记录旧、新任务映射；
仅当输入和验收条件仍兼容时复用已成功结果。
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Task(BaseModel):
    """单个任务契约。"""

    task_id: str = Field(description="任务唯一标识符，在同一计划版本内稳定不变")
    title: str = Field(description="任务标题，用于人类可读的简要描述")
    instruction: str = Field(description="任务执行指令，指导 Executor 如何完成该任务")
    dependencies: list[str] = Field(default_factory=list, description="依赖的前置任务 ID 列表，需等待这些任务完成后才能执行")
    required_capabilities: list[str] = Field(default_factory=list, description="执行此任务所需的能力列表")
    tool_allowlist: list[str] = Field(default_factory=list, description="允许使用的工具白名单，空列表表示不限制")
    input_refs: list[str] = Field(default_factory=list, description="输入数据引用列表，指向其他任务的输出或外部数据")
    output_schema: dict | None = Field(default=None, description="期望的输出数据结构 Schema，None 表示不限制输出格式")
    success_criteria: list[str] = Field(default_factory=list, description="任务成功的判定标准列表")
    timeout_seconds: int | None = Field(default=None, description="任务超时时间（秒），None 表示不限时")
    max_attempts: int = Field(default=2, description="最大重试次数")


class Plan(BaseModel):
    """任务 DAG 计划。"""

    plan_id: str = Field(description="计划唯一标识符")
    version: int = Field(default=1, description="计划版本号，每次重规划自增")
    objective: str = Field(description="计划的总体目标和要解决的问题描述")
    assumptions: list[str] = Field(default_factory=list, description="计划制定时的前提假设列表")
    global_success_criteria: list[str] = Field(default_factory=list, description="计划级别的全局成功判定标准")
    tasks: list[Task] = Field(default_factory=list, description="计划包含的任务 DAG 节点列表")


__all__ = ["Plan", "Task"]
