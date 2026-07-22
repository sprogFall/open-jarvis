"""领域模型：Plan、Task、Review、Experience 等结构化数据契约。

使用 Pydantic v2 定义边界模型，TypedDict + Annotated reducer 定义 LangGraph 状态。
"""
from app.domain.aggregate import AggregateResult
from app.domain.assignment import Assignment
from app.domain.budget import RunBudget
from app.domain.diagnosis import Diagnosis
from app.domain.experience import Experience
from app.domain.final_answer import FinalAnswer, RunStatus
from app.domain.plan import Plan, Task
from app.domain.review import ReviewResult
from app.domain.run_context import RunContext
from app.domain.task import TaskResult, TaskStatus

__all__ = [
    "Assignment",
    "Diagnosis",
    "Experience",
    "Plan",
    "ReviewResult",
    "RunBudget",
    "RunContext",
    "Task",
    "TaskResult",
    "TaskStatus",
    "AggregateResult",
    "RunStatus",
    "FinalAnswer",
]

