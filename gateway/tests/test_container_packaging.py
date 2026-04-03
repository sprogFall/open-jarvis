from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def test_gateway_and_client_dockerfiles_bundle_runtime_dependencies():
    gateway_dockerfile = _read("gateway/Dockerfile")
    client_dockerfile = _read("client/Dockerfile")

    assert "COPY gateway /app/gateway" in gateway_dockerfile
    assert "COPY client /app/client" in gateway_dockerfile
    assert "COPY skill_catalog.py /app/skill_catalog.py" in gateway_dockerfile
    assert "gateway/requirements.txt" in gateway_dockerfile
    assert "client/requirements.txt" in gateway_dockerfile
    assert "docker.io" in gateway_dockerfile
    assert "bash" in gateway_dockerfile
    assert "procps" in gateway_dockerfile

    assert "COPY client /app/client" in client_dockerfile
    assert "COPY skill_catalog.py /app/skill_catalog.py" in client_dockerfile
    assert "docker.io" in client_dockerfile
    assert "bash" in client_dockerfile
    assert "procps" in client_dockerfile



def test_dashboard_container_is_built_from_repo_sources():
    dockerfile = _read("dashboard/Dockerfile")
    nginx_conf = _read("dashboard/nginx.conf")

    assert "FROM node:" in dockerfile
    assert "npm ci" in dockerfile
    assert "npm run build" in dockerfile
    assert "FROM nginx:" in dockerfile
    assert "VITE_GATEWAY_BASE_URL" in dockerfile
    assert "dashboard/nginx.conf" in dockerfile

    assert "location /jarvis/dashboard/" in nginx_conf
    assert "location /jarvis/api/" in nginx_conf
    assert "proxy_set_header Upgrade $http_upgrade;" in nginx_conf
    assert "proxy_set_header Connection \"upgrade\";" in nginx_conf



def test_compose_stack_can_boot_from_clone_without_external_database_or_static_host():
    compose = _read("docker-compose.yml")

    for service_name in ("postgres:", "gateway:", "client:", "dashboard:"):
        assert service_name in compose

    assert "gateway/Dockerfile" in compose
    assert "client/Dockerfile" in compose
    assert "dashboard/Dockerfile" in compose
    assert "postgres:16-alpine" in compose
    assert "postgresql://${POSTGRES_USER:-jarvis}:${POSTGRES_PASSWORD:-jarvis}@postgres:5432/${POSTGRES_DB:-jarvis}" in compose
    assert "condition: service_healthy" in compose
    assert "./:/workspace:ro" in compose
    assert "/var/run/docker.sock:/var/run/docker.sock" in compose
    assert "${DASHBOARD_PORT:-8080}:80" in compose



def test_deployment_docs_describe_one_command_container_bootstrap():
    root_readme = _read("README.md")
    dashboard_deployment = _read("dashboard/DEPLOYMENT.md")
    dockerignore = _read(".dockerignore")

    assert "docker compose up --build -d" in root_readme
    assert "dashboard" in root_readme
    assert "postgres" in root_readme.lower()
    assert "Flutter App 仍需单独运行" in root_readme

    assert "dashboard/Dockerfile" in dashboard_deployment
    assert "/jarvis/dashboard/" in dashboard_deployment
    assert "/jarvis/api" in dashboard_deployment
    assert "docker compose up --build -d" in dashboard_deployment

    assert "dashboard/node_modules" in dockerignore
    assert "dashboard/dist" in dockerignore
