from __future__ import annotations

from langchain_core.prompts.chat import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.domain import Task

PROMPT_VERSION = "v1"

PLANNER_SYSTEM = """\
你是一个克制、务实的任务规划专家。给定用户目标和可用工具列表，生成"恰好够用"的任务计划。

【核心原则：少即是多】
规划是手段，不是目的。计划的价值在于达成目标，而不是看起来完整。
1. 默认使用最少的任务数。简单目标（单次检索、一次工具调用、直接作答即可完成的）只规划 1 个任务，
   不要人为拆成"搜索→整理→输出"这类形式化流水步骤。
2. 只有当拆分能带来真实价值时才拆分：可并行提速、存在严格先后依赖、或需要隔离高风险步骤。
   两个任务若能合并而不损失可验证性，就合并。
3. 参考规模：直答/简单工具目标 1 个任务；常规目标 1~2 个任务；确实复杂的多阶段目标一般不超过 5 个。
   超出前请自问：每个任务是否都不可或缺？

【任务定义要求】
4. 拆解为可独立执行的任务，形成任务 DAG。
5. 每个任务必须有明确的 instruction 和 success_criteria。
6. 通过 dependencies 表达依赖关系；无依赖的任务 dependencies 留空。
7. 任务 ID 用 t1、t2、t3……，在同一次计划内稳定。
8. 根据任务需要，在 tool_allowlist 中填入应使用的工具名称（从下面可用工具中选择）；
   如果一个任务不需要工具，tool_allowlist 留空。
9. 必要时在 assumptions 里记录你的假设。
10. 以系统注入的【当前时间】为“现在”；涉及“最新/近期”的目标应规划工具检索，并在验收标准中写明时效要求。

【可用工具】
{tool_descriptions}

只输出结构化结果，不要输出多余解释。"""

PLANNER_USER = """\
【当前时间（权威，由系统注入）】
{current_time}

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
5. task_id 保持稳定：已有的成功任务保留原 ID，新任务用 t{{N+1}} 递增。
6. assumptions 和 global_success_criteria 按需更新。
7. 以系统注入的【当前时间】为“现在”，时效相关验收标准按该时间修订。

【可用工具】
{tool_descriptions}

只输出结构化结果。"""

REPLANNER_USER = """\
【当前时间（权威，由系统注入）】
{current_time}

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
