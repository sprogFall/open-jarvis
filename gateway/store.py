from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from skill_catalog import builtin_skill


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

DEVICE_REGISTRY_BOOTSTRAP_KEY = "device_registry_bootstrapped"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS gateway_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
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
    logs_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS devices (
    device_id    TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    type         TEXT NOT NULL DEFAULT 'cli',
    device_key   TEXT NOT NULL,
    created_at   TEXT NOT NULL,
    last_seen_at TEXT
);
CREATE TABLE IF NOT EXISTS skills (
    skill_id           TEXT PRIMARY KEY,
    name               TEXT NOT NULL,
    description        TEXT NOT NULL DEFAULT '',
    config_json        TEXT NOT NULL DEFAULT '{}',
    archive_filename   TEXT,
    archive_sha256     TEXT,
    archive_size       INTEGER NOT NULL DEFAULT 0,
    archive_updated_at TEXT,
    created_at         TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS device_skills (
    device_id   TEXT NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
    skill_id    TEXT NOT NULL REFERENCES skills(skill_id)   ON DELETE CASCADE,
    assigned_at TEXT NOT NULL,
    config_json TEXT NOT NULL DEFAULT '{}',
    PRIMARY KEY (device_id, skill_id)
);
CREATE TABLE IF NOT EXISTS ai_configs (
    scope      TEXT NOT NULL,
    device_id  TEXT NOT NULL DEFAULT '',
    provider   TEXT NOT NULL,
    model      TEXT NOT NULL,
    api_key    TEXT NOT NULL,
    base_url   TEXT,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (scope, device_id)
);
"""

_MIGRATIONS = {
    "tasks": {
        "created_at": "TEXT NOT NULL DEFAULT ''",
    },
    "devices": {
        "name": "TEXT NOT NULL DEFAULT ''",
        "type": "TEXT NOT NULL DEFAULT 'cli'",
        "device_key": "TEXT NOT NULL DEFAULT ''",
        "created_at": "TEXT NOT NULL DEFAULT ''",
        "last_seen_at": "TEXT",
    },
    "skills": {
        "description": "TEXT NOT NULL DEFAULT ''",
        "config_json": "TEXT NOT NULL DEFAULT '{}'",
        "archive_filename": "TEXT",
        "archive_sha256": "TEXT",
        "archive_size": "INTEGER NOT NULL DEFAULT 0",
        "archive_updated_at": "TEXT",
        "created_at": "TEXT NOT NULL DEFAULT ''",
    },
    "device_skills": {
        "assigned_at": "TEXT NOT NULL DEFAULT ''",
        "config_json": "TEXT NOT NULL DEFAULT '{}'",
    },
}


class GatewayStore:
    """统一存储层 — 自动检测 PostgreSQL / SQLite."""

    def __init__(self, database_url: str) -> None:
        self._pg = database_url.startswith("postgresql")
        self._url = database_url
        if self._pg:
            import psycopg2.pool  # noqa: F811
            self._pool = psycopg2.pool.SimpleConnectionPool(1, 10, database_url)
        else:
            path = database_url
            for prefix in ("sqlite:///", "sqlite://"):
                if path.startswith(prefix):
                    path = path[len(prefix):]
                    break
            self._sqlite_path = Path(path)
            self._sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self._device_table_preexisted = self._table_exists("devices")
        self._initialize()

    # ── connection ────────────────────────────────────────────────────────

    @contextmanager
    def _connect(self):
        """Yield a connection that auto-commits on success, auto-rollbacks on error."""
        if self._pg:
            conn = self._pool.getconn()
            try:
                yield _PgConn(conn)
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                self._pool.putconn(conn)
        else:
            conn = sqlite3.connect(self._sqlite_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            try:
                yield _SqliteConn(conn)
                conn.commit()
            finally:
                conn.close()

    # ── init ──────────────────────────────────────────────────────────────

    @staticmethod
    def _now() -> str:
        return datetime.now(tz=timezone.utc).isoformat()

    def _initialize(self) -> None:
        with self._connect() as db:
            if self._pg:
                db.execute(_SCHEMA)
            else:
                db.executescript(_SCHEMA)
            self._migrate_schema(db)

    def _migrate_schema(self, db: Any) -> None:
        for table_name, columns in _MIGRATIONS.items():
            existing_columns = self._list_columns(db, table_name)
            for column_name, definition in columns.items():
                if column_name in existing_columns:
                    continue
                db.execute(
                    f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}"
                )

    def _list_columns(self, db: Any, table_name: str) -> set[str]:
        if self._pg:
            rows = db.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = current_schema() AND table_name = ?",
                (table_name,),
            ).fetchall()
            return {dict(row)["column_name"] for row in rows}
        rows = db.execute(f"PRAGMA table_info({table_name})").fetchall()
        return {dict(row)["name"] for row in rows}

    def _table_exists(self, table_name: str) -> bool:
        with self._connect() as db:
            if self._pg:
                row = db.execute(
                    "SELECT 1 FROM information_schema.tables "
                    "WHERE table_schema = current_schema() AND table_name = ?",
                    (table_name,),
                ).fetchone()
            else:
                row = db.execute(
                    "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                    (table_name,),
                ).fetchone()
        return row is not None

    @staticmethod
    def _row_value(row: Any, key: str) -> Any:
        return dict(row)[key]

    # ── tasks ─────────────────────────────────────────────────────────────

    def create_task(self, task_id: str, device_id: str, instruction: str) -> dict:
        now = self._now()
        with self._connect() as db:
            db.execute(
                "INSERT INTO tasks "
                "(task_id, device_id, instruction, status, checkpoint_id, "
                "command, reason, result, error, logs_json, created_at) "
                "VALUES (?, ?, ?, 'PENDING_DISPATCH', NULL, NULL, NULL, NULL, NULL, '[]', ?)",
                (task_id, device_id, instruction, now),
            )
        return self.get_task(task_id)  # type: ignore[return-value]

    def get_task(self, task_id: str) -> dict | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
        return self._row_to_task(row) if row else None

    def update_task(self, task_id: str, **updates: Any) -> dict:
        if not updates:
            task = self.get_task(task_id)
            if task is None:
                raise KeyError(task_id)
            return task
        assignments = []
        values: list[Any] = []
        for key, value in updates.items():
            column = "logs_json" if key == "logs" else key
            if key == "logs":
                value = json.dumps(value, ensure_ascii=False)
            assignments.append(f"{column} = ?")
            values.append(value)
        values.append(task_id)
        with self._connect() as db:
            db.execute(
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
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM tasks WHERE status = 'AWAITING_APPROVAL' ORDER BY created_at ASC"
            ).fetchall()
        return [self._row_to_task(row) for row in rows]

    def list_tasks_for_device(self, device_id: str, statuses: Iterable[str]) -> list[dict]:
        statuses = tuple(statuses)
        if not statuses:
            return []
        placeholders = ", ".join("?" for _ in statuses)
        with self._connect() as db:
            rows = db.execute(
                f"SELECT * FROM tasks WHERE device_id = ? AND status IN ({placeholders}) "
                "ORDER BY created_at ASC",
                (device_id, *statuses),
            ).fetchall()
        return [self._row_to_task(row) for row in rows]

    def list_tasks_filtered(
        self, *, status: str | None = None, device_id: str | None = None, limit: int = 50,
    ) -> list[dict]:
        query = "SELECT * FROM tasks WHERE 1=1"
        params: list[Any] = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if device_id:
            query += " AND device_id = ?"
            params.append(device_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as db:
            rows = db.execute(query, params).fetchall()
        return [self._row_to_task(row) for row in rows]

    def list_connected_view(self) -> list[dict]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT device_id, COUNT(*) AS task_count FROM tasks "
                "GROUP BY device_id ORDER BY device_id ASC"
            ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def _row_to_task(row: Any) -> dict:
        task = dict(row)
        task["logs"] = json.loads(task.pop("logs_json"))
        task.pop("created_at", None)
        return {field: task.get(field) for field in TASK_FIELDS}

    # ── devices ───────────────────────────────────────────────────────────

    @staticmethod
    def _row_to_dict(row: Any) -> dict:
        d = dict(row)
        for key in list(d):
            if key.endswith("_json"):
                d[key.removesuffix("_json")] = json.loads(d.pop(key))
        builtin = builtin_skill(str(d.get("skill_id", "")))
        if builtin is not None:
            d["source"] = "builtin"
            d["archive_ready"] = True
            d["action_names"] = builtin.action_names
        else:
            d["source"] = "archive"
            d["action_names"] = []
            if "archive_sha256" in d:
                d["archive_ready"] = bool(d.get("archive_sha256"))
        return d

    def sync_device(self, device_id: str, device_key: str) -> dict:
        now = self._now()
        with self._connect() as db:
            db.execute(
                "INSERT INTO devices (device_id, name, type, device_key, created_at) "
                "VALUES (?, ?, 'cli', ?, ?) "
                "ON CONFLICT(device_id) DO NOTHING",
                (device_id, device_id, device_key, now),
            )
        return self.get_device(device_id)  # type: ignore[return-value]

    def initialize_device_registry(self, configured_devices: dict[str, str]) -> dict[str, str]:
        with self._connect() as db:
            if self._get_meta(db, DEVICE_REGISTRY_BOOTSTRAP_KEY) != "1":
                if not self._device_table_preexisted and db.fetchval("SELECT COUNT(*) FROM devices") == 0:
                    now = self._now()
                    for device_id, device_key in configured_devices.items():
                        db.execute(
                            "INSERT INTO devices (device_id, name, type, device_key, created_at) "
                            "VALUES (?, ?, 'cli', ?, ?) "
                            "ON CONFLICT(device_id) DO NOTHING",
                            (device_id, device_id, device_key, now),
                        )
                self._set_meta(db, DEVICE_REGISTRY_BOOTSTRAP_KEY, "1")
            rows = db.execute(
                "SELECT device_id, device_key FROM devices ORDER BY created_at ASC, device_id ASC"
            ).fetchall()
        return {
            self._row_value(row, "device_id"): self._row_value(row, "device_key")
            for row in rows
        }

    def _get_meta(self, db: Any, key: str) -> str | None:
        row = db.execute(
            "SELECT value FROM gateway_meta WHERE key = ?",
            (key,),
        ).fetchone()
        if row is None:
            return None
        return self._row_value(row, "value")

    def _set_meta(self, db: Any, key: str, value: str) -> None:
        db.execute(
            "INSERT INTO gateway_meta (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )

    def create_device(self, device_id: str, name: str, device_type: str, device_key: str) -> dict:
        now = self._now()
        with self._connect() as db:
            db.execute(
                "INSERT INTO devices (device_id, name, type, device_key, created_at) VALUES (?,?,?,?,?)",
                (device_id, name, device_type, device_key, now),
            )
        return self.get_device(device_id)  # type: ignore[return-value]

    def get_device(self, device_id: str) -> dict | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM devices WHERE device_id = ?", (device_id,)).fetchone()
        return self._row_to_dict(row) if row else None

    def list_devices(self) -> list[dict]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM devices ORDER BY created_at ASC").fetchall()
        return [self._row_to_dict(r) for r in rows]

    def update_device(self, device_id: str, **updates: Any) -> dict:
        allowed = {"name", "type", "device_key"}
        cols = {k: v for k, v in updates.items() if k in allowed}
        if not cols:
            return self.get_device(device_id)  # type: ignore[return-value]
        sets = ", ".join(f"{k} = ?" for k in cols)
        vals = list(cols.values()) + [device_id]
        with self._connect() as db:
            db.execute(f"UPDATE devices SET {sets} WHERE device_id = ?", vals)
        return self.get_device(device_id)  # type: ignore[return-value]

    def delete_device(self, device_id: str) -> bool:
        with self._connect() as db:
            cur = db.execute("DELETE FROM devices WHERE device_id = ?", (device_id,))
        return cur.rowcount > 0

    def touch_device(self, device_id: str) -> None:
        with self._connect() as db:
            db.execute(
                "UPDATE devices SET last_seen_at = ? WHERE device_id = ?",
                (self._now(), device_id),
            )

    # ── skills ────────────────────────────────────────────────────────────

    def create_skill(self, skill_id: str, name: str, description: str = "", config: dict | None = None) -> dict:
        now = self._now()
        with self._connect() as db:
            db.execute(
                "INSERT INTO skills "
                "(skill_id, name, description, config_json, archive_filename, archive_sha256, "
                "archive_size, archive_updated_at, created_at) "
                "VALUES (?, ?, ?, ?, NULL, NULL, 0, NULL, ?)",
                (skill_id, name, description, json.dumps(config or {}, ensure_ascii=False), now),
            )
        return self.get_skill(skill_id)  # type: ignore[return-value]

    def get_skill(self, skill_id: str) -> dict | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM skills WHERE skill_id = ?", (skill_id,)).fetchone()
        return self._row_to_dict(row) if row else None

    def list_skills(self) -> list[dict]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM skills ORDER BY created_at ASC").fetchall()
        return [self._row_to_dict(r) for r in rows]

    def update_skill(self, skill_id: str, **updates: Any) -> dict:
        allowed = {"name", "description", "config"}
        cols: dict[str, Any] = {}
        for k, v in updates.items():
            if k not in allowed:
                continue
            if k == "config":
                cols["config_json"] = json.dumps(v, ensure_ascii=False)
            else:
                cols[k] = v
        if not cols:
            return self.get_skill(skill_id)  # type: ignore[return-value]
        sets = ", ".join(f"{k} = ?" for k in cols)
        vals = list(cols.values()) + [skill_id]
        with self._connect() as db:
            db.execute(f"UPDATE skills SET {sets} WHERE skill_id = ?", vals)
        return self.get_skill(skill_id)  # type: ignore[return-value]

    def delete_skill(self, skill_id: str) -> bool:
        with self._connect() as db:
            cur = db.execute("DELETE FROM skills WHERE skill_id = ?", (skill_id,))
        return cur.rowcount > 0

    def set_skill_archive(
        self,
        skill_id: str,
        *,
        filename: str,
        sha256: str,
        size: int,
    ) -> dict:
        now = self._now()
        with self._connect() as db:
            db.execute(
                "UPDATE skills SET archive_filename = ?, archive_sha256 = ?, archive_size = ?, "
                "archive_updated_at = ? WHERE skill_id = ?",
                (filename, sha256, size, now, skill_id),
            )
        return self.get_skill(skill_id)  # type: ignore[return-value]

    # ── device-skill 分配 ─────────────────────────────────────────────────

    def assign_skill(self, device_id: str, skill_id: str, config: dict | None = None) -> dict:
        now = self._now()
        with self._connect() as db:
            db.execute(
                "INSERT INTO device_skills (device_id, skill_id, assigned_at, config_json) "
                "VALUES (?, ?, ?, ?) "
                "ON CONFLICT(device_id, skill_id) DO UPDATE SET config_json = excluded.config_json",
                (device_id, skill_id, now, json.dumps(config or {}, ensure_ascii=False)),
            )
        return {"device_id": device_id, "skill_id": skill_id, "assigned_at": now, "config": config or {}}

    def list_devices_for_skill(self, skill_id: str) -> list[str]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT device_id FROM device_skills WHERE skill_id = ? ORDER BY assigned_at ASC",
                (skill_id,),
            ).fetchall()
        return [self._row_value(row, "device_id") for row in rows]

    def unassign_skill(self, device_id: str, skill_id: str) -> bool:
        with self._connect() as db:
            cur = db.execute(
                "DELETE FROM device_skills WHERE device_id = ? AND skill_id = ?",
                (device_id, skill_id),
            )
        return cur.rowcount > 0

    def list_device_skills(self, device_id: str) -> list[dict]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT s.skill_id, s.name, s.description, ds.assigned_at, ds.config_json, "
                "s.config_json AS skill_config_json, s.archive_filename, s.archive_sha256, "
                "s.archive_size, s.archive_updated_at "
                "FROM device_skills ds "
                "JOIN skills s ON s.skill_id = ds.skill_id "
                "WHERE ds.device_id = ? ORDER BY ds.assigned_at ASC",
                (device_id,),
            ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    # ── 统计 ──────────────────────────────────────────────────────────────

    def overview_stats(self) -> dict:
        with self._connect() as db:
            device_count = db.fetchval("SELECT COUNT(*) FROM devices")
            skill_count = db.fetchval("SELECT COUNT(*) FROM skills")
            rows = db.execute(
                "SELECT status, COUNT(*) AS cnt FROM tasks GROUP BY status"
            ).fetchall()
            task_counts = {dict(r)["status"]: dict(r)["cnt"] for r in rows}
        return {
            "device_count": device_count,
            "skill_count": skill_count,
            "task_counts": task_counts,
        }

    # ── ai config ────────────────────────────────────────────────────────────

    def save_ai_config(
        self,
        scope: str,
        *,
        provider: str,
        model: str,
        api_key: str,
        base_url: str | None = None,
        device_id: str | None = None,
    ) -> dict:
        normalized_device_id = device_id or ""
        now = self._now()
        with self._connect() as db:
            db.execute(
                "INSERT INTO ai_configs (scope, device_id, provider, model, api_key, base_url, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(scope, device_id) DO UPDATE SET "
                "provider = excluded.provider, model = excluded.model, "
                "api_key = excluded.api_key, base_url = excluded.base_url, "
                "updated_at = excluded.updated_at",
                (scope, normalized_device_id, provider, model, api_key, base_url, now),
            )
        return self.get_ai_config(scope, device_id=device_id)  # type: ignore[return-value]

    def get_ai_config(self, scope: str, *, device_id: str | None = None) -> dict | None:
        normalized_device_id = device_id or ""
        with self._connect() as db:
            row = db.execute(
                "SELECT scope, device_id, provider, model, api_key, base_url, updated_at "
                "FROM ai_configs WHERE scope = ? AND device_id = ?",
                (scope, normalized_device_id),
            ).fetchone()
        if row is None:
            return None
        payload = dict(row)
        if not payload["device_id"]:
            payload.pop("device_id", None)
        return payload

    def delete_ai_config(self, scope: str, *, device_id: str | None = None) -> bool:
        normalized_device_id = device_id or ""
        with self._connect() as db:
            cursor = db.execute(
                "DELETE FROM ai_configs WHERE scope = ? AND device_id = ?",
                (scope, normalized_device_id),
            )
        return cursor.rowcount > 0


# ── thin wrappers to normalise sqlite3 / psycopg2 differences ────────────

class _SqliteConn:
    """Wraps sqlite3.Connection to provide a unified interface."""

    __slots__ = ("_conn",)

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def execute(self, sql: str, params: tuple | list = ()) -> Any:
        return self._conn.execute(sql, params)

    def executescript(self, sql: str) -> None:
        self._conn.executescript(sql)

    def fetchval(self, sql: str, params: tuple | list = ()) -> Any:
        return self._conn.execute(sql, params).fetchone()[0]


class _PgConn:
    """Wraps psycopg2 connection: translates ? → %s and returns dict rows."""

    __slots__ = ("_conn",)

    def __init__(self, conn: Any) -> None:
        self._conn = conn

    @staticmethod
    def _translate(sql: str) -> str:
        # Replace ? placeholders with %s, but not inside string literals.
        # Simple approach: replace unquoted ? with %s.
        result: list[str] = []
        in_quote = False
        for ch in sql:
            if ch == "'":
                in_quote = not in_quote
            if ch == "?" and not in_quote:
                result.append("%s")
            else:
                result.append(ch)
        return "".join(result)

    def execute(self, sql: str, params: tuple | list = ()) -> Any:
        from psycopg2.extras import RealDictCursor
        cur = self._conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(self._translate(sql), params)
        return cur

    def executescript(self, sql: str) -> None:
        cur = self._conn.cursor()
        cur.execute(sql)

    def fetchval(self, sql: str, params: tuple | list = ()) -> Any:
        cur = self._conn.cursor()
        cur.execute(self._translate(sql), params)
        return cur.fetchone()[0]
