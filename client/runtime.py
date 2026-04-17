from __future__ import annotations

from typing import Callable

from client.checkpoints import CheckpointStore
from client.langgraph_workflow import LangGraphTaskWorkflow
from client.models import TaskAction
from client.redaction import LogRedactor
from client.safety import CommandSafetyFilter
from client.storage import StorageTarget, derive_workflow_storage_target, normalize_storage_target
from skill_catalog import SkillActionSpec


class ActionRegistry:
    def __init__(self, *, enabled_skill_ids: set[str] | None = None) -> None:
        self._handlers: dict[str, Callable[[TaskAction], str]] = {}
        self._action_specs: dict[str, SkillActionSpec] = {}
        self._enabled_skill_ids = enabled_skill_ids
        self._device_skills: list[dict] = []

    def register(
        self,
        name: str,
        handler: Callable[[TaskAction], str],
        *,
        action_spec: SkillActionSpec | None = None,
    ) -> None:
        self._handlers[name] = handler
        if action_spec is not None:
            self._action_specs[name] = action_spec

    def sync_skills(self, skills: list[dict]) -> None:
        self._device_skills = skills
        self._enabled_skill_ids = {
            str(skill["skill_id"])
            for skill in skills
            if skill.get("source") == "builtin"
        }

    def available_actions(self) -> list[SkillActionSpec]:
        return [
            spec
            for spec in self._action_specs.values()
            if self._is_action_enabled(spec)
        ]

    def execute(self, action: TaskAction) -> str:
        handler = self._handlers.get(action.name)
        if handler is None:
            raise KeyError(f"Unknown action handler: {action.name}")
        action_spec = self._action_specs.get(action.name)
        if action_spec is not None and not self._is_action_enabled(action_spec):
            raise PermissionError(f"Skill action is not enabled: {action.name}")
        return handler(action)

    def _is_action_enabled(self, action_spec: SkillActionSpec) -> bool:
        if self._enabled_skill_ids is None:
            return True
        return action_spec.skill_id in self._enabled_skill_ids


class TaskRunner:
    def __init__(
        self,
        planner,
        registry: ActionRegistry,
        transport,
        checkpoints: CheckpointStore,
        workflow_store_path: StorageTarget | None = None,
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
            normalize_storage_target(workflow_store_path)
            if workflow_store_path is not None
            else derive_workflow_storage_target(checkpoints.database_url)
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
