from client.planner import RuleBasedPlanner


def test_planner_extracts_process_and_docker_actions():
    planner = RuleBasedPlanner()

    actions = planner.plan("查看系统负载，然后重启容器 api-service")

    assert [action.name for action in actions] == [
        "process.inspect_load",
        "docker.restart",
    ]
    assert actions[1].requires_approval is True
    assert actions[1].args == {"container": "api-service"}


def test_planner_translates_working_directory_request_into_pwd():
    planner = RuleBasedPlanner()

    actions = planner.plan("查看本机工作目录")

    assert [action.name for action in actions] == ["shell.exec"]
    assert actions[0].command == "pwd"
    assert actions[0].args == {"command": "pwd"}
    assert actions[0].requires_approval is True
