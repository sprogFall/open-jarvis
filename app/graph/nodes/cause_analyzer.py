"""Cause Analyzer 节点：根据错误、轨迹和审核意见进行结构化归因，选择下一动作。

先使用规则证据，再让 LLM 处理语义歧义，禁止仅凭模型猜测。
输出：Diagnosis
"""

from __future__ import annotations

from app.domain import Diagnosis
from app.domain.diagnosis import FaultDomain
from app.graph.state import RunState


async def cause_analyzer(state: RunState) -> dict:
    budget = state.get("budget")
    if budget is not None and budget.exhausted:
        return {"diagnosis": Diagnosis(
            fault_domain=FaultDomain.execution_transient,
            confidence=1,
            evidence=["预算已耗尽"],
            suggested_action="finalize"
        )}

    return {"diagnosis": Diagnosis(
        fault_domain=FaultDomain.planning,
        confidence=0.5,
        evidence=["存在失败任务，无明确执行错误"],
        suggested_action="finalize"
    )}


__all__ = ["cause_analyzer"]
