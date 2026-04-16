import { startTransition } from "react";

import { tabs, type TabId } from "./model";
import { useDashboardController } from "./useDashboardController";
import { AssignmentSheet } from "../features/devices/AssignmentSheet";
import { AiCallDetailDialog } from "../features/ai-logs/AiCallDetailDialog";
import { AiCallsTab } from "../features/ai-logs/AiCallsTab";
import { ChatTab } from "../features/chat/ChatTab";
import { QuickDeployTab } from "../features/deploy/QuickDeployTab";
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

  function handleTabChange(tabId: TabId) {
    startTransition(() => {
      controller.selectTab(tabId);
    });
  }

  return (
    <>
      <div className="app-layout">
        <aside className="sidebar">
          <div className="sidebar-brand">
            <p className="eyebrow">OpenJarvis</p>
            <h1>Dashboard</h1>
            <p className="muted">任务编排、设备执行、审批闭环</p>
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
          {controller.bannerMessage ? (
            <div className="banner-error">{controller.bannerMessage}</div>
          ) : null}

          {controller.activeTab === "overview" ? (
            <OverviewTab overview={controller.overview} />
          ) : null}

          {controller.activeTab === "chat" ? (
            <ChatTab
              tasks={controller.tasks}
              selectedTask={controller.chatTask}
              selectedTaskId={controller.chatTaskId}
              targets={controller.chatTargets}
              selectedDeviceId={controller.chatDeviceId}
              gatewayAi={controller.systemInfo?.gateway_ai ?? null}
              clientAi={controller.systemInfo?.client_ai ?? []}
              onSelectTask={controller.selectChatTask}
              onSelectDevice={controller.selectChatDevice}
              onSendTask={controller.createChatTask}
              onSubmitDecision={controller.submitChatDecision}
              onDeleteTask={controller.deleteChatTask}
              onRefreshTasks={controller.refreshChatTasks}
            />
          ) : null}

          {controller.activeTab === "devices" ? (
            <DevicesTab
              devices={controller.devices}
              skills={controller.skills}
              onCreate={controller.openDeviceCreate}
              onEdit={controller.openDeviceEdit}
              onAssign={controller.openAssignment}
              onDelete={controller.removeDevice}
            />
          ) : null}

          {controller.activeTab === "quick-deploy" && controller.quickDeployDraft ? (
            <QuickDeployTab
              draft={controller.quickDeployDraft}
              form={controller.quickDeployForm}
              skills={controller.skills}
              busy={controller.quickDeployBusy}
              error={controller.quickDeployError}
              onFieldChange={controller.patchQuickDeployModuleValue}
              onClientPackageChange={controller.patchQuickDeployClientPackage}
              onToggleSkill={controller.toggleQuickDeploySkill}
              onSubmit={controller.downloadQuickDeployPackage}
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

          {controller.activeTab === "ai-calls" ? (
            <AiCallsTab
              calls={controller.aiCalls}
              selectedCallId={controller.selectedAiCallId}
              onOpenDetail={controller.selectAiCall}
              onRefresh={() => controller.refreshTab("ai-calls")}
            />
          ) : null}

          {controller.activeTab === "settings" ? (
            <SettingsTab
              systemInfo={controller.systemInfo}
              devices={controller.devices}
              gatewayAiSummary={controller.gatewayAiSummary}
              deviceAiSummary={
                controller.clientAiSummaries[controller.deviceAiForm.device_id] ?? null
              }
              gatewayAiForm={controller.gatewayAiForm}
              gatewayAiError={controller.gatewayAiError}
              gatewayAiTestMessage={controller.gatewayAiTestMessage}
              deviceAiForm={controller.deviceAiForm}
              deviceAiError={controller.deviceAiError}
              deviceAiTestMessage={controller.deviceAiTestMessage}
              onGatewayAiChange={controller.patchGatewayAiForm}
              onDeviceAiChange={controller.patchDeviceAiForm}
              onSaveGatewayAiConfig={controller.saveGatewayAiConfig}
              onSaveDeviceAiConfig={controller.saveDeviceAiConfig}
              onClearGatewayAiConfig={controller.clearGatewayAiConfig}
              onClearDeviceAiConfig={controller.clearDeviceAiConfig}
              onTestGatewayAiConfig={controller.testGatewayAiConfig}
              onTestDeviceAiConfig={controller.testDeviceAiConfig}
            />
          ) : null}
        </main>
      </div>

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

      {controller.aiCallDetail ? (
        <AiCallDetailDialog
          call={controller.aiCallDetail}
          onClose={() => controller.selectAiCall(null)}
        />
      ) : null}
    </>
  );
}
