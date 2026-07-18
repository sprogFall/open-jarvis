"""Executor 的 Prompt。

当前阶段 Executor 只做单轮 LLM 调用（无工具），
后续替换为 create_react_agent 子图 + 真实工具。
"""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

PROMPT_VERSION = "v1"

EXECUTOR_SYSTEM = """\
你是一个任务执行者。请严格根据任务指令完成工作，输出最终结果。
要求：
- 直接给出可交付的答案，不要复述任务。
- 若信息不足，给出你能做的最佳回答并说明假设。
- 保持简洁、准确、可追溯。"""

EXECUTOR_USER = """\
【计划目标】
{objective}

【任务标题】
{task_title}

【任务指令】
{instruction}

【成功标准】
{success_criteria}

请完成该任务。"""

executor_prompt = ChatPromptTemplate.from_messages(
    [("system", EXECUTOR_SYSTEM), ("user", EXECUTOR_USER)]
)

__all__ = ["executor_prompt", "PROMPT_VERSION"]