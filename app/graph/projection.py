"""当前计划版本的任务结果投影。

task_events 是 append-only 事件流，跨 replan 会残留旧版本结果。
调度、汇总、审核、归因统一通过本模块只读「当前 plan_version」下每任务最新事件，
避免历史 failed/completed 污染新一轮执行。
"""

from __future__ import annotations

from typing import Any

from app.domain import Plan, Task, TaskResult, TaskStatus
from app.graph.state import RunState

# Reviewer / 诊断展示用的单任务输出上限（完整候选答案由 Aggregator 另行提供）
_RESULT_PREVIEW_CHARS = 2000


def resolve_plan_version(state: RunState) -> int:
    """解析当前应投影的计划版本。"""
    plan = state.get("plan")
    if plan is not None and getattr(plan, "version", None):
        return int(plan.version)
    return int(state.get("plan_version") or 1)


def latest_task_results(
    state: RunState,
    *,
    plan_version: int | None = None,
) -> dict[str, TaskResult]:
    """返回当前计划版本下每个 task_id 的最新 TaskResult。

    事件按追加顺序扫描，后写覆盖先写。plan_version 不匹配的历史事件被忽略。
    """
    version = resolve_plan_version(state) if plan_version is None else plan_version
    latest: dict[str, TaskResult] = {}
    for event in state.get("task_events", []):
        event_version = getattr(event, "plan_version", None)
        if event_version is None:
            event_version = 1
        if int(event_version) != int(version):
            continue
        latest[event.task_id] = event
    return latest


def task_status_map(
    state: RunState,
    *,
    plan_version: int | None = None,
) -> dict[str, TaskStatus]:
    """当前计划版本下每任务最新状态。"""
    return {
        task_id: result.status
        for task_id, result in latest_task_results(state, plan_version=plan_version).items()
    }


def format_task_contracts(plan: Plan | None) -> str:
    """把计划内任务契约格式化为 LLM 可读文本（给 Reviewer / 诊断用）。"""
    if plan is None or not plan.tasks:
        return "（无任务契约）"
    blocks: list[str] = []
    for task in plan.tasks:
        criteria = "\n".join(f"  - {c}" for c in task.success_criteria) or "  - （无显式标准）"
        deps = ", ".join(task.dependencies) if task.dependencies else "无"
        blocks.append(
            f"### [{task.task_id}] {task.title}\n"
            f"指令：{task.instruction}\n"
            f"依赖：{deps}\n"
            f"成功标准：\n{criteria}"
        )
    return "\n\n".join(blocks)


def format_latest_task_results(
    state: RunState,
    *,
    plan_version: int | None = None,
    preview_chars: int = _RESULT_PREVIEW_CHARS,
) -> str:
    """当前计划版本的任务结果紧凑 JSON 文本。"""
    import json

    latest = latest_task_results(state, plan_version=plan_version)
    plan = state.get("plan")
    task_ids = [t.task_id for t in plan.tasks] if plan else list(latest.keys())
    # 保证计划内任务顺序，并包含尚无事件的任务占位
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for task_id in task_ids:
        seen.add(task_id)
        result = latest.get(task_id)
        if result is None:
            rows.append({"task_id": task_id, "status": "pending", "answer": "", "error": None})
            continue
        answer = ""
        if result.output and "answer" in result.output:
            answer = str(result.output["answer"])
            if len(answer) > preview_chars:
                answer = answer[:preview_chars] + "…[已截断]"
        rows.append({
            "task_id": result.task_id,
            "status": result.status.value,
            "attempt": result.attempt,
            "answer": answer,
            "error": result.error_message,
            "tools_used": result.tools_used,
        })
    for task_id, result in latest.items():
        if task_id in seen:
            continue
        answer = ""
        if result.output and "answer" in result.output:
            answer = str(result.output["answer"])[:preview_chars]
        rows.append({
            "task_id": result.task_id,
            "status": result.status.value,
            "attempt": result.attempt,
            "answer": answer,
            "error": result.error_message,
            "tools_used": result.tools_used,
        })
    if not rows:
        return "（无任务结果）"
    return json.dumps(rows, ensure_ascii=False, indent=2)


def format_structured_candidate(
    plan: Plan | None,
    latest_outputs: dict[str, dict[str, Any]],
) -> str:
    """按任务契约顺序生成带标题的候选答案，便于 Reviewer 逐项对照。"""
    if plan is None:
        parts = []
        for task_id, output in latest_outputs.items():
            answer = output.get("answer", output)
            parts.append(f"## [{task_id}]\n{answer}")
        return "\n\n".join(parts) if parts else "(无任务输出)"

    parts: list[str] = []
    for task in plan.tasks:
        output = latest_outputs.get(task.task_id)
        if output is None:
            continue
        answer = output.get("answer", output)
        criteria = "；".join(task.success_criteria) if task.success_criteria else "（无显式标准）"
        parts.append(
            f"## [{task.task_id}] {task.title}\n"
            f"验收标准：{criteria}\n"
            f"输出：\n{answer}"
        )
    return "\n\n".join(parts) if parts else "(无任务输出)"


def task_lookup(plan: Plan | None, task_id: str) -> Task | None:
    if plan is None:
        return None
    return next((t for t in plan.tasks if t.task_id == task_id), None)


__all__ = [
    "resolve_plan_version",
    "latest_task_results",
    "task_status_map",
    "format_task_contracts",
    "format_latest_task_results",
    "format_structured_candidate",
    "task_lookup",
]
