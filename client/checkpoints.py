from __future__ import annotations

import json
import sqlite3
from pathlib import Path


class CheckpointStore:
    def __init__(self, database_path: Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS checkpoints (
                    task_id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL
                )
                """
            )

    def save(self, task_id: str, payload: dict) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO checkpoints(task_id, payload_json)
                VALUES (?, ?)
                ON CONFLICT(task_id) DO UPDATE SET payload_json = excluded.payload_json
                """,
                (task_id, json.dumps(payload, ensure_ascii=False)),
            )

    def load(self, task_id: str) -> dict | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM checkpoints WHERE task_id = ?",
                (task_id,),
            ).fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def delete(self, task_id: str) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM checkpoints WHERE task_id = ?", (task_id,))

