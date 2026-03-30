from __future__ import annotations

import os
import subprocess


class ProcessSkill:
    def inspect_load(self) -> str:
        load1, load5, load15 = os.getloadavg()
        return f"load1={load1:.2f} load5={load5:.2f} load15={load15:.2f}"

    def list_processes(self) -> str:
        result = subprocess.run(
            ["ps", "-eo", "pid,comm,%cpu,%mem", "--sort=-%cpu"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout.strip() or result.stderr.strip() or "No process data"
