from __future__ import annotations

import subprocess


class DockerSkill:
    def list_containers(self, include_all: bool = False) -> str:
        command = ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"]
        if include_all:
            command.insert(2, "-a")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout.strip() or result.stderr.strip() or "No containers found"

    def restart_container(self, container: str) -> str:
        result = subprocess.run(
            ["docker", "restart", container],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"Failed to restart {container}")
        return result.stdout.strip() or f"restarted {container}"
