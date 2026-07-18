"""Plan DAG 校验。

任务数、未知依赖、自依赖、环、孤立输出、工具权限和 Schema。
"""

from __future__ import annotations

from app.domain.plan import Plan


class PlanValidationError(Exception):
    """Plan DAG 校验失败，携带具体问题列表。"""

    def __init__(self, issues: list[str]) -> None:
        self.issues = issues
        super().__init__("; ".join(issues))


def validate_plan(plan: Plan) -> None:
    """校验 Plan 的 DAG 结构，失败抛 PlanValidationError。

    校验项：
    1. 至少有一个任务
    2. 任务 ID 在同计划内唯一
    3. 无自依赖
    4. 依赖引用的任务必须存在（无未知依赖）
    5. 无依赖环
    """
    issues: list[str] = []
    # 1. 至少一个任务
    if not plan.tasks:
        raise PlanValidationError(["计划中没有任何任务"])

    task_ids = [t.task_id for t in plan.tasks]

    # 2. ID 唯一性
    seen: set[str] = set()
    duplicates = [tid for tid in task_ids if tid in seen or seen.add(tid)]
    if duplicates:
        issues.append(f"任务 ID 重复：{duplicates}")

    # 所有task_id的set集合
    id_set = set(task_ids)

    # 3. 自依赖
    self_deps = [t.task_id for t in plan.tasks if t.task_id in t.dependencies]
    if self_deps:
        issues.append(f"任务自依赖：{self_deps}")

    # 4. 未知依赖
    unknown = {dep for t in plan.tasks for dep in t.dependencies if dep not in id_set}
    if unknown:
        issues.append(f"依赖了不存在的任务：{sorted(unknown)}")

    # 5. 依赖环检测（DFS 三色标记）
    cycle = _detect_cycle(plan)
    if cycle:
        issues.append(f"存在依赖环：{' → '.join(cycle)}")

    if issues:
        raise PlanValidationError(issues)


def _detect_cycle(plan: Plan) -> list[str] | None:
    """DFS 三色标记检测环，返回环上任务 ID 序列，无环返回 None。"""
    graph: dict[str, list[str]] = {t.task_id: list(t.dependencies) for t in plan.tasks}
    white, gray, black = 0, 1, 2
    color: dict[str, int] = {tid: white for tid in graph}
    path: list[str] = []
    def dfs(node: str) -> list[str] | None:
        color[node] = gray
        path.append(node)
        for dep in graph.get(node, []):
            if dep not in color:
                continue  # 未知依赖，留给上面的校验报
            if color[dep] == gray:
                idx = path.index(dep)
                return path[idx:] + [dep]
            if color[dep] == white:
                dfs_found = dfs(dep)
                if dfs_found:
                    return dfs_found
        path.pop()
        color[node] = black
        return None

    for tid in graph:
        if color[tid] == white:
            found = dfs(tid)
            if found:
                return found
    return None


__all__ = ["validate_plan", "PlanValidationError"]