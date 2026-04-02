from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from gateway.main import create_app
from gateway.settings import GatewaySettings


def test_gateway_no_longer_serves_dashboard_page(tmp_path):
    settings = GatewaySettings(
        database_url=str(tmp_path / "gateway.db"),
        jwt_secret="test-secret-test-secret-test-secret",
    )
    client = TestClient(create_app(settings))

    response = client.get("/dashboard/")

    assert response.status_code == 404


def test_dashboard_is_packaged_as_npm_frontend_project():
    package_json = (
        Path(__file__).resolve().parents[2] / "dashboard" / "package.json"
    )

    package = json.loads(package_json.read_text(encoding="utf-8"))

    assert package["private"] is True
    assert "build" in package["scripts"]


def test_dashboard_contains_subpath_deployment_reference():
    deployment_doc = (
        Path(__file__).resolve().parents[2] / "dashboard" / "DEPLOYMENT.md"
    )

    content = deployment_doc.read_text(encoding="utf-8")

    assert "/jarvis/dashboard" in content
    assert "/jarvis/api" in content


def test_dashboard_frontend_is_split_into_feature_modules():
    root = Path(__file__).resolve().parents[2] / "dashboard" / "src"
    required_files = [
        root / "app" / "AppShell.tsx",
        root / "app" / "useDashboardController.ts",
        root / "components" / "SideSheet.tsx",
        root / "components" / "StatusPill.tsx",
        root / "features" / "auth" / "LoginScreen.tsx",
        root / "features" / "devices" / "DevicesTab.tsx",
        root / "features" / "skills" / "SkillsTab.tsx",
        root / "features" / "tasks" / "TasksTab.tsx",
        root / "features" / "overview" / "OverviewTab.tsx",
        root / "features" / "settings" / "SettingsTab.tsx",
        root / "lib" / "format.ts",
    ]

    missing = [str(path.relative_to(root.parent)) for path in required_files if not path.exists()]

    assert missing == []


def test_dashboard_app_entry_is_thin_after_refactor():
    app_file = Path(__file__).resolve().parents[2] / "dashboard" / "src" / "App.tsx"

    content = app_file.read_text(encoding="utf-8")

    assert len(content.splitlines()) < 220
    assert "useDashboardController" not in content
    assert "LoginScreen" in content
    assert "AppShell" in content


def test_agents_document_dashboard_frontend_conventions():
    agents_file = Path(__file__).resolve().parents[2] / "AGENTS.md"

    content = agents_file.read_text(encoding="utf-8")

    assert "Dashboard 前端开发规范" in content
    assert "src/features" in content
    assert "App.tsx 保持薄" in content


def test_dashboard_css_is_split_into_style_modules():
    src_root = Path(__file__).resolve().parents[2] / "dashboard" / "src"
    required_files = [
        src_root / "styles" / "index.css",
        src_root / "styles" / "tokens.css",
        src_root / "styles" / "base.css",
        src_root / "styles" / "layout.css",
        src_root / "styles" / "components.css",
        src_root / "styles" / "features.css",
        src_root / "styles" / "responsive.css",
    ]

    missing = [
        str(path.relative_to(src_root.parent)) for path in required_files if not path.exists()
    ]

    assert missing == []

    main_file = src_root / "main.tsx"
    content = main_file.read_text(encoding="utf-8")
    assert './styles/index.css' in content or "\"./styles/index.css\"" in content
