from __future__ import annotations

from pathlib import Path
from typing import Callable

from client.checkpoints import CheckpointStore
from client.langgraph_workflow import LangGraphTaskWorkflow
from client.models import TaskAction
from client.redaction import LogRedactor
from client.safety import CommandSafetyFilter


class ActionRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, Callable[[TaskAction], str]] = {}

    def register(self, name: str, handler: Callable[[TaskAction], str]) -> None:
        self._handlers[name] = handler

    def execute(self, action: TaskAction) -> str:
        handler = self._handlers.get(action.name)
        if handler is None:
            raise KeyError(f"Unknown action handler: {action.name}")
        return handler(action)


class TaskRunner:
    def __init__(
        self,
        planner,
        registry: ActionRegistry,
        transport,
        checkpoints: CheckpointStore,
        workflow_store_path: Path | None = None,
        redactor: LogRedactor | None = None,
        safety_filter: CommandSafetyFilter | None = None,
    ) -> None:
        self.planner = planner
        self.registry = registry
        self.transport = transport
        self.checkpoints = checkpoints
        self.redactor = redactor or LogRedactor()
        self.safety_filter = safety_filter or CommandSafetyFilter()
        self.workflow_store_path = (
            Path(workflow_store_path)
            if workflow_store_path is not None
            else checkpoints.database_path.with_suffix(".langgraph.db")
        )
        self.workflow = LangGraphTaskWorkflow(
            planner=self.planner,
            registry=self.registry,
            redactor=self.redactor,
            safety_filter=self.safety_filter,
            database_path=self.workflow_store_path,
        )

    def close(self) -> None:
        self.workflow.close()

    def handle_assignment(self, task_id: str, instruction: str) -> None:
        self.transport.send(
            {
                "type": "TASK_STATUS",
                "task_id": task_id,
                "status": "RUNNING",
            }
        )
        try:
            result = self.workflow.start(task_id, instruction)
            self._handle_workflow_result(
                task_id=task_id,
                instruction=instruction,
                delivered_log_count=0,
                result=result,
            )
        except Exception as exc:
            self._fail_task(task_id, exc)

    def handle_approval(self, task_id: str, approved: bool) -> None:
        checkpoint = self.checkpoints.load(task_id)
        if checkpoint is None:
            return
        delivered_log_count = checkpoint.get("delivered_log_count", 0)
        if not approved:
            try:
                result = self.workflow.resume(task_id, approved=False)
                self._handle_workflow_result(
                    task_id=task_id,
                    instruction=checkpoint["instruction"],
                    delivered_log_count=delivered_log_count,
                    result=result,
                )
            except Exception as exc:
                self._fail_task(task_id, exc)
            return
        self.transport.send(
            {
                "type": "TASK_STATUS",
                "task_id": task_id,
                "status": "RESUMING",
            }
        )
        try:
            result = self.workflow.resume(task_id, approved=True)
            self._handle_workflow_result(
                task_id=task_id,
                instruction=checkpoint["instruction"],
                delivered_log_count=delivered_log_count,
                result=result,
            )
        except Exception as exc:
            self._fail_task(task_id, exc)

    def _handle_workflow_result(
        self,
        *,
        task_id: str,
        instruction: str,
        delivered_log_count: int,
        result,
    ) -> None:
        logs = result.logs
        for message in logs[delivered_log_count:]:
            self.transport.send(
                {
                    "type": "TASK_LOG",
                    "task_id": task_id,
                    "message": message,
                }
            )
        if result.is_interrupted:
            self.checkpoints.save(
                task_id,
                {
                    "instruction": instruction,
                    "delivered_log_count": len(logs),
                },
            )
            self.transport.send(
                {
                    "type": "INTERRUPT_REQUEST",
                    "task_id": task_id,
                    "checkpoint_id": result.interrupt_id,
                    "command": result.interrupt_value["command"],
                    "reason": result.interrupt_value["reason"],
                }
            )
            return
        self.checkpoints.delete(task_id)
        self.workflow.delete_thread(task_id)
        if result.outcome == "rejected":
            self.transport.send(
                {
                    "type": "TASK_STATUS",
                    "task_id": task_id,
                    "status": "REJECTED",
                }
            )
            return
        self.transport.send(
            {
                "type": "TASK_COMPLETED",
                "task_id": task_id,
                "result": result.last_result or "completed",
            }
        )

    def _fail_task(self, task_id: str, exc: Exception) -> None:
        self.checkpoints.delete(task_id)
        self.workflow.delete_thread(task_id)
        self.transport.send(
            {
                "type": "TASK_FAILED",
                "task_id": task_id,
                "error": self.redactor.redact(str(exc)),
            }
        )
