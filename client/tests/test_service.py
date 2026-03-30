from client.service import ClientService


class RecordingRunner:
    def __init__(self) -> None:
        self.assignments: list[tuple[str, str]] = []
        self.approvals: list[tuple[str, bool]] = []

    def handle_assignment(self, task_id: str, instruction: str) -> None:
        self.assignments.append((task_id, instruction))

    def handle_approval(self, task_id: str, approved: bool) -> None:
        self.approvals.append((task_id, approved))


def test_service_routes_gateway_messages_to_runner():
    runner = RecordingRunner()
    service = ClientService(runner=runner, transport=None)

    service.handle_gateway_message(
        {
            "type": "TASK_ASSIGNED",
            "task": {
                "task_id": "task-1",
                "instruction": "查看系统负载",
            },
        }
    )
    service.handle_gateway_message(
        {
            "type": "APPROVAL_DECISION",
            "task_id": "task-1",
            "approved": True,
        }
    )

    assert runner.assignments == [("task-1", "查看系统负载")]
    assert runner.approvals == [("task-1", True)]
