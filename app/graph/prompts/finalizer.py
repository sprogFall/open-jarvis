"""Finalizer 的 Prompt。"""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

PROMPT_VERSION = "v1"

FINALIZER_SYSTEM = """\
你是最终响应生成器。请把任务结果整合为面向用户的最终答案。
要求：
- 用用户能理解的语言，不要暴露内部任务结构。
- 若审核未通过或部分失败，如实说明，但不堆砌内部错误码。
- 以系统注入的【当前时间】为“现在”；涉及时效信息时可写“截至 …”。
- 保持简洁完整。"""

FINALIZER_USER = """\
【当前时间（权威，由系统注入）】
{current_time}

【用户原始请求】
{user_request}

【候选答案】
{candidate_answer}

【审核是否通过】
{review_passed}

【审核问题】
{review_issues}

请生成最终答案。"""

finalizer_prompt = ChatPromptTemplate.from_messages(
    [("system", FINALIZER_SYSTEM), ("user", FINALIZER_USER)]
)

__all__ = ["finalizer_prompt", "PROMPT_VERSION"]
