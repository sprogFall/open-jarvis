from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any

from typing_extensions import TypedDict

from client.models import TaskAction
from client.storage import (
    SQLStorageBackend,
    StorageTarget,
    is_postgres_target,
    normalize_storage_target,
    resolve_sqlite_path,
)

try:  # pragma: no cover - exercised only when LangGraph is installed
    from langgraph.graph import END, START, StateGraph
    from langgraph.types import Command, interrupt
except Exception:  # pragma: no cover - fallback path is covered in tests
    StateGraph = None
    END = None
    START = None
    Command = None
    interrupt = None

try:  # pragma: no cover - optional runtime dependency
    from langgraph.checkpoint.sqlite import SqliteSaver
except Exception:  # pragma: no cover - fallback path is covered in tests
    SqliteSaver = None

try:  # pragma: no cover - optional runtime dependency
    from langgraph.checkpoint.postgres import PostgresSaver
except Exception:  # pragma: no cover - fallback path is covered in tests
    PostgresSaver = None


LANGGRAPH_AVAILABLE = all(
    dependency is not None
    for dependency in (StateGraph, END, START, Command, interrupt)
)


class WorkflowState(TypedDict, total=False):
    task_id: str
    instruction: str
    actions: list[dict[str, Any]]
    next_action_index: int
    logs: list[str]
    last_result: str | None
    approved: bool | None
    outcome: str | None


@dataclass(slots=True)
class WorkflowExecutionResult:
    state: WorkflowState
    interrupt_id: str | None = None
    interrupt_value: dict[str, Any] | None = None

    @property
    def logs(self) -> list[str]:
        return list(self.state.get("logs", []))

    @property
    def last_result(self) -> str:
        return self.state.get("last_result") or ""

    @property
    def outcome(self) -> str | None:
        return self.state.get("outcome")

    @property
    def is_interrupted(self) -> bool:
        return self.interrupt_id is not None


class LangGraphTaskWorkflow:
    def __init__(
        self,
        *,
        planner,
        registry,
        redactor,
        safety_filter,
        database_path: StorageTarget,
    ) -> None:
        self.planner = planner
        self.registry = registry
        self.redactor = redactor
        self.safety_filter = safety_filter
        self.database_path = normalize_storage_target(database_path)
        self._native_connection: sqlite3.Connection | None = None
        self._checkpointer_context = None
        self._checkpointer = None
        self._manual_backend: SQLStorageBackend | None = None
        self.graph = None

        if self._can_use_native_langgraph():
            self._initialize_native_graph()
        else:
            self._manual_backend = SQLStorageBackend(self.database_path)
            self._initialize_manual_store()

    def close(self) -> None:
        if self._native_connection is not None:
            self._native_connection.close()
        if self._checkpointer_context is not None:
            self._checkpointer_context.__exit__(None, None, None)
        if self._manual_backend is not None:
            self._manual_backend.close()

    def start(self, task_id: str, instruction: str) -> WorkflowExecutionResult:
        if self.graph is not None:
            result = self.graph.invoke(
                {
                    "task_id": task_id,
                    "instruction": instruction,
                    "actions": [],
                    "next_action_index": 0,
                    "logs": [],
                    "last_result": None,
                    "approved": None,
                    "outcome": None,
                },
                self._config(task_id),
            )
            return self._normalize_result(result)

        state: WorkflowState = {
            "task_id": task_id,
            "instruction": instruction,
            "actions": [],
            "next_action_index": 0,
            "logs": [],
            "last_result": None,
            "approved": None,
            "outcome": None,
        }
        return self._run(task_id, state)

    def resume(self, task_id: str, approved: bool) -> WorkflowExecutionResult:
        if self.graph is not None:
            result = self.graph.invoke(Command(resume=approved), self._config(task_id))
            return self._normalize_result(result)

        state = self._load_state(task_id)
        if state is None:
            raise KeyError(task_id)
        state["approved"] = approved
        return self._run(task_id, state)

    def delete_thread(self, task_id: str) -> None:
        if self.graph is not None:
            self._checkpointer.delete_thread(task_id)
            return
        with self._manual_backend.connect() as connection:
            connection.execute(
                "DELETE FROM workflow_threads WHERE task_id = ?",
                (task_id,),
            )

    def _can_use_native_langgraph(self) -> bool:
        if not LANGGRAPH_AVAILABLE:
            return False
        if is_postgres_target(self.database_path):
            return PostgresSaver is not None
        return SqliteSaver is not None

    def _initialize_native_graph(self) -> None:
        if is_postgres_target(self.database_path):
            self._checkpointer_context = PostgresSaver.from_conn_string(self.database_path)
            self._checkpointer = self._checkpointer_context.__enter__()
        else:
            sqlite_path = resolve_sqlite_path(self.database_path)
            sqlite_path.parent.mkdir(parents=True, exist_ok=True)
            self._native_connection = sqlite3.connect(sqlite_path, check_same_thread=False)
            self._checkpointer = SqliteSaver(self._native_connection)
        self._checkpointer.setup()
        self.graph = self._build_graph().compile(checkpointer=self._checkpointer)

    def _initialize_manual_store(self) -> None:
        with self._manual_backend.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_threads (
                    task_id TEXT PRIMARY KEY,
                    state_json TEXT NOT NULL
                )
                """
            )

    def _config(self, task_id: str) -> dict[str, dict[str, str]]:
        return {"configurable": {"thread_id": task_id}}

    def _build_graph(self) -> StateGraph:
        builder = StateGraph(WorkflowState)
        builder.add_node("plan", self._plan_node)
        builder.add_node("approval", self._approval_node)
        builder.add_node("execute", self._execute_node)
        builder.add_node("complete", self._complete_node)
        builder.add_node("reject", self._reject_node)
        builder.add_edge(START, "plan")
        builder.add_conditional_edges(
            "plan",
            self._route_next_step,
            {
                "approval": "approval",
                "execute": "execute",
                "complete": "complete",
            },
        )
        builder.add_conditional_edges(
            "execute",
            self._route_next_step,
            {
                "approval": "approval",
                "execute": "execute",
                "complete": "complete",
            },
        )
        builder.add_conditional_edges(
            "approval",
            self._route_approval_decision,
            {
                "execute": "execute",
                "reject": "reject",
            },
        )
        builder.add_edge("complete", END)
        builder.add_edge("reject", END)
        return builder

    def _plan_node(self, state: WorkflowState) -> WorkflowState:
        if state.get("actions"):
            return {}
        actions = [
            action.to_dict()
            for action in self._plan_actions(
                state["instruction"],
                task_id=state.get("task_id"),
            )
        ]
        return {
            "actions": actions,
            "next_action_index": 0,
        }

    def _approval_node(self, state: WorkflowState) -> WorkflowState:
        action = self._get_current_action(state)
        approved = interrupt(
            {
                "command": action.command,
                "reason": action.reason or "Sensitive action requires approval",
                "action_name": action.name,
            }
        )
        return {"approved": bool(approved)}

    def _execute_node(self, state: WorkflowState) -> WorkflowState:
        action = self._get_current_action(state)
        if action.name == "shell.exec":
            self.safety_filter.ensure_safe(action.command)

        result = self.registry.execute(action)
        redacted_result = self.redactor.redact(str(result))
        logs = list(state.get("logs", []))
        if not action.requires_approval:
            logs.append(redacted_result)

        return {
            "logs": logs,
            "last_result": redacted_result,
            "next_action_index": state.get("next_action_index", 0) + 1,
            "approved": None,
        }

    def _complete_node(self, _state: WorkflowState) -> WorkflowState:
        return {"outcome": "completed", "approved": None}

    def _reject_node(self, _state: WorkflowState) -> WorkflowState:
        return {"outcome": "rejected", "approved": None}

    def _route_next_step(self, state: WorkflowState) -> str:
        actions = state.get("actions", [])
        next_action_index = state.get("next_action_index", 0)
        if next_action_index >= len(actions):
            return "complete"
        action = self._get_current_action(state)
        if action.requires_approval:
            return "approval"
        return "execute"

    def _route_approval_decision(self, state: WorkflowState) -> str:
        if state.get("approved"):
            return "execute"
        return "reject"

    def _get_current_action(self, state: WorkflowState) -> TaskAction:
        actions = state.get("actions", [])
        next_action_index = state.get("next_action_index", 0)
        return TaskAction.from_dict(actions[next_action_index])

    def _normalize_result(self, payload: dict[str, Any]) -> WorkflowExecutionResult:
        interrupts = payload.get("__interrupt__") or []
        state = {
            key: value
            for key, value in payload.items()
            if key != "__interrupt__"
        }
        if interrupts:
            interrupt_event = interrupts[0]
            return WorkflowExecutionResult(
                state=state,
                interrupt_id=interrupt_event.id,
                interrupt_value=dict(interrupt_event.value),
            )
        return WorkflowExecutionResult(state=state)

    def _run(self, task_id: str, state: WorkflowState) -> WorkflowExecutionResult:
        if not state.get("actions"):
            state["actions"] = [
                action.to_dict()
                for action in self._plan_actions(
                    state["instruction"],
                    task_id=state.get("task_id") or task_id,
                )
            ]
            state["next_action_index"] = 0

        while True:
            actions = state.get("actions", [])
            next_action_index = state.get("next_action_index", 0)
            if next_action_index >= len(actions):
                state["outcome"] = "completed"
                return WorkflowExecutionResult(state=state)

            action = TaskAction.from_dict(actions[next_action_index])
            approved = state.get("approved")
            if action.requires_approval and approved is None:
                self._save_state(task_id, state)
                return WorkflowExecutionResult(
                    state=state,
                    interrupt_id=f"{task_id}:{next_action_index}",
                    interrupt_value={
                        "command": action.command,
                        "reason": action.reason or "Sensitive action requires approval",
                        "action_name": action.name,
                    },
                )
            if action.requires_approval and approved is False:
                state["outcome"] = "rejected"
                state["approved"] = None
                return WorkflowExecutionResult(state=state)

            if action.name == "shell.exec":
                self.safety_filter.ensure_safe(action.command)

            result = self.registry.execute(action)
            redacted_result = self.redactor.redact(str(result))
            logs = list(state.get("logs", []))
            if not action.requires_approval:
                logs.append(redacted_result)
            state["logs"] = logs
            state["last_result"] = redacted_result
            state["next_action_index"] = next_action_index + 1
            state["approved"] = None

    def _save_state(self, task_id: str, state: WorkflowState) -> None:
        with self._manual_backend.connect() as connection:
            connection.execute(
                """
                INSERT INTO workflow_threads(task_id, state_json)
                VALUES (?, ?)
                ON CONFLICT(task_id) DO UPDATE SET state_json = excluded.state_json
                """,
                (task_id, json.dumps(state, ensure_ascii=False)),
            )

    def _plan_actions(self, instruction: str, *, task_id: str | None) -> list[TaskAction]:
        try:
            return self.planner.plan(instruction, task_id=task_id)
        except TypeError as exc:
            if "task_id" not in str(exc):
                raise
            return self.planner.plan(instruction)

    def _load_state(self, task_id: str) -> WorkflowState | None:
        with self._manual_backend.connect() as connection:
            row = connection.execute(
                "SELECT state_json FROM workflow_threads WHERE task_id = ?",
                (task_id,),
            ).fetchone()
        if row is None:
            return None
        return json.loads(row[0])
