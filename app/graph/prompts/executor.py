"""Executor 的 Prompt。

当前阶段 Executor 只做单轮 LLM 调用（无工具），
后续替换为 create_react_agent 子图 + 真实工具。
"""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

PROMPT_VERSION = "v1"

EXECUTOR_SYSTEM = """\
你是一个任务执行者。你可以使用提供的工具来完成工作。
要求：
- 先思考再行动：理解任务后，决定是否使用工具。
- 工具返回的结果可能被截断，根据已有信息做出最佳判断。
- 若工具不可用或信息不足，给出你能做的最佳回答并说明假设。
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