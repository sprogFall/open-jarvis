from __future__ import annotations

import json

from client.storage import SQLStorageBackend, StorageTarget


_CHECKPOINTS_SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS checkpoints (
        task_id TEXT PRIMARY KEY,
        payload_json TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_config (
        scope TEXT PRIMARY KEY,
        payload_json TEXT NOT NULL
    )
    """,
]


class CheckpointStore:
    def __init__(self, database_path: StorageTarget, *, ai_scope: str = "default") -> None:
        self.backend = SQLStorageBackend(database_path)
        self.database_url = self.backend.database_url
        self.database_path = self.backend.sqlite_path
        self.ai_scope = ai_scope
        self._initialize()

    def close(self) -> None:
        self.backend.close()

    def _initialize(self) -> None:
        with self.backend.connect() as connection:
            for statement in _CHECKPOINTS_SCHEMA:
                connection.execute(statement)

    def save(self, task_id: str, payload: dict) -> None:
        with self.backend.connect() as connection:
            connection.execute(
                """
                INSERT INTO checkpoints(task_id, payload_json)
                VALUES (?, ?)
                ON CONFLICT(task_id) DO UPDATE SET payload_json = excluded.payload_json
                """,
                (task_id, json.dumps(payload, ensure_ascii=False)),
            )

    def load(self, task_id: str) -> dict | None:
        with self.backend.connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM checkpoints WHERE task_id = ?",
                (task_id,),
            ).fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def delete(self, task_id: str) -> None:
        with self.backend.connect() as connection:
            connection.execute("DELETE FROM checkpoints WHERE task_id = ?", (task_id,))

    def save_ai_config(self, payload: dict) -> None:
        with self.backend.connect() as connection:
            connection.execute(
                """
                INSERT INTO ai_config(scope, payload_json)
                VALUES (?, ?)
                ON CONFLICT(scope) DO UPDATE SET payload_json = excluded.payload_json
                """,
                (self.ai_scope, json.dumps(payload, ensure_ascii=False)),
            )

    def load_ai_config(self) -> dict | None:
        with self.backend.connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM ai_config WHERE scope = ?",
                (self.ai_scope,),
            ).fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def delete_ai_config(self) -> None:
        with self.backend.connect() as connection:
            connection.execute("DELETE FROM ai_config WHERE scope = ?", (self.ai_scope,))
