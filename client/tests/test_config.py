from client.config import ClientConfig


def test_client_config_defaults_to_local_sqlite_when_local_paths_are_unset(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://jarvis:pg-secret@db:5432/jarvis")
    monkeypatch.delenv("OMNI_AGENT_CHECKPOINT_DB", raising=False)
    monkeypatch.delenv("OMNI_AGENT_LANGGRAPH_DB", raising=False)

    config = ClientConfig.from_env()

    assert str(config.checkpoint_path).endswith("/client/client.db")
    assert str(config.workflow_store_path).endswith("/client/langgraph.db")


def test_client_config_accepts_explicit_postgres_storage_targets(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("OMNI_AGENT_CHECKPOINT_DB", "postgresql://jarvis:pg-secret@db:5432/jarvis")
    monkeypatch.setenv("OMNI_AGENT_LANGGRAPH_DB", "postgresql://jarvis:pg-secret@db:5432/jarvis")

    config = ClientConfig.from_env()

    assert config.checkpoint_path == "postgresql://jarvis:pg-secret@db:5432/jarvis"
    assert config.workflow_store_path == "postgresql://jarvis:pg-secret@db:5432/jarvis"
