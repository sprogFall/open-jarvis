from client.config import ClientConfig


def test_client_config_reuses_shared_postgres_storage_when_local_paths_are_unset(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://jarvis:pg-secret@db:5432/jarvis")
    monkeypatch.delenv("OMNI_AGENT_CHECKPOINT_DB", raising=False)
    monkeypatch.delenv("OMNI_AGENT_LANGGRAPH_DB", raising=False)

    config = ClientConfig.from_env()

    assert config.checkpoint_path == "postgresql://jarvis:pg-secret@db:5432/jarvis"
    assert config.workflow_store_path == "postgresql://jarvis:pg-secret@db:5432/jarvis"


def test_client_config_keeps_local_sqlite_defaults_for_remote_gateway_deploy(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://jarvis:pg-secret@db:5432/jarvis")
    monkeypatch.setenv("OMNI_AGENT_GATEWAY_URL", "http://192.168.10.8:8000")
    monkeypatch.delenv("OMNI_AGENT_CHECKPOINT_DB", raising=False)
    monkeypatch.delenv("OMNI_AGENT_LANGGRAPH_DB", raising=False)

    config = ClientConfig.from_env()

    assert str(config.checkpoint_path).endswith("/client/client.db")
    assert str(config.workflow_store_path).endswith("/client/langgraph.db")
