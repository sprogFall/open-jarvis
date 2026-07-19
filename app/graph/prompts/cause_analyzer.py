"""Cause Analyzer 的 Prompt 与结构化输出 schema。

规则先收集证据（错误码、状态、预算），LLM 处理语义歧义。
"""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.domain.diagnosis import FaultDomain

PROMPT_VERSION = "v1"

CAUSE_ANALYZER_SYSTEM = """\
你是一个故障诊断专家。系统已经收集了初步证据，请你判断故障的根因并建议恢复动作。

故障域定义：
- planning：任务缺失、依赖错误、验收标准与目标不一致
- allocation：工具/模型能力不匹配、上下文不足
- execution_transient：429、网络错误、工具暂时不可用
- execution_permanent：参数非法、权限不足、工具不支持
- data：必需输入不存在或来源冲突
- review：汇总遗漏、格式不合格但原始结果正确

建议恢复动作：
- replan：重规划（保留成功任务、修订失败任务）
- reallocate：重分配（调整模型、工具、重试策略）
- reaggregate：重新汇总（不重跑任务）
- finalize：终止并输出当前结果

只输出结构化结果，不要多余解释。"""

CAUSE_ANALYZER_USER = """\
【用户目标】
{objective}

【计划任务数】
{task_count}

【规则证据（确定性结论）】
{rule_evidence}

【任务执行摘要】
{task_summary}

【审核结果】
{review_summary}

【预算状态】
{budget_status}

请诊断故障原因并建议恢复动作。"""

cause_analyzer_prompt = ChatPromptTemplate.from_messages(
    [("system", CAUSE_ANALYZER_SYSTEM), ("user", CAUSE_ANALYZER_USER)]
)


class CauseAnalyzerDraft(BaseModel):
    """LLM 直接填充的诊断草稿。fault_domain 由 LLM 建议，代码做合法性校验。"""

    fault_domain: FaultDomain = Field(description="故障归属域")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="置信度")
    additional_evidence: list[str] = Field(default_factory=list, description="LLM 发现的新证据")
    suggested_action: str = Field(
        default="finalize",
        description="建议动作：replan / reallocate / reaggregate / finalize",
    )
    rationale: str = Field(default="", description="诊断理由，简短可审计")


__all__ = ["cause_analyzer_prompt", "CauseAnalyzerDraft", "PROMPT_VERSION"]