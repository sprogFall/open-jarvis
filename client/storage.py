from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any


StorageTarget = str | Path


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_storage_path(raw_path: StorageTarget) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = _project_root() / path
    return path.resolve()


def is_postgres_target(storage_target: StorageTarget) -> bool:
    return str(storage_target).startswith("postgresql://")


def normalize_storage_target(storage_target: StorageTarget) -> str:
    raw_target = str(storage_target).strip()
    if raw_target.startswith("postgresql://"):
        return raw_target
    for prefix in ("sqlite:///", "sqlite://"):
        if raw_target.startswith(prefix):
            return f"sqlite:///{resolve_storage_path(raw_target[len(prefix):])}"
    return str(resolve_storage_path(raw_target))


def resolve_sqlite_path(storage_target: StorageTarget) -> Path:
    raw_target = str(storage_target).strip()
    for prefix in ("sqlite:///", "sqlite://"):
        if raw_target.startswith(prefix):
            raw_target = raw_target[len(prefix):]
            break
    return resolve_storage_path(raw_target)


def derive_workflow_storage_target(checkpoint_target: StorageTarget) -> str:
    normalized = normalize_storage_target(checkpoint_target)
    if is_postgres_target(normalized):
        return normalized
    return str(resolve_sqlite_path(normalized).with_suffix(".langgraph.db"))


class SQLStorageBackend:
    def __init__(self, storage_target: StorageTarget) -> None:
        self.database_url = normalize_storage_target(storage_target)
        self.is_postgres = is_postgres_target(self.database_url)
        self.sqlite_path: Path | None = None
        self._pool = None
        if self.is_postgres:
            import psycopg2.pool

            self._pool = psycopg2.pool.SimpleConnectionPool(1, 10, self.database_url)
        else:
            self.sqlite_path = resolve_sqlite_path(self.database_url)
            self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect(self):
        if self.is_postgres:
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
            conn = sqlite3.connect(self.sqlite_path)
            try:
                yield _SqliteConn(conn)
                conn.commit()
            finally:
                conn.close()

    def close(self) -> None:
        if self._pool is not None:
            self._pool.closeall()


class _SqliteConn:
    __slots__ = ("_conn",)

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def execute(self, sql: str, params: tuple | list = ()) -> Any:
        return self._conn.execute(sql, params)


class _PgConn:
    __slots__ = ("_conn",)

    def __init__(self, conn: Any) -> None:
        self._conn = conn

    @staticmethod
    def _translate(sql: str) -> str:
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
        cursor = self._conn.cursor()
        cursor.execute(self._translate(sql), params)
        return cursor
