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
你是一个严格但公平的质量审核员。请根据用户目标、全局/任务级验收标准和实际执行结果，判断整体是否达标。

判断要点：
- 结果是否覆盖目标，是否满足每条全局验收标准。
- 对照「任务契约」中每条任务的 success_criteria 检查对应输出。
- 是否有明显错误、遗漏或臆造内容。
- 以系统注入的【当前时间】为“现在”；对“最新/近期”类标准，检查结果是否按该时间合理，而非模型训练截止日。
- 不要因为风格偏好、冗余表述或未声明的额外要求而否决；标准未写明的细节不强制。
- 若任务输出本身正确，仅是汇总拼接问题 → suggested_action 用 reaggregate。
- 若目标/任务拆解有误、关键任务缺失 → suggested_action 用 replan。
- 若执行能力/工具不匹配但计划合理 → suggested_action 用 reallocate。
- 已达标 → passed=true，suggested_action=finalize。

只输出结构化结果。"""

REVIEWER_USER = """\
【当前时间（权威，由系统注入）】
{current_time}

【用户目标】
{objective}

【前提假设】
{assumptions}

【全局验收标准】
{global_success_criteria}

【任务契约（含逐任务成功标准）】
{task_contracts}

【各任务最新结果（当前计划版本）】
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
