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


# ─── 重规划 Prompt─────────────────────────────────────

REPLANNER_SYSTEM = """\
你是一个任务计划修正专家。系统诊断出了当前计划的问题，请你根据诊断信息和已完成的任务结果，生成修正后的计划。

要求：
1. 保留所有成功完成的任务不动（复用它们的 task_id 和 instruction）。
2. 对失败或被诊断出问题的任务：修订 instruction、success_criteria、dependencies 或重新规划。
3. 如果诊断指出是工具/执行器问题，相应调整 required_capabilities 和 tool_allowlist。
4. 如果诊断指出是规划问题，可能需要新增任务、拆分任务或调整依赖关系。
5. task_id 保持稳定：已有的成功任务保留原 ID，新任务用 t{N+1} 递增。
6. assumptions 和 global_success_criteria 按需更新。
只输出结构化结果。"""

REPLANNER_USER = """\
【用户目标】
{objective}

【当前计划版本】
{plan_version}

【诊断结论】
{fault_domain}

【诊断证据】
{diagnosis_evidence}

【建议动作】
{suggested_action}

【任务执行摘要】
{task_summary}

【当前计划结构】
{current_plan_json}

请生成修正后的计划。"""

replanner_prompt = ChatPromptTemplate.from_messages(
    [("system", REPLANNER_SYSTEM), ("user", REPLANNER_USER)]
)


class ReplannerDraft(BaseModel):
    """重规划的 LLM 草稿。"""

    objective: str = Field(description="计划总体目标（通常不变）")
    assumptions: list[str] = Field(default_factory=list, description="更新后的假设")
    global_success_criteria: list[str] = Field(
        default_factory=list, description="更新后的成功标准"
    )
    tasks: list[Task] = Field(description="修正后的任务列表")
    changes_summary: str = Field(default="", description="本次修改摘要，可审计")


__all__ = ["planner_prompt", "PlannerDraft",
           "replanner_prompt", "ReplannerDraft",
           "PROMPT_VERSION"
           ]
