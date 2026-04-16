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
        root / "features" / "deploy" / "QuickDeployTab.tsx",
        root / "features" / "devices" / "DevicesTab.tsx",
        root / "features" / "skills" / "SkillsTab.tsx",
        root / "features" / "tasks" / "TasksTab.tsx",
        root / "features" / "ai-logs" / "AiCallsTab.tsx",
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
    assert "弹层、抽屉、长表单与长列表必须保证内容完整可见" in content
    assert "必要时提供内部滚动" in content


def test_agents_document_dashboard_api_response_whitelist_rules():
    agents_file = Path(__file__).resolve().parents[2] / "AGENTS.md"

    content = agents_file.read_text(encoding="utf-8")

    assert "接口返回必须采用白名单 DTO" in content
    assert "默认禁止透出数据库连接串" in content
    assert "设备密钥" in content


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


def test_dashboard_selects_define_readable_popup_option_styles():
    components_css = (
        Path(__file__).resolve().parents[2]
        / "dashboard"
        / "src"
        / "styles"
        / "components.css"
    ).read_text(encoding="utf-8")

    assert ".field select option" in components_css
    assert ".task-filters select option" in components_css
    assert "background-color: var(--panel-strong)" in components_css
    assert "color: var(--text)" in components_css
    assert "select option:checked" in components_css
    assert "select option:hover" in components_css


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


def test_dashboard_exposes_independent_quick_deploy_workspace():
    dashboard_root = Path(__file__).resolve().parents[2] / "dashboard"
    deploy_tab = dashboard_root / "src" / "features" / "deploy" / "QuickDeployTab.tsx"
    app_model = dashboard_root / "src" / "app" / "model.ts"
    app_shell = dashboard_root / "src" / "app" / "AppShell.tsx"
    controller = dashboard_root / "src" / "app" / "useDashboardController.ts"
    api = dashboard_root / "src" / "api.ts"
    readme = dashboard_root / "README.md"

    deploy_tab_content = deploy_tab.read_text(encoding="utf-8")
    app_model_content = app_model.read_text(encoding="utf-8")
    app_shell_content = app_shell.read_text(encoding="utf-8")
    controller_content = controller.read_text(encoding="utf-8")
    api_content = api.read_text(encoding="utf-8")
    readme_content = readme.read_text(encoding="utf-8")

    assert deploy_tab.exists()
    assert 'label: "快速部署"' in app_model_content
    assert "QuickDeployTab" in app_shell_content
    assert "CLI 快速部署" in deploy_tab_content
    assert "quickDeployDraft" in controller_content
    assert "downloadQuickDeployPackage" in controller_content
    assert "getQuickDeployDraft" in api_content
    assert "downloadQuickDeployPackage" in api_content
    assert "快速部署" in readme_content


def test_dashboard_quick_deploy_copy_stays_focused_on_cli_delivery():
    dashboard_root = Path(__file__).resolve().parents[2] / "dashboard"
    deploy_tab = (dashboard_root / "src" / "features" / "deploy" / "QuickDeployTab.tsx").read_text(
        encoding="utf-8"
    )
    app_model = (dashboard_root / "src" / "app" / "model.ts").read_text(encoding="utf-8")
    readme = (dashboard_root / "README.md").read_text(encoding="utf-8")

    assert 'label: "快速部署"' in app_model
    assert 'hint: "CLI 部署包与接入配置"' in app_model

    assert "CLI 快速部署" in deploy_tab
    assert "Client 部署包" in deploy_tab
    assert "Gateway / Client / Dashboard" not in deploy_tab
    assert "quick-target-row" not in deploy_tab
    assert "onToggleTarget" not in deploy_tab
    assert "目标模块" not in deploy_tab
    assert "Gateway 端口" not in deploy_tab
    assert "Dashboard 端口" not in deploy_tab

    assert "CLI 快速部署" in readme
    assert "按 `Gateway / Client / Dashboard` 勾选目标模块" not in readme
    assert "下载 zip 后可分别进入 `gateway/`、`client/`、`dashboard/` 目录独立部署" not in readme


def test_dashboard_visible_copy_stays_focused_on_business_workflows():
    dashboard_root = Path(__file__).resolve().parents[2] / "dashboard" / "src"
    login_screen = (dashboard_root / "features" / "auth" / "LoginScreen.tsx").read_text(
        encoding="utf-8"
    )
    settings_tab = (dashboard_root / "features" / "settings" / "SettingsTab.tsx").read_text(
        encoding="utf-8"
    )
    chat_tab = (dashboard_root / "features" / "chat" / "ChatTab.tsx").read_text(
        encoding="utf-8"
    )
    devices_tab = (dashboard_root / "features" / "devices" / "DevicesTab.tsx").read_text(
        encoding="utf-8"
    )
    device_editor = (
        dashboard_root / "features" / "devices" / "DeviceEditorSheet.tsx"
    ).read_text(encoding="utf-8")
    assignment_sheet = (
        dashboard_root / "features" / "devices" / "AssignmentSheet.tsx"
    ).read_text(encoding="utf-8")
    skills_tab = (dashboard_root / "features" / "skills" / "SkillsTab.tsx").read_text(
        encoding="utf-8"
    )
    skill_editor = (
        dashboard_root / "features" / "skills" / "SkillEditorSheet.tsx"
    ).read_text(encoding="utf-8")
    quick_deploy_tab = (
        dashboard_root / "features" / "deploy" / "QuickDeployTab.tsx"
    ).read_text(encoding="utf-8")
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
        "聊天页改为手动同步，避免打断当前输入。",
        "新对话时不会自动切走当前输入。",
        "Gateway 配置会作为 CLI 的默认模型来源",
        "设备注册信息会直接写入网关持久化存储。",
        "已分配的内建 Skill 会直接暴露给 AI；归档 Skill 会通过 Gateway 同步并在设备侧解压。",
        "快速部署入口已收敛到独立菜单。",
        "下载包内会包含",
        "生成时写入 Gateway 设备表",
        "在同一条线程里查看审批、恢复状态和执行日志；需要特殊模型时再为 CLI 单独覆盖。",
        "请先在系统页配置 Gateway 默认 AI，或为特定 CLI 设置覆盖。",
    ]

    for snippet in forbidden_copy:
        assert snippet not in login_screen
        assert snippet not in settings_tab
        assert snippet not in chat_tab
        assert snippet not in devices_tab
        assert snippet not in device_editor
        assert snippet not in assignment_sheet
        assert snippet not in skills_tab
        assert snippet not in skill_editor
        assert snippet not in quick_deploy_tab
        assert snippet not in app_shell

    assert "gatewayLabel" not in login_screen
    assert "gatewayLabel" not in app_entry
    assert "Gateway:" not in app_shell
    assert "部署信息" not in app_model

    assert "统一查看任务、设备与技能状态" in login_screen
    assert "运行信息" in settings_tab
    assert "业务配置与账号范围" in app_model
    assert "维护默认 AI 与设备专用 AI 设置。" not in settings_tab
    assert "查看最新任务进展" not in chat_tab
    assert "维护设备注册、在线状态与 Skill 分配。" not in devices_tab
    assert "填写设备基本信息。" in device_editor
    assert "选择 Skill 并填写分配参数。" in assignment_sheet
    assert "维护内建与自定义 Skill。" not in skills_tab
    assert "上传归档并维护 Skill 信息。" in skill_editor
    assert "生成 CLI 设备部署包，可选登记设备与 Skill。" not in quick_deploy_tab
    assert "聊天任务" in chat_tab
    assert "会话框" in chat_tab


def test_dashboard_settings_exposes_write_only_ai_override_entrypoints():
    dashboard_root = Path(__file__).resolve().parents[2] / "dashboard" / "src"
    settings_tab = (dashboard_root / "features" / "settings" / "SettingsTab.tsx").read_text(
        encoding="utf-8"
    )
    controller = (dashboard_root / "app" / "useDashboardController.ts").read_text(
        encoding="utf-8"
    )
    api = (dashboard_root / "api.ts").read_text(encoding="utf-8")

    assert "Gateway AI 默认配置" in settings_tab
    assert "CLI 特殊覆盖" in settings_tab
    assert "当前生效配置" in settings_tab
    assert "API Key（掩码）" in settings_tab
    assert "saveGatewayAiConfig" in controller
    assert "saveDeviceAiConfig" in controller
    assert "/dashboard/api/ai/gateway" in api
    assert "/dashboard/api/ai/devices/" in api


def test_dashboard_exposes_ai_call_log_workspace_and_ai_test_actions():
    dashboard_root = Path(__file__).resolve().parents[2] / "dashboard" / "src"
    app_model = (dashboard_root / "app" / "model.ts").read_text(encoding="utf-8")
    app_shell = (dashboard_root / "app" / "AppShell.tsx").read_text(encoding="utf-8")
    controller = (dashboard_root / "app" / "useDashboardController.ts").read_text(
        encoding="utf-8"
    )
    settings_tab = (dashboard_root / "features" / "settings" / "SettingsTab.tsx").read_text(
        encoding="utf-8"
    )
    api = (dashboard_root / "api.ts").read_text(encoding="utf-8")

    assert 'label: "AI 调用"' in app_model
    assert "AiCallsTab" in app_shell
    assert "测试当前默认" in settings_tab
    assert "测试当前设备配置" in settings_tab
    assert "testGatewayAiConfig" in controller
    assert "testDeviceAiConfig" in controller
    assert "listAiCallLogs" in controller
    assert "/dashboard/api/ai/calls" in api
    assert "/dashboard/api/ai/test/gateway" in api
    assert "/dashboard/api/ai/test/devices/" in api


def test_dashboard_settings_guards_missing_ai_summary_fields():
    settings_tab = (
        Path(__file__).resolve().parents[2]
        / "dashboard"
        / "src"
        / "features"
        / "settings"
        / "SettingsTab.tsx"
    ).read_text(encoding="utf-8")

    assert "systemInfo?.client_ai.length" not in settings_tab
    assert "?? []" in settings_tab


def test_dashboard_sheet_styles_keep_long_content_fully_visible():
    dashboard_root = Path(__file__).resolve().parents[2] / "dashboard" / "src"
    layout_css = (dashboard_root / "styles" / "layout.css").read_text(encoding="utf-8")

    assert ".sheet-panel" in layout_css
    assert "max-height: 100vh" in layout_css
    assert "overflow: hidden" in layout_css
    assert ".sheet-body" in layout_css
    assert "overflow-y: auto" in layout_css


def test_dashboard_chat_workspace_uses_single_visual_language():
    dashboard_root = Path(__file__).resolve().parents[2] / "dashboard" / "src"
    features_css = (dashboard_root / "styles" / "features.css").read_text(encoding="utf-8")

    assert ".chat-stage" in features_css
    assert "grid-template-rows: auto minmax(0, 1fr) auto" in features_css
    assert ".chat-conversation" in features_css
    assert ".chat-thread-list" in features_css

    legacy_chat_selectors = [
        ".chat-summary",
        ".thread-item",
        ".bubble,",
        ".approval-card,",
        ".result-panel,",
        ".welcome-panel",
        ".chat-transcript",
        ".prompt-chip",
    ]

    for selector in legacy_chat_selectors:
        assert selector not in features_css


def test_dashboard_workspace_shell_removes_redundant_tab_copy_and_global_sync_actions():
    app_shell = (
        Path(__file__).resolve().parents[2] / "dashboard" / "src" / "app" / "AppShell.tsx"
    ).read_text(encoding="utf-8")

    assert "workspace-title-group" not in app_shell
    assert "activeTab?.hint" not in app_shell
    assert "workspace-sync" not in app_shell
    assert 'controller.refreshTab()' not in app_shell
    assert "Workspace" not in app_shell


def test_dashboard_chat_supports_manual_delete_task_refresh_and_live_conversation_updates():
    dashboard_root = Path(__file__).resolve().parents[2] / "dashboard" / "src"
    chat_tab = (dashboard_root / "features" / "chat" / "ChatTab.tsx").read_text(
        encoding="utf-8"
    )
    controller = (dashboard_root / "app" / "useDashboardController.ts").read_text(
        encoding="utf-8"
    )
    api = (dashboard_root / "api.ts").read_text(encoding="utf-8")

    assert "删除记录" in chat_tab
    assert "onDeleteTask" in chat_tab
    assert "实时同步中" not in chat_tab
    assert "刷新任务" in chat_tab
    assert "手动同步" not in chat_tab
    assert "新对话时不会自动切走当前输入。" not in chat_tab
    assert "查看最新任务进展" not in chat_tab
    assert "会话框" in chat_tab
    assert "EventSource" not in controller
    assert "refreshChatConversation" in controller
    assert "getTask(token, taskId)" in controller
    assert "TASK_HISTORY_SYNC" not in controller
    assert "TASK_SNAPSHOT" not in controller
    assert "TASK_LOG" not in controller
    assert "getTask(" in api
    assert "deleteTask(" in api
    assert "/tasks/${taskId}" in api


def test_dashboard_extracts_shared_ui_primitives_for_metrics_and_detail_blocks():
    src_root = Path(__file__).resolve().parents[2] / "dashboard" / "src"
    section_header = src_root / "components" / "SectionHeader.tsx"
    form_field = src_root / "components" / "FormField.tsx"
    metric_card = src_root / "components" / "MetricCard.tsx"
    key_value_grid = src_root / "components" / "KeyValueGrid.tsx"

    assert section_header.exists()
    assert form_field.exists()
    assert metric_card.exists()
    assert key_value_grid.exists()

    overview_tab = (src_root / "features" / "overview" / "OverviewTab.tsx").read_text(
        encoding="utf-8"
    )
    settings_tab = (src_root / "features" / "settings" / "SettingsTab.tsx").read_text(
        encoding="utf-8"
    )
    devices_sheet = (src_root / "features" / "devices" / "AssignmentSheet.tsx").read_text(
        encoding="utf-8"
    )

    assert "SectionHeader" in overview_tab
    assert "MetricCard" in overview_tab
    assert "SectionHeader" in settings_tab
    assert "KeyValueGrid" in settings_tab
    assert "FormField" in settings_tab
    assert "KeyValueGrid" in devices_sheet


def test_dashboard_accessibility_and_motion_guards_are_centralized():
    src_root = Path(__file__).resolve().parents[2] / "dashboard" / "src"
    side_sheet = (src_root / "components" / "SideSheet.tsx").read_text(encoding="utf-8")
    base_css = (src_root / "styles" / "base.css").read_text(encoding="utf-8")
    components_css = (src_root / "styles" / "components.css").read_text(encoding="utf-8")

    assert 'role="dialog"' in side_sheet
    assert 'aria-modal="true"' in side_sheet
    assert "aria-labelledby" in side_sheet
    assert "@media (prefers-reduced-motion: reduce)" in base_css
    assert ":focus-visible" in components_css


def test_agents_document_shared_ui_primitives_and_app_shell_rules():
    agents_file = Path(__file__).resolve().parents[2] / "AGENTS.md"
    content = agents_file.read_text(encoding="utf-8")

    assert "同类页面头部、统计卡、键值信息块、表单标签必须优先抽成共享组件" in content
    assert "Dashboard 必须统一提供 `:focus-visible` 与 `prefers-reduced-motion` 兜底" in content
    assert "新增或修改 `select`、下拉菜单、PopupMenu 或 Dropdown 后" in content
    assert "必须检查展开态的选项面板在当前主题下是否清晰可读" in content
    assert "禁止出现选项文字与背景混色、透明叠底或 hover / selected 态不可辨认的问题" in content
    assert "App 端聊天首页只保留一个一等壳层实现" in content
    assert "`home_screen.dart` 仅保留入口包装职责" in content
