from __future__ import annotations

import asyncio
import threading

from gateway.ai import GatewayAIConfigResolver


class _GatewayLocalTransport:
    def __init__(self, executor: "GatewayLocalExecutor") -> None:
        self.executor = executor

    def send(self, payload: dict) -> None:
        self.executor.publish(payload)


class GatewayLocalExecutor:
    def __init__(self, store, manager, settings) -> None:
        self.store = store
        self.manager = manager
        self.settings = settings
        self.config_resolver = GatewayAIConfigResolver(store, settings)
        self._loop: asyncio.AbstractEventLoop | None = None
        self._lock = threading.Lock()
        self.runner = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def handle_assignment(self, task_id: str, instruction: str) -> None:
        self._run_in_background("handle_assignment", task_id, instruction)

    def handle_approval(self, task_id: str, approved: bool) -> None:
        self._run_in_background("handle_approval", task_id, approved)

    def close(self) -> None:
        if self.runner is not None:
            self.runner.close()

    def _run_in_background(self, method_name: str, *args) -> None:
        worker = threading.Thread(
            target=self._run_serialized,
            args=(method_name, *args),
            daemon=True,
        )
        worker.start()

    def _run_serialized(self, method_name: str, *args) -> None:
        with self._lock:
            self._ensure_runner()
            getattr(self.runner, method_name)(*args)

    def _ensure_runner(self) -> None:
        if self.runner is not None:
            return
        from client.checkpoints import CheckpointStore
        from client.planner import LLMPlanner
        from client.runtime import TaskRunner
        from client.service import build_default_registry

        checkpoints = CheckpointStore(self.settings.local_checkpoint_path)
        self.runner = TaskRunner(
            planner=LLMPlanner(config_resolver=self.config_resolver.resolve),
            registry=build_default_registry(self.settings),
            transport=_GatewayLocalTransport(self),
            checkpoints=checkpoints,
            workflow_store_path=self.settings.local_workflow_store_path,
        )

    def publish(self, payload: dict) -> None:
        if self._loop is None:
            raise RuntimeError("Gateway local executor event loop is not bound")
        future = asyncio.run_coroutine_threadsafe(
            self._apply_payload(payload),
            self._loop,
        )
        future.result()

    async def _apply_payload(self, payload: dict) -> None:
        message_type = payload.get("type")
        task_id = payload.get("task_id")
        if not task_id:
            return
        if message_type == "TASK_STATUS":
            updated = self.store.update_task(task_id, status=payload["status"])
            await self.manager.broadcast_task(updated)
        elif message_type == "TASK_LOG":
            updated = self.store.append_log(task_id, payload["message"])
            await self.manager.broadcast_log(task_id, payload["message"])
            await self.manager.broadcast_task(updated)
        elif message_type == "INTERRUPT_REQUEST":
            updated = self.store.update_task(
                task_id,
                status="AWAITING_APPROVAL",
                checkpoint_id=payload["checkpoint_id"],
                command=payload["command"],
                reason=payload["reason"],
            )
            await self.manager.broadcast_task(updated)
        elif message_type == "TASK_COMPLETED":
            updated = self.store.update_task(
                task_id,
                status="COMPLETED",
                result=payload["result"],
                checkpoint_id=None,
            )
            await self.manager.broadcast_task(updated)
        elif message_type == "TASK_FAILED":
            updated = self.store.update_task(
                task_id,
                status="FAILED",
                error=payload["error"],
                checkpoint_id=None,
            )
            await self.manager.broadcast_task(updated)
