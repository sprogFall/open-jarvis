import pytest

from client.safety import CommandSafetyFilter, UnsafeCommandError


def test_blocks_destructive_shell_command():
    safety = CommandSafetyFilter()

    with pytest.raises(UnsafeCommandError):
        safety.ensure_safe("rm -rf /")


def test_allows_safe_docker_listing():
    safety = CommandSafetyFilter()

    assert safety.ensure_safe("docker ps") == "docker ps"
