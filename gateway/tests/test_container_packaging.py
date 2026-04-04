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


def test_client_china_dockerfile_uses_cn_mirrors():
    client_dockerfile = _read("client/Dockerfile.cn")
    root_readme = _read("README.md")
    compose = _read("docker-compose.yml")
    env_example = _read(".env.example")

    assert "ARG APT_MIRROR_HOST=mirrors.tuna.tsinghua.edu.cn" in client_dockerfile
    assert "ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple" in client_dockerfile
    assert "ARG PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn" in client_dockerfile
    assert "/etc/apt/sources.list.d/debian.sources" in client_dockerfile
    assert "pip install -r /tmp/client-requirements.txt" in client_dockerfile
    assert "client/Dockerfile.cn" in root_readme
    assert "${CLIENT_DOCKERFILE:-client/Dockerfile}" in compose
    assert "CLIENT_DOCKERFILE=client/Dockerfile" in env_example


def test_gateway_china_dockerfile_uses_cn_mirrors():
    gateway_dockerfile = _read("gateway/Dockerfile.cn")
    root_readme = _read("README.md")
    compose = _read("docker-compose.yml")
    env_example = _read(".env.example")

    assert "ARG APT_MIRROR_HOST=mirrors.tuna.tsinghua.edu.cn" in gateway_dockerfile
    assert "ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple" in gateway_dockerfile
    assert "ARG PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn" in gateway_dockerfile
    assert "/etc/apt/sources.list.d/debian.sources" in gateway_dockerfile
    assert "pip install -r /tmp/gateway-requirements.txt -r /tmp/client-requirements.txt" in gateway_dockerfile
    assert "gateway/Dockerfile.cn" in root_readme
    assert "${GATEWAY_DOCKERFILE:-gateway/Dockerfile}" in compose
    assert "GATEWAY_DOCKERFILE=gateway/Dockerfile" in env_example


def test_dashboard_china_dockerfile_uses_cn_registry_and_compose_support():
    dashboard_dockerfile = _read("dashboard/Dockerfile.cn")
    root_readme = _read("README.md")
    compose = _read("docker-compose.yml")
    env_example = _read(".env.example")

    assert "ARG NPM_REGISTRY=https://registry.npmmirror.com" in dashboard_dockerfile
    assert 'npm config set registry "${NPM_REGISTRY}"' in dashboard_dockerfile
    assert "npm ci" in dashboard_dockerfile
    assert "dashboard/Dockerfile.cn" in root_readme
    assert "${DASHBOARD_DOCKERFILE:-dashboard/Dockerfile}" in compose
    assert 'NPM_REGISTRY: ${DASHBOARD_NPM_REGISTRY:-}' in compose
    assert "DASHBOARD_DOCKERFILE=dashboard/Dockerfile" in env_example
    assert "DASHBOARD_NPM_REGISTRY=" in env_example


def test_dashboard_container_is_built_from_repo_sources():
    dockerfile = _read("dashboard/Dockerfile")
    nginx_conf = _read("dashboard/nginx.conf")

    assert "FROM node:" in dockerfile
    assert "ARG NPM_REGISTRY=" in dockerfile
    assert 'if [ -n "${NPM_REGISTRY}" ]; then npm config set registry "${NPM_REGISTRY}"; fi' in dockerfile
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
