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
    assert "Dashboard 页面文案必须聚焦当前业务操作与结果反馈" in content
    assert "不要展示实现细节、数据来源限制、环境变量回显策略" in content


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


def test_dashboard_skill_management_mentions_zip_upload_flow():
    dashboard_root = Path(__file__).resolve().parents[2] / "dashboard"
    skill_editor = dashboard_root / "src" / "features" / "skills" / "SkillEditorSheet.tsx"
    skills_tab = dashboard_root / "src" / "features" / "skills" / "SkillsTab.tsx"
    readme = dashboard_root / "README.md"

    skill_editor_content = skill_editor.read_text(encoding="utf-8")
    skills_tab_content = skills_tab.read_text(encoding="utf-8")
    readme_content = readme.read_text(encoding="utf-8")

    assert 'type="file"' in skill_editor_content
    assert "zip" in skill_editor_content.lower()
    assert "归档" in skills_tab_content
    assert "zip" in readme_content.lower()


def test_dashboard_visible_copy_stays_focused_on_business_workflows():
    dashboard_root = Path(__file__).resolve().parents[2] / "dashboard" / "src"
    login_screen = (dashboard_root / "features" / "auth" / "LoginScreen.tsx").read_text(
        encoding="utf-8"
    )
    settings_tab = (dashboard_root / "features" / "settings" / "SettingsTab.tsx").read_text(
        encoding="utf-8"
    )
    app_shell = (dashboard_root / "app" / "AppShell.tsx").read_text(encoding="utf-8")
    app_model = (dashboard_root / "app" / "model.ts").read_text(encoding="utf-8")
    app_entry = (dashboard_root / "App.tsx").read_text(encoding="utf-8")

    forbidden_copy = [
        "dist / static",
        "Nginx",
        "same-origin",
        "Deployment",
        "部署信息",
        "静态前端",
        "AI 覆盖配置",
        "Dashboard 只负责覆盖写入或清除覆盖",
        "不展示已有数据库配置",
        "不会回显环境变量里的供应商",
        "每次进入页面表单都保持为空",
    ]

    for snippet in forbidden_copy:
        assert snippet not in login_screen
        assert snippet not in settings_tab
        assert snippet not in app_shell

    assert "gatewayLabel" not in login_screen
    assert "gatewayLabel" not in app_entry
    assert "Gateway:" not in app_shell
    assert "部署信息" not in app_model

    assert "统一查看任务、设备与技能状态" in login_screen
    assert "运行信息" in settings_tab
    assert "业务配置与账号范围" in app_model


def test_dashboard_settings_exposes_write_only_ai_override_entrypoints():
    dashboard_root = Path(__file__).resolve().parents[2] / "dashboard" / "src"
    settings_tab = (dashboard_root / "features" / "settings" / "SettingsTab.tsx").read_text(
        encoding="utf-8"
    )
    controller = (dashboard_root / "app" / "useDashboardController.ts").read_text(
        encoding="utf-8"
    )
    api = (dashboard_root / "api.ts").read_text(encoding="utf-8")

    assert "Gateway AI 覆盖" in settings_tab
    assert "CLI AI 覆盖" in settings_tab
    assert "saveGatewayAiConfig" in controller
    assert "saveDeviceAiConfig" in controller
    assert "/dashboard/api/ai/gateway" in api
    assert "/dashboard/api/ai/devices/" in api
