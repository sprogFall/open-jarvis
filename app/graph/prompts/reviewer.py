"""Reviewer 的 Prompt 与结构化输出 schema。

审核采用"规则预检 + LLM 语义审核"两段式：
- 规则预检：有任务 failed/cancelled → 直接判失败，不调 LLM。
- LLM 审核：全部 completed 时，让 LLM 按验收标准做语义判断。
"""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

PROMPT_VERSION = "v1"

REVIEWER_SYSTEM = """\
你是一个严格的质量审核员。请根据用户目标、验收标准和任务结果，判断整体是否达标。
判断要点：
- 结果是否覆盖目标。
- 是否满足每条验收标准。
- 是否有明显错误、遗漏或臆造内容。
只输出结构化结果。"""

REVIEWER_USER = """\
【用户目标】
{objective}

【全局验收标准】
{global_success_criteria}

【各任务结果】
{task_results}

【候选答案】
{candidate_answer}

请审核。"""

reviewer_prompt = ChatPromptTemplate.from_messages(
    [("system", REVIEWER_SYSTEM), ("user", REVIEWER_USER)]
)


class ReviewerDraft(BaseModel):
    """LLM 直接填充的审核草稿。failed_task_ids 由代码规则补全。"""

    passed: bool = Field(description="是否通过审核")
    score: float = Field(ge=0.0, le=1.0, description="审核评分 0.0~1.0")
    issues: list[str] = Field(default_factory=list, description="发现的问题")
    rationale: str = Field(default="", description="审核理由，简短可审计")
    suggested_action: str = Field(
        default="finalize",
        description="建议动作：finalize / replan / reallocate / reaggregate",
    )


__all__ = ["reviewer_prompt", "ReviewerDraft", "PROMPT_VERSION"]