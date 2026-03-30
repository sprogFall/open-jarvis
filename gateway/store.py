from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable


TASK_FIELDS = (
    "task_id",
    "device_id",
    "instruction",
    "status",
    "checkpoint_id",
    "command",
    "reason",
    "result",
    "error",
    "logs",
)


class GatewayStore:
    def __init__(self, database_path: Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    device_id TEXT NOT NULL,
                    instruction TEXT NOT NULL,
                    status TEXT NOT NULL,
                    checkpoint_id TEXT,
                    command TEXT,
                    reason TEXT,
                    result TEXT,
                    error TEXT,
                    logs_json TEXT NOT NULL DEFAULT '[]'
                )
                """
            )

    def create_task(self, task_id: str, device_id: str, instruction: str) -> dict:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO tasks (
                    task_id, device_id, instruction, status, checkpoint_id,
                    command, reason, result, error, logs_json
                )
                VALUES (?, ?, ?, 'PENDING_DISPATCH', NULL, NULL, NULL, NULL, NULL, '[]')
                """,
                (task_id, device_id, instruction),
            )
        return self.get_task(task_id)

    def get_task(self, task_id: str) -> dict | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM tasks WHERE task_id = ?",
                (task_id,),
            ).fetchone()
        return self._row_to_task(row) if row else None

    def update_task(self, task_id: str, **updates) -> dict:
        if not updates:
            task = self.get_task(task_id)
            if task is None:
                raise KeyError(task_id)
            return task
        assignments = []
        values = []
        for key, value in updates.items():
            column = "logs_json" if key == "logs" else key
            if key == "logs":
                value = json.dumps(value, ensure_ascii=False)
            assignments.append(f"{column} = ?")
            values.append(value)
        values.append(task_id)
        with self._connect() as connection:
            connection.execute(
                f"UPDATE tasks SET {', '.join(assignments)} WHERE task_id = ?",
                values,
            )
        task = self.get_task(task_id)
        if task is None:
            raise KeyError(task_id)
        return task

    def append_log(self, task_id: str, message: str) -> dict:
        task = self.get_task(task_id)
        if task is None:
            raise KeyError(task_id)
        logs = list(task["logs"])
        logs.append(message)
        return self.update_task(task_id, logs=logs)

    def list_pending_approvals(self) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM tasks
                WHERE status = 'AWAITING_APPROVAL'
                ORDER BY rowid ASC
                """
            ).fetchall()
        return [self._row_to_task(row) for row in rows]

    def list_tasks_for_device(self, device_id: str, statuses: Iterable[str]) -> list[dict]:
        statuses = tuple(statuses)
        if not statuses:
            return []
        placeholders = ", ".join("?" for _ in statuses)
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM tasks
                WHERE device_id = ? AND status IN ({placeholders})
                ORDER BY rowid ASC
                """,
                (device_id, *statuses),
            ).fetchall()
        return [self._row_to_task(row) for row in rows]

    def list_connected_view(self) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT device_id, COUNT(*) AS task_count
                FROM tasks
                GROUP BY device_id
                ORDER BY device_id ASC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def _row_to_task(self, row: sqlite3.Row) -> dict:
        task = dict(row)
        task["logs"] = json.loads(task.pop("logs_json"))
        return {field: task.get(field) for field in TASK_FIELDS}

