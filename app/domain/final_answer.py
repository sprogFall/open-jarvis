"""最终答案模型。"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class RunStatus(StrEnum):
    success = "success"
    partial = "partial"
    failed = "failed"
    cancelled = "cancelled"


class FinalAnswer(BaseModel):
    """Finalizer 产出的用户可见最终响应。"""

    content: str = Field(description="最终返回给用户的文本内容")
    status: RunStatus = Field(default=RunStatus.success, description="最终运行状态：success（成功）、partial（部分完成）、failed（失败）、cancelled（已取消）")
    artifact_refs: list[str] = Field(default_factory=list, description="最终结果关联的产物引用列表")
    warnings: list[str] = Field(default_factory=list, description="返回给用户的警告信息列表")


__all__ = ["FinalAnswer", "RunStatus"]