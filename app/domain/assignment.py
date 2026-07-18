"""执行分配模型。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Assignment(BaseModel):
    """Scheduler 为就绪任务生成的执行分配。
    """

    task_id: str = Field(description="被分配的目标任务 ID")
    executor_profile: str = Field(default="default", description="执行器配置名称，决定运行时环境与资源")
    model_tier: str = Field(default="standard", description="模型层级：fast（快速）、standard（标准）、reasoning（推理）")
    tool_allowlist: list[str] = Field(default_factory=list, description="本次执行允许调用的工具白名单")
    resolved_input_refs: dict[str, str] = Field(default_factory=dict, description="已解析的输入引用映射，key 为参数名，value 为已解析的值")
    timeout_seconds: int | None = Field(default=None, description="任务执行超时时间（秒），None 表示不限时")
    attempt: int = Field(default=1, description="当前重试次数，从 1 开始计数")


__all__ = ["Assignment"]
