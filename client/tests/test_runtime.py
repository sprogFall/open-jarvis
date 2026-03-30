from __future__ import annotations

from client.checkpoints import CheckpointStore
from client.models import TaskAction
from client.runtime import ActionRegistry, TaskRunner


class FixedPlanner:
    def __init__(self, actions: list[TaskAction]):
        self.actions = actions

    def plan(self, instruction: str) -> list[TaskAction]:
        return list(self.actions)


class FakeTransport:
    def __init__(self) -> None:
        self.events: list[dict] = []

    def send(self, payload: dict) -> None:
        self.events.append(payload)


def test_runner_interrupts_and_persists_checkpoint(tmp_path):
    transport = FakeTransport()
    checkpoints = CheckpointStore(tmp_path / "client.db")
    registry = ActionRegistry()
    registry.register("process.inspect_load", lambda _action: "load=0.42")
    registry.register("docker.restart", lambda action: f"restarted {action.args['container']}")
    planner = FixedPlanner(
        [
            TaskAction(
                name="process.inspect_load",
                command="inspect system load",
                args={},
            ),
            TaskAction(
                name="docker.restart",
                command="docker restart api-service",
                args={"container": "api-service"},
                requires_approval=True,
                reason="重启容器会打断服务",
            ),
        ]
    )
    runner = TaskRunner(
        planner=planner,
        registry=registry,
        transport=transport,
        checkpoints=checkpoints,
    )

    runner.handle_assignment("task-1", "查看系统负载，然后重启容器 api-service")

    assert transport.events[0] == {
        "type": "TASK_STATUS",
        "task_id": "task-1",
        "status": "RUNNING",
    }
    assert transport.events[1]["type"] == "TASK_LOG"
    assert transport.events[-1]["type"] == "INTERRUPT_REQUEST"
    assert transport.events[-1]["task_id"] == "task-1"
    assert transport.events[-1]["command"] == "docker restart api-service"
    assert transport.events[-1]["reason"] == "重启容器会打断服务"
    assert transport.events[-1]["checkpoint_id"]
    checkpoint = checkpoints.load("task-1")
    assert checkpoint["instruction"] == "查看系统负载，然后重启容器 api-service"
    assert checkpoint["delivered_log_count"] == 1


def test_runner_resumes_after_approval(tmp_path):
    transport = FakeTransport()
    checkpoints = CheckpointStore(tmp_path / "client.db")
    registry = ActionRegistry()
    registry.register("process.inspect_load", lambda _action: "load=0.42")
    registry.register("docker.restart", lambda action: f"restarted {action.args['container']}")
    planner = FixedPlanner(
        [
            TaskAction(
                name="process.inspect_load",
                command="inspect system load",
                args={},
            ),
            TaskAction(
                name="docker.restart",
                command="docker restart api-service",
                args={"container": "api-service"},
                requires_approval=True,
                reason="重启容器会打断服务",
            ),
        ]
    )
    runner = TaskRunner(
        planner=planner,
        registry=registry,
        transport=transport,
        checkpoints=checkpoints,
    )

    runner.handle_assignment("task-2", "查看系统负载，然后重启容器 api-service")
    runner.handle_approval("task-2", approved=True)

    assert transport.events[-2] == {
        "type": "TASK_STATUS",
        "task_id": "task-2",
        "status": "RESUMING",
    }
    assert transport.events[-1] == {
        "type": "TASK_COMPLETED",
        "task_id": "task-2",
        "result": "restarted api-service",
    }
    assert checkpoints.load("task-2") is None


def test_runner_marks_task_rejected_when_user_denies(tmp_path):
    transport = FakeTransport()
    checkpoints = CheckpointStore(tmp_path / "client.db")
    registry = ActionRegistry()
    registry.register("docker.restart", lambda action: f"restarted {action.args['container']}")
    planner = FixedPlanner(
        [
            TaskAction(
                name="docker.restart",
                command="docker restart api-service",
                args={"container": "api-service"},
                requires_approval=True,
                reason="重启容器会打断服务",
            ),
        ]
    )
    runner = TaskRunner(
        planner=planner,
        registry=registry,
        transport=transport,
        checkpoints=checkpoints,
    )

    runner.handle_assignment("task-3", "重启容器 api-service")
    runner.handle_approval("task-3", approved=False)

    assert transport.events[-1] == {
        "type": "TASK_STATUS",
        "task_id": "task-3",
        "status": "REJECTED",
    }
    assert checkpoints.load("task-3") is None


def test_runner_resumes_with_new_instance_from_langgraph_sqlite(tmp_path):
    transport = FakeTransport()
    checkpoints = CheckpointStore(tmp_path / "client.db")
    workflow_path = tmp_path / "langgraph.db"
    registry = ActionRegistry()
    registry.register("process.inspect_load", lambda _action: "load=0.42")
    registry.register("docker.restart", lambda action: f"restarted {action.args['container']}")
    planner = FixedPlanner(
        [
            TaskAction(
                name="process.inspect_load",
                command="inspect system load",
                args={},
            ),
            TaskAction(
                name="docker.restart",
                command="docker restart api-service",
                args={"container": "api-service"},
                requires_approval=True,
                reason="重启容器会打断服务",
            ),
        ]
    )
    runner = TaskRunner(
        planner=planner,
        registry=registry,
        transport=transport,
        checkpoints=checkpoints,
        workflow_store_path=workflow_path,
    )

    runner.handle_assignment("task-4", "查看系统负载，然后重启容器 api-service")

    restarted_transport = FakeTransport()
    restarted_runner = TaskRunner(
        planner=planner,
        registry=registry,
        transport=restarted_transport,
        checkpoints=checkpoints,
        workflow_store_path=workflow_path,
    )
    restarted_runner.handle_approval("task-4", approved=True)

    assert workflow_path.exists()
    assert restarted_transport.events[0] == {
        "type": "TASK_STATUS",
        "task_id": "task-4",
        "status": "RESUMING",
    }
    assert restarted_transport.events[-1] == {
        "type": "TASK_COMPLETED",
        "task_id": "task-4",
        "result": "restarted api-service",
    }
