from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def test_root_gitignore_restores_local_virtualenv_and_db_rules() -> None:
    gitignore = _read(".gitignore")

    assert ".venv/" in gitignore
    assert ".venv-sys/" in gitignore
    assert "*.db" in gitignore
    assert "*.db-shm" in gitignore
    assert "*.db-wal" in gitignore


def test_root_gitignore_keeps_env_examples_trackable() -> None:
    gitignore = _read(".gitignore")

    assert "*.env.*" in gitignore
    assert "!.env.example" in gitignore
    assert "!**/.env.example" in gitignore
    assert "```" not in gitignore
