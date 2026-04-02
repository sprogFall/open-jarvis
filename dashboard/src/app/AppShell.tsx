import { startTransition } from "react";

import { dashboardApi } from "../api";
import { tabs, type TabId } from "./model";
import { useDashboardController } from "./useDashboardController";
import { AssignmentSheet } from "../features/devices/AssignmentSheet";
import { DeviceEditorSheet } from "../features/devices/DeviceEditorSheet";
import { DevicesTab } from "../features/devices/DevicesTab";
import { OverviewTab } from "../features/overview/OverviewTab";
import { SettingsTab } from "../features/settings/SettingsTab";
import { SkillEditorSheet } from "../features/skills/SkillEditorSheet";
import { SkillsTab } from "../features/skills/SkillsTab";
import { TaskDetailSheet } from "../features/tasks/TaskDetailSheet";
import { TasksTab } from "../features/tasks/TasksTab";

type AppShellProps = {
  token: string;
  onLogout: () => void;
  onSessionExpired: (message: string) => void;
};

export function AppShell({
  token,
  onLogout,
  onSessionExpired,
}: AppShellProps) {
  const controller = useDashboardController({ token, onSessionExpired });
  const activeTab = tabs.find((tab) => tab.id === controller.activeTab);

  function handleTabChange(tabId: TabId) {
    startTransition(() => {
      controller.selectTab(tabId);
    });
  }

  return (
    <>
      <aside className="sidebar">
        <div className="sidebar-brand">
          <p className="eyebrow">OpenJarvis</p>
          <h1>Dashboard</h1>
          <p className="muted">独立静态前端 · 连接网关 API</p>
        </div>

        <nav className="tab-list">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={`tab-chip${controller.activeTab === tab.id ? " active" : ""}`}
              onClick={() => handleTabChange(tab.id)}
              type="button"
            >
              <span>{tab.label}</span>
              <small>{tab.hint}</small>
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div>
            <span className="live-dot" />
            <strong>{controller.refreshing ? "同步中" : "在线"}</strong>
          </div>
          <button className="ghost-button" onClick={onLogout} type="button">
            退出登录
          </button>
        </div>
      </aside>

      <main className="workspace">
        <header className="workspace-header">
          <div>
            <p className="eyebrow">Operational Surface</p>
            <h2>{activeTab?.label}</h2>
          </div>
          <div className="header-actions">
            <span className="signal-copy">
              Gateway: {dashboardApi.gatewayBaseUrl || "same-origin proxy"}
            </span>
            <button
              className="ghost-button"
              onClick={() => void controller.refreshTab()}
              type="button"
            >
              刷新
            </button>
          </div>
        </header>

        {controller.bannerMessage ? (
          <div className="banner-error">{controller.bannerMessage}</div>
        ) : null}

        {controller.activeTab === "overview" ? (
          <OverviewTab overview={controller.overview} />
        ) : null}

        {controller.activeTab === "devices" ? (
          <DevicesTab
            devices={controller.devices}
            onCreate={controller.openDeviceCreate}
            onEdit={controller.openDeviceEdit}
            onAssign={controller.openAssignment}
            onDelete={controller.removeDevice}
          />
        ) : null}

        {controller.activeTab === "skills" ? (
          <SkillsTab
            skills={controller.skills}
            onCreate={controller.openSkillCreate}
            onEdit={controller.openSkillEdit}
            onDelete={controller.removeSkill}
          />
        ) : null}

        {controller.activeTab === "tasks" ? (
          <TasksTab
            tasks={controller.tasks}
            devices={controller.devices}
            taskStatusFilter={controller.taskStatusFilter}
            taskDeviceFilter={controller.taskDeviceFilter}
            onStatusFilterChange={controller.setTaskStatusFilter}
            onDeviceFilterChange={controller.setTaskDeviceFilter}
            onRefresh={() => controller.refreshTab("tasks")}
            onSelectTask={controller.openTaskDetail}
          />
        ) : null}

        {controller.activeTab === "settings" ? (
          <SettingsTab systemInfo={controller.systemInfo} />
        ) : null}
      </main>

      {controller.deviceEditorMode ? (
        <DeviceEditorSheet
          mode={controller.deviceEditorMode}
          form={controller.deviceForm}
          error={controller.deviceFormError}
          onClose={controller.closeDeviceEditor}
          onSubmit={controller.saveDevice}
          onChange={controller.patchDeviceForm}
        />
      ) : null}

      {controller.skillEditorMode ? (
        <SkillEditorSheet
          mode={controller.skillEditorMode}
          form={controller.skillForm}
          error={controller.skillFormError}
          onClose={controller.closeSkillEditor}
          onSubmit={controller.saveSkill}
          onChange={controller.patchSkillForm}
        />
      ) : null}

      {controller.assignmentDevice ? (
        <AssignmentSheet
          device={controller.assignmentDevice}
          skills={controller.skills}
          form={controller.assignmentForm}
          error={controller.assignmentError}
          onClose={controller.closeAssignment}
          onSubmit={controller.submitAssignment}
          onChange={controller.patchAssignmentForm}
          onRemove={controller.removeAssignment}
        />
      ) : null}

      {controller.taskDetail ? (
        <TaskDetailSheet
          task={controller.taskDetail}
          onClose={controller.closeTaskDetail}
        />
      ) : null}
    </>
  );
}
