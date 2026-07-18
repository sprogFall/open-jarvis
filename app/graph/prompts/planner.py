from __future__ import annotations

from langchain_core.prompts.chat import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.domain import Task

PROMPT_VERSION = "v1"

PLANNER_SYSTEM = """\
你是一个严谨的任务规划专家。给定用户目标，你需要：
1. 拆解为可独立执行的任务，形成任务 DAG。
2. 每个任务必须有明确的 instruction 和 success_criteria。
3. 通过 dependencies 表达依赖关系；无依赖的任务 dependencies 留空。
4. 任务 ID 用 t1、t2、t3……，在同一次计划内稳定。
5. tool_allowlist 暂时留空（当前阶段未接入工具）。
6. 必要时在 assumptions 里记录你的假设。
只输出结构化结果，不要输出多余解释。"""

PLANNER_USER = """\
用户目标：
{user_request}

请生成任务计划。"""

planner_prompt = ChatPromptTemplate.from_messages(
    [("system", PLANNER_SYSTEM), ("user", PLANNER_USER)]
)

class PlannerDraft(BaseModel):
    """LLM 直接填充的计划草稿，不含 plan_id / version。"""

    objective: str = Field(description="计划总体目标")
    assumptions: list[str] = Field(default_factory=list, description="前提假设")
    global_success_criteria: list[str] = Field(
        default_factory=list, description="全局成功标准"
    )
    tasks: list[Task] = Field(description="任务 DAG，task_id 用 t1/t2/...")

__all__ = ["planner_prompt", "PlannerDraft", "PROMPT_VERSION"]