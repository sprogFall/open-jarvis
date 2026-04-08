import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";

import { dashboardApi } from "../api";
import {
  createEmptyClientDeploymentForm,
  createEmptyDeviceAiForm,
  createEmptyAssignmentForm,
  createEmptyDeviceForm,
  createEmptyGatewayAiForm,
  createEmptyQuickDeployForm,
  createEmptySkillForm,
  type AssignmentForm,
  type ClientDeploymentForm,
  type DeviceAiForm,
  type DeviceForm,
  type GatewayAiForm,
  type QuickDeployForm,
  type SkillForm,
  type TabId,
} from "./model";
import { getErrorMessage } from "../lib/format";
import { parseJsonInput } from "../lib/json";
import type {
  AICallLog,
  AIConfigSummary,
  Device,
  DeviceSkill,
  Overview,
  QuickDeployDraft,
  QuickDeployModuleId,
  Skill,
  SystemInfo,
  Task,
} from "../types";

type UseDashboardControllerArgs = {
  token: string;
  onSessionExpired: (message: string) => void;
};

type ChatTarget = {
  device_id: string;
  name: string;
  type: string;
  connected: boolean;
  label: string;
};

const GATEWAY_LOCAL_DEVICE_ID = "gateway-local";

function mergeTask(current: Task | undefined, incoming: Task): Task {
  return {
    ...current,
    ...incoming,
    logs: incoming.logs.length ? incoming.logs : current?.logs ?? [],
  };
}

function upsertTask(tasks: Task[], incoming: Task): Task[] {
  const existing = tasks.find((task) => task.task_id === incoming.task_id);
  const merged = mergeTask(existing, incoming);
  return [merged, ...tasks.filter((task) => task.task_id !== incoming.task_id)];
}

function replaceTasks(current: Task[], incoming: Task[]): Task[] {
  return incoming.map((task) => mergeTask(
    current.find((existing) => existing.task_id === task.task_id),
    task,
  ));
}

function appendTaskLog(tasks: Task[], taskId: string, message: string): Task[] {
  return tasks.map((task) => (
    task.task_id === taskId
      ? { ...task, logs: [...task.logs, message] }
      : task
  ));
}

function removeTask(tasks: Task[], taskId: string): Task[] {
  return tasks.filter((task) => task.task_id !== taskId);
}

function isTaskDeletable(task: Task): boolean {
  return task.status === "COMPLETED" || task.status === "FAILED" || task.status === "REJECTED";
}

function buildChatTargets(devices: Device[]): ChatTarget[] {
  return [
    {
      device_id: GATEWAY_LOCAL_DEVICE_ID,
      name: "Gateway 本机",
      type: "gateway",
      connected: true,
      label: "Gateway 本机",
    },
    ...devices
      .filter((device) => device.type === "cli")
      .map((device) => ({
        device_id: device.device_id,
        name: device.name,
        type: device.type,
        connected: device.connected,
        label: `${device.name} (${device.device_id})`,
      })),
  ];
}

function pickChatTaskId(tasks: Task[], current: string | null): string | null {
  if (current && tasks.some((task) => task.task_id === current)) {
    return current;
  }
  const awaiting = tasks.find((task) => task.status === "AWAITING_APPROVAL");
  return awaiting?.task_id ?? tasks[0]?.task_id ?? null;
}

function pickChatDeviceId(targets: ChatTarget[], current: string): string {
  if (current && targets.some((target) => target.device_id === current)) {
    return current;
  }
  return targets[0]?.device_id ?? "";
}

function pickAiCallId(calls: AICallLog[], current: string | null): string | null {
  if (current && calls.some((call) => call.call_id === current)) {
    return current;
  }
  return calls[0]?.call_id ?? null;
}

function summarizeAiTestResponse(response: Record<string, unknown>): string {
  const summary = response.summary;
  if (typeof summary === "string" && summary.trim()) {
    return summary.trim();
  }
  return JSON.stringify(response, null, 2);
}

function isSessionExpiredMessage(message: string): boolean {
  return (
    message.includes("401")
    || message.includes("未登录")
    || message.includes("登录已过期")
  );
}

function suggestGatewayUrl(): string {
  try {
    if (!dashboardApi.gatewayBaseUrl) {
      return "";
    }
    return new URL(dashboardApi.gatewayBaseUrl, window.location.origin).toString().replace(/\/+$/, "");
  } catch {
    return "";
  }
}

function suggestDashboardGatewayBaseUrl(): string {
  return dashboardApi.gatewayBaseUrl || "";
}

function triggerFileDownload(blob: Blob, filename: string) {
  const objectUrl = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = filename;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  window.URL.revokeObjectURL(objectUrl);
}

export function useDashboardController({
  token,
  onSessionExpired,
}: UseDashboardControllerArgs) {
  const [activeTab, setActiveTab] = useState<TabId>("overview");
  const [bannerMessage, setBannerMessage] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const [overview, setOverview] = useState<Overview | null>(null);
  const [devices, setDevices] = useState<Device[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [aiCalls, setAiCalls] = useState<AICallLog[]>([]);
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);

  const [taskStatusFilter, setTaskStatusFilter] = useState("");
  const [taskDeviceFilter, setTaskDeviceFilter] = useState("");
  const [chatTaskId, setChatTaskId] = useState<string | null>(null);
  const [selectedAiCallId, setSelectedAiCallId] = useState<string | null>(null);
  const [chatDeviceId, setChatDeviceId] = useState<string>(GATEWAY_LOCAL_DEVICE_ID);
  const [chatSocketState, setChatSocketState] = useState<"connecting" | "connected" | "offline">(
    "offline",
  );

  const [deviceEditorMode, setDeviceEditorMode] = useState<"create" | "edit" | null>(null);
  const [deviceForm, setDeviceForm] = useState<DeviceForm>(createEmptyDeviceForm());
  const [deviceFormError, setDeviceFormError] = useState<string | null>(null);

  const [skillEditorMode, setSkillEditorMode] = useState<"create" | "edit" | null>(null);
  const [skillForm, setSkillForm] = useState<SkillForm>(createEmptySkillForm());
  const [skillFormError, setSkillFormError] = useState<string | null>(null);

  const [assignmentDevice, setAssignmentDevice] = useState<Device | null>(null);
  const [assignmentForm, setAssignmentForm] = useState<AssignmentForm>(
    createEmptyAssignmentForm(),
  );
  const [assignmentError, setAssignmentError] = useState<string | null>(null);
  const [gatewayAiForm, setGatewayAiForm] = useState<GatewayAiForm>(createEmptyGatewayAiForm());
  const [gatewayAiError, setGatewayAiError] = useState<string | null>(null);
  const [gatewayAiTestMessage, setGatewayAiTestMessage] = useState<string | null>(null);
  const [deviceAiForm, setDeviceAiForm] = useState<DeviceAiForm>(createEmptyDeviceAiForm());
  const [deviceAiError, setDeviceAiError] = useState<string | null>(null);
  const [deviceAiTestMessage, setDeviceAiTestMessage] = useState<string | null>(null);
  const [clientBootstrapOpen, setClientBootstrapOpen] = useState(false);
  const [clientBootstrapBusy, setClientBootstrapBusy] = useState(false);
  const [clientBootstrapForm, setClientBootstrapForm] = useState<ClientDeploymentForm>(
    createEmptyClientDeploymentForm(suggestGatewayUrl()),
  );
  const [clientBootstrapError, setClientBootstrapError] = useState<string | null>(null);
  const [quickDeployDraft, setQuickDeployDraft] = useState<QuickDeployDraft | null>(null);
  const [quickDeployForm, setQuickDeployForm] = useState<QuickDeployForm>(
    createEmptyQuickDeployForm(
      null,
      suggestGatewayUrl(),
      suggestDashboardGatewayBaseUrl(),
    ),
  );
  const [quickDeployBusy, setQuickDeployBusy] = useState(false);
  const [quickDeployError, setQuickDeployError] = useState<string | null>(null);

  const [taskDetail, setTaskDetail] = useState<Task | null>(null);

  const chatTargets = useMemo(() => buildChatTargets(devices), [devices]);
  const chatTask = tasks.find((task) => task.task_id === chatTaskId) ?? null;
  const aiCallDetail = aiCalls.find((call) => call.call_id === selectedAiCallId) ?? null;
  const gatewayAiSummary: AIConfigSummary | null = systemInfo?.gateway_ai ?? null;
  const clientAiSummaries = useMemo(() => {
    return Object.fromEntries(
      (systemInfo?.client_ai ?? []).map((summary) => [summary.device_id ?? "", summary]),
    ) as Record<string, AIConfigSummary>;
  }, [systemInfo?.client_ai]);

  function handleApiError(error: unknown) {
    const message = getErrorMessage(error);
    if (isSessionExpiredMessage(message)) {
      onSessionExpired("登录状态已失效，请重新登录");
      return;
    }
    setBannerMessage(message);
  }

  async function refreshSystemInfo() {
    const nextSystemInfo = await dashboardApi.getSystemInfo(token);
    setSystemInfo(nextSystemInfo);
  }

  async function refreshAiCalls() {
    const nextCalls = await dashboardApi.listAiCallLogs(token, { limit: 100 });
    setAiCalls(nextCalls);
    setSelectedAiCallId((current) => pickAiCallId(nextCalls, current));
  }

  async function refreshQuickDeployDraft(resetForm: boolean = false) {
    const nextDraft = await dashboardApi.getQuickDeployDraft(token);
    setQuickDeployDraft(nextDraft);
    if (resetForm) {
      setQuickDeployForm(
        createEmptyQuickDeployForm(
          nextDraft,
          suggestGatewayUrl(),
          suggestDashboardGatewayBaseUrl(),
        ),
      );
      setQuickDeployError(null);
    }
  }

  async function refreshChatData() {
    const [nextDevices, nextTasks, nextSystemInfo] = await Promise.all([
      dashboardApi.listDevices(token),
      dashboardApi.listTasks(token, {}),
      dashboardApi.getSystemInfo(token),
    ]);
    setDevices(nextDevices);
    setTasks((current) => replaceTasks(current, nextTasks));
    setSystemInfo(nextSystemInfo);
    const nextTargets = buildChatTargets(nextDevices);
    setChatDeviceId((current) => pickChatDeviceId(nextTargets, current));
    setChatTaskId((current) => pickChatTaskId(nextTasks, current));
  }

  useEffect(() => {
    const activeToken = token;
    let cancelled = false;

    async function bootstrap() {
      setRefreshing(true);
      try {
        const [
          nextOverview,
          nextDevices,
          nextSkills,
          nextTasks,
          nextSystemInfo,
          nextQuickDeployDraft,
        ] =
          await Promise.all([
            dashboardApi.getOverview(activeToken),
            dashboardApi.listDevices(activeToken),
            dashboardApi.listSkills(activeToken),
            dashboardApi.listTasks(activeToken, {}),
            dashboardApi.getSystemInfo(activeToken),
            dashboardApi.getQuickDeployDraft(activeToken),
          ]);
        if (cancelled) {
          return;
        }
        setOverview(nextOverview);
        setDevices(nextDevices);
        setSkills(nextSkills);
        setTasks((current) => replaceTasks(current, nextTasks));
        setSystemInfo(nextSystemInfo);
        setQuickDeployDraft(nextQuickDeployDraft);
        setQuickDeployForm(
          createEmptyQuickDeployForm(
            nextQuickDeployDraft,
            suggestGatewayUrl(),
            suggestDashboardGatewayBaseUrl(),
          ),
        );
        const nextTargets = buildChatTargets(nextDevices);
        setChatTaskId((current) => pickChatTaskId(nextTasks, current));
        setChatDeviceId((current) => pickChatDeviceId(nextTargets, current));
        setBannerMessage(null);
      } catch (error) {
        if (!cancelled) {
          handleApiError(error);
        }
      } finally {
        if (!cancelled) {
          setRefreshing(false);
        }
      }
    }

    void bootstrap();
    return () => {
      cancelled = true;
    };
  }, [onSessionExpired, token]);

  useEffect(() => {
    let cancelled = false;

    async function refreshCurrentTab() {
      try {
        const nextOverview = await dashboardApi.getOverview(token);
        if (cancelled) {
          return;
        }
        setOverview(nextOverview);

        if (activeTab === "chat") {
          await refreshChatData();
        }

        if (activeTab === "devices") {
          const nextDevices = await dashboardApi.listDevices(token);
          if (!cancelled) {
            setDevices(nextDevices);
            const nextTargets = buildChatTargets(nextDevices);
            setChatDeviceId((current) => pickChatDeviceId(nextTargets, current));
          }
        }

        if (activeTab === "skills") {
          const nextSkills = await dashboardApi.listSkills(token);
          if (!cancelled) {
            setSkills(nextSkills);
          }
        }

        if (activeTab === "tasks") {
          const nextTasks = await dashboardApi.listTasks(token, {});
          if (!cancelled) {
            setTasks((current) => replaceTasks(current, nextTasks));
            setChatTaskId((current) => pickChatTaskId(nextTasks, current));
          }
        }

        if (activeTab === "ai-calls") {
          const nextCalls = await dashboardApi.listAiCallLogs(token, { limit: 100 });
          if (!cancelled) {
            setAiCalls(nextCalls);
            setSelectedAiCallId((current) => pickAiCallId(nextCalls, current));
          }
        }

        if (activeTab === "quick-deploy") {
          return;
        }

        if (activeTab === "settings") {
          const nextSystemInfo = await dashboardApi.getSystemInfo(token);
          if (!cancelled) {
            setSystemInfo(nextSystemInfo);
          }
        }
      } catch (error) {
        if (!cancelled) {
          handleApiError(error);
        }
      }
    }

    const intervalId = window.setInterval(() => {
      void refreshCurrentTab();
    }, 12000);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [activeTab, taskDeviceFilter, taskStatusFilter, token]);

  useEffect(() => {
    let socket: WebSocket | null = null;
    let heartbeatTimer: number | null = null;
    let reconnectTimer: number | null = null;
    let disposed = false;

    const connect = () => {
      setChatSocketState("connecting");
      socket = new WebSocket(dashboardApi.buildWebSocketUrl("/ws/app", { token }));

      socket.onopen = () => {
        if (!disposed) {
          setChatSocketState("connected");
          heartbeatTimer = window.setInterval(() => {
            if (socket?.readyState === WebSocket.OPEN) {
              socket.send("ping");
            }
          }, 15000);
        }
      };

      socket.onmessage = (event) => {
        const payload = JSON.parse(String(event.data)) as {
          type?: string;
          tasks?: Task[];
          task?: Task;
          task_id?: string;
          message?: string;
        };

        if (payload.type === "TASK_HISTORY_SYNC" && payload.tasks) {
          const incoming = payload.tasks;
          setTasks((current) => replaceTasks(current, incoming));
          setTaskDetail((current) => {
            if (!current) {
              return current;
            }
            const matched = incoming.find((task) => task.task_id === current.task_id);
            return matched ? mergeTask(current, matched) : null;
          });
          setChatTaskId((current) => pickChatTaskId(incoming, current ?? null));
        }

        if (payload.type === "TASK_SNAPSHOT" && payload.task) {
          const incoming = payload.task;
          setTasks((current) => upsertTask(current, incoming));
          setTaskDetail((current) => (
            current?.task_id === incoming.task_id ? mergeTask(current, incoming) : current
          ));
          setChatTaskId((current) => current ?? incoming.task_id);
        }

        if (payload.type === "TASK_LOG" && payload.task_id && payload.message) {
          setTasks((current) => appendTaskLog(current, payload.task_id!, payload.message!));
          setTaskDetail((current) => {
            if (!current || current.task_id !== payload.task_id) {
              return current;
            }
            return { ...current, logs: [...current.logs, payload.message!] };
          });
        }

        if (payload.type === "TASK_DELETED" && payload.task_id) {
          setTasks((current) => {
            const nextTasks = removeTask(current, payload.task_id!);
            setChatTaskId((currentTaskId) => pickChatTaskId(
              nextTasks,
              currentTaskId === payload.task_id ? null : currentTaskId,
            ));
            return nextTasks;
          });
          setTaskDetail((current) => (
            current?.task_id === payload.task_id ? null : current
          ));
        }
      };

      socket.onerror = () => {
        socket?.close();
      };

      socket.onclose = () => {
        if (disposed) {
          return;
        }
        if (heartbeatTimer) {
          window.clearInterval(heartbeatTimer);
          heartbeatTimer = null;
        }
        setChatSocketState("offline");
        reconnectTimer = window.setTimeout(connect, 3000);
      };
    };

    connect();

    return () => {
      disposed = true;
      if (heartbeatTimer) {
        window.clearInterval(heartbeatTimer);
      }
      if (reconnectTimer) {
        window.clearTimeout(reconnectTimer);
      }
      socket?.close();
    };
  }, [token]);

  async function refreshTab(tab: TabId = activeTab) {
    setRefreshing(true);
    try {
      if (tab === "overview") {
        setOverview(await dashboardApi.getOverview(token));
      }
      if (tab === "chat") {
        await refreshChatData();
      }
      if (tab === "devices") {
        const nextDevices = await dashboardApi.listDevices(token);
        setDevices(nextDevices);
        const nextTargets = buildChatTargets(nextDevices);
        setChatDeviceId((current) => pickChatDeviceId(nextTargets, current));
      }
      if (tab === "quick-deploy") {
        await refreshQuickDeployDraft(true);
      }
      if (tab === "skills") {
        setSkills(await dashboardApi.listSkills(token));
      }
      if (tab === "tasks") {
        const nextTasks = await dashboardApi.listTasks(token, {});
        setTasks((current) => replaceTasks(current, nextTasks));
        setChatTaskId((current) => pickChatTaskId(nextTasks, current));
      }
      if (tab === "ai-calls") {
        await refreshAiCalls();
      }
      if (tab === "settings") {
        await refreshSystemInfo();
      }
      setOverview(await dashboardApi.getOverview(token));
      setBannerMessage(null);
    } catch (error) {
      handleApiError(error);
    } finally {
      setRefreshing(false);
    }
  }

  function selectTab(tab: TabId) {
    setActiveTab(tab);
    setBannerMessage(null);
    void refreshTab(tab);
  }

  function patchDeviceForm(patch: Partial<DeviceForm>) {
    setDeviceForm((current) => ({ ...current, ...patch }));
  }

  function patchSkillForm(patch: Partial<SkillForm>) {
    setSkillForm((current) => ({ ...current, ...patch }));
  }

  function patchAssignmentForm(patch: Partial<AssignmentForm>) {
    setAssignmentForm((current) => ({ ...current, ...patch }));
  }

  function patchGatewayAiForm(patch: Partial<GatewayAiForm>) {
    setGatewayAiTestMessage(null);
    setGatewayAiForm((current) => ({ ...current, ...patch }));
  }

  function patchDeviceAiForm(patch: Partial<DeviceAiForm>) {
    setDeviceAiTestMessage(null);
    setDeviceAiForm((current) => ({ ...current, ...patch }));
  }

  function patchClientDeploymentForm(patch: Partial<ClientDeploymentForm>) {
    setClientBootstrapError(null);
    setClientBootstrapForm((current) => ({ ...current, ...patch }));
  }

  function patchQuickDeployModuleValue(
    moduleId: QuickDeployModuleId,
    key: string,
    value: string,
  ) {
    setQuickDeployError(null);
    setQuickDeployForm((current) => {
      const nextForm: QuickDeployForm = {
        ...current,
        modules: {
          ...current.modules,
          [moduleId]: {
            ...current.modules[moduleId],
            [key]: value,
          },
        },
      };

      if (
        moduleId === "client"
        && key === "OMNI_AGENT_DEVICE_ID"
        && !current.client_package.device_name.trim()
      ) {
        nextForm.client_package = {
          ...nextForm.client_package,
          device_name: value,
        };
      }

      return nextForm;
    });
  }

  function patchQuickDeployClientPackage(patch: Partial<QuickDeployForm["client_package"]>) {
    setQuickDeployError(null);
    setQuickDeployForm((current) => ({
      ...current,
      client_package: {
        ...current.client_package,
        ...patch,
      },
    }));
  }

  function toggleQuickDeployTarget(moduleId: QuickDeployModuleId) {
    setQuickDeployError(null);
    setQuickDeployForm((current) => {
      const selected = current.targets.includes(moduleId);
      const orderedTargets: QuickDeployModuleId[] = ["gateway", "client", "dashboard"];
      return {
        ...current,
        targets: selected
          ? current.targets.filter((target) => target !== moduleId)
          : orderedTargets.filter((target) => current.targets.includes(target) || target === moduleId),
      };
    });
  }

  function toggleQuickDeploySkill(skillId: string) {
    setQuickDeployError(null);
    setQuickDeployForm((current) => {
      const selected = current.client_package.skill_ids.includes(skillId);
      return {
        ...current,
        client_package: {
          ...current.client_package,
          skill_ids: selected
            ? current.client_package.skill_ids.filter((item) => item !== skillId)
            : [...current.client_package.skill_ids, skillId],
        },
      };
    });
  }

  function openDeviceCreate() {
    setDeviceEditorMode("create");
    setDeviceForm(createEmptyDeviceForm());
    setDeviceFormError(null);
  }

  function openDeviceEdit(device: Device) {
    setDeviceEditorMode("edit");
    setDeviceForm({
      device_id: device.device_id,
      name: device.name,
      type: device.type,
      device_key: "",
    });
    setDeviceFormError(null);
  }

  function closeDeviceEditor() {
    setDeviceEditorMode(null);
    setDeviceFormError(null);
  }

  function openClientDeployment() {
    setClientBootstrapOpen(true);
    setClientBootstrapBusy(false);
    setClientBootstrapError(null);
    setClientBootstrapForm(createEmptyClientDeploymentForm(suggestGatewayUrl()));
  }

  function closeClientDeployment() {
    setClientBootstrapOpen(false);
    setClientBootstrapBusy(false);
    setClientBootstrapError(null);
  }

  function toggleClientDeploymentSkill(skillId: string) {
    setClientBootstrapError(null);
    setClientBootstrapForm((current) => {
      const selected = current.skill_ids.includes(skillId);
      return {
        ...current,
        skill_ids: selected
          ? current.skill_ids.filter((item) => item !== skillId)
          : [...current.skill_ids, skillId],
      };
    });
  }

  async function saveDevice(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!deviceEditorMode) {
      return;
    }
    setDeviceFormError(null);
    try {
      if (deviceEditorMode === "create") {
        await dashboardApi.createDevice(token, deviceForm);
      } else {
        const nextDeviceKey = deviceForm.device_key.trim();
        await dashboardApi.updateDevice(token, deviceForm.device_id, {
          name: deviceForm.name,
          type: deviceForm.type,
          device_key: nextDeviceKey || undefined,
        });
      }
      closeDeviceEditor();
      await Promise.all([refreshTab("devices"), refreshTab("settings")]);
    } catch (error) {
      setDeviceFormError(getErrorMessage(error));
    }
  }

  async function removeDevice(device: Device) {
    if (!window.confirm(`确认删除设备 ${device.device_id} 吗？`)) {
      return;
    }
    try {
      await dashboardApi.deleteDevice(token, device.device_id);
      await Promise.all([refreshTab("devices"), refreshTab("settings"), refreshTab("tasks")]);
    } catch (error) {
      handleApiError(error);
    }
  }

  async function downloadClientPackage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setClientBootstrapError(null);

    const payload = {
      device_id: clientBootstrapForm.device_id.trim(),
      name: clientBootstrapForm.name.trim(),
      device_key: clientBootstrapForm.device_key.trim() || undefined,
      gateway_url: clientBootstrapForm.gateway_url.trim(),
      repo_url: clientBootstrapForm.repo_url.trim(),
      repo_ref: clientBootstrapForm.repo_ref.trim() || "main",
      network_profile: clientBootstrapForm.network_profile,
      skill_ids: clientBootstrapForm.skill_ids,
    };

    if (!payload.device_id || !payload.name || !payload.gateway_url || !payload.repo_url) {
      setClientBootstrapError("请先填写设备、Gateway 和代码仓库信息");
      return;
    }

    setClientBootstrapBusy(true);
    try {
      const result = await dashboardApi.downloadClientPackage(token, payload);
      triggerFileDownload(
        result.blob,
        result.filename || `open-jarvis-client-${payload.device_id}.zip`,
      );
      closeClientDeployment();
      await Promise.all([refreshTab("devices"), refreshTab("settings")]);
      setBannerMessage(`设备 ${payload.device_id} 的部署包已生成`);
    } catch (error) {
      const message = getErrorMessage(error);
      if (isSessionExpiredMessage(message)) {
        onSessionExpired("登录状态已失效，请重新登录");
        return;
      }
      setClientBootstrapError(message);
    } finally {
      setClientBootstrapBusy(false);
    }
  }

  async function downloadQuickDeployPackage() {
    setQuickDeployError(null);

    if (!quickDeployForm.targets.length) {
      setQuickDeployError("请至少选择一个部署目标");
      return;
    }

    const clientSelected = quickDeployForm.targets.includes("client");
    const clientDeviceId = quickDeployForm.modules.client.OMNI_AGENT_DEVICE_ID?.trim() || "";
    const deviceName = quickDeployForm.client_package.device_name.trim() || clientDeviceId;

    if (clientSelected && !deviceName) {
      setQuickDeployError("请填写 Client 设备名称或设备 ID");
      return;
    }

    if (clientSelected && !quickDeployForm.client_package.repo_url.trim()) {
      setQuickDeployError("请填写 Client 代码仓库地址");
      return;
    }

    setQuickDeployBusy(true);
    try {
      const result = await dashboardApi.downloadQuickDeployPackage(token, {
        targets: quickDeployForm.targets,
        modules: quickDeployForm.modules,
        client_package: {
          device_name: deviceName,
          repo_url: quickDeployForm.client_package.repo_url.trim(),
          repo_ref: quickDeployForm.client_package.repo_ref.trim() || "main",
          register_device: quickDeployForm.client_package.register_device,
          skill_ids: quickDeployForm.client_package.skill_ids,
        },
      });
      triggerFileDownload(result.blob, result.filename || "open-jarvis-quick-deploy.zip");
      if (clientSelected && quickDeployForm.client_package.register_device) {
        await Promise.all([refreshTab("devices"), refreshTab("settings")]);
      }
      const targetLabel = quickDeployForm.targets
        .map((target) => quickDeployDraft?.modules[target].title ?? target)
        .join(" / ");
      setBannerMessage(`已生成 ${targetLabel} 快速部署工件`);
    } catch (error) {
      const message = getErrorMessage(error);
      if (isSessionExpiredMessage(message)) {
        onSessionExpired("登录状态已失效，请重新登录");
        return;
      }
      setQuickDeployError(message);
    } finally {
      setQuickDeployBusy(false);
    }
  }

  function openSkillCreate() {
    setSkillEditorMode("create");
    setSkillForm(createEmptySkillForm());
    setSkillFormError(null);
  }

  function openSkillEdit(skill: Skill) {
    setSkillEditorMode("edit");
    setSkillForm({
      skill_id: skill.skill_id,
      name: skill.name,
      description: skill.description,
      config: JSON.stringify(skill.config ?? {}, null, 2),
      source: skill.source,
      archive_file: null,
      existing_archive_filename: skill.archive_filename ?? "",
      existing_archive_sha256: skill.archive_sha256 ?? "",
      existing_archive_size: skill.archive_size ?? 0,
    });
    setSkillFormError(null);
  }

  function closeSkillEditor() {
    setSkillEditorMode(null);
    setSkillFormError(null);
  }

  async function saveSkill(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!skillEditorMode) {
      return;
    }
    setSkillFormError(null);
    let createdSkillId: string | null = null;
    try {
      if (skillForm.source === "builtin" && skillForm.archive_file) {
        setSkillFormError("内建 Skill 不支持上传 zip");
        return;
      }
      if (
        skillEditorMode === "create"
        && skillForm.source === "archive"
        && !skillForm.archive_file
      ) {
        setSkillFormError("请上传包含 SKILL.md 的 zip 压缩包");
        return;
      }
      const config = parseJsonInput(skillForm.config);
      if (skillEditorMode === "create") {
        await dashboardApi.createSkill(token, {
          skill_id: skillForm.skill_id,
          name: skillForm.name,
          description: skillForm.description,
          config,
        });
        createdSkillId = skillForm.skill_id;
        if (skillForm.archive_file) {
          await dashboardApi.uploadSkillArchive(token, skillForm.skill_id, skillForm.archive_file);
        }
      } else {
        await dashboardApi.updateSkill(token, skillForm.skill_id, {
          name: skillForm.name,
          description: skillForm.description,
          config,
        });
        if (skillForm.archive_file) {
          await dashboardApi.uploadSkillArchive(token, skillForm.skill_id, skillForm.archive_file);
        }
      }
    } catch (error) {
      if (createdSkillId) {
        await dashboardApi.deleteSkill(token, createdSkillId).catch(() => undefined);
      }
      setSkillFormError(getErrorMessage(error));
      return;
    }

    closeSkillEditor();
    await Promise.all([refreshTab("skills"), refreshTab("devices")]);
  }

  async function removeSkill(skill: Skill) {
    if (!window.confirm(`确认删除 Skill ${skill.skill_id} 吗？`)) {
      return;
    }
    try {
      await dashboardApi.deleteSkill(token, skill.skill_id);
      await Promise.all([refreshTab("skills"), refreshTab("devices")]);
    } catch (error) {
      handleApiError(error);
    }
  }

  async function openAssignment(deviceId: string) {
    try {
      const [device, nextSkills] = await Promise.all([
        dashboardApi.getDevice(token, deviceId),
        dashboardApi.listSkills(token),
      ]);
      const readySkills = nextSkills.filter(
        (skill) => skill.source === "builtin" || skill.archive_ready,
      );
      setAssignmentDevice(device);
      setSkills(nextSkills);
      setAssignmentForm({
        skill_id: readySkills[0]?.skill_id ?? "",
        config: "{}",
      });
      setAssignmentError(null);
    } catch (error) {
      handleApiError(error);
    }
  }

  function closeAssignment() {
    setAssignmentDevice(null);
    setAssignmentError(null);
  }

  async function submitAssignment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!assignmentDevice) {
      return;
    }
    if (!assignmentForm.skill_id) {
      setAssignmentError("当前没有可分配的 Skill，请先启用内建 Skill 或上传 zip 归档");
      return;
    }
    setAssignmentError(null);
    try {
      await dashboardApi.assignSkill(token, assignmentDevice.device_id, {
        skill_id: assignmentForm.skill_id,
        config: parseJsonInput(assignmentForm.config),
      });
      const refreshed = await dashboardApi.getDevice(token, assignmentDevice.device_id);
      setAssignmentDevice(refreshed);
      setAssignmentForm(createEmptyAssignmentForm());
      await refreshTab("devices");
    } catch (error) {
      setAssignmentError(getErrorMessage(error));
    }
  }

  async function removeAssignment(skill: DeviceSkill) {
    if (!assignmentDevice) {
      return;
    }
    if (!window.confirm(`确认移除 ${skill.skill_id} 吗？`)) {
      return;
    }
    try {
      await dashboardApi.unassignSkill(token, assignmentDevice.device_id, skill.skill_id);
      const refreshed = await dashboardApi.getDevice(token, assignmentDevice.device_id);
      setAssignmentDevice(refreshed);
      await refreshTab("devices");
    } catch (error) {
      handleApiError(error);
    }
  }

  function openTaskDetail(task: Task) {
    setTaskDetail(task);
  }

  function closeTaskDetail() {
    setTaskDetail(null);
  }

  function selectChatTask(taskId: string | null) {
    setChatTaskId(taskId);
  }

  function selectChatDevice(deviceId: string) {
    setChatDeviceId(deviceId);
  }

  function selectAiCall(callId: string | null) {
    setSelectedAiCallId(callId);
  }

  async function createChatTask(instruction: string) {
    try {
      const nextTask = await dashboardApi.createTask(token, {
        device_id: chatDeviceId || undefined,
        instruction,
      });
      setTasks((current) => upsertTask(current, nextTask));
      setChatTaskId(nextTask.task_id);
      setBannerMessage(null);
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  }

  async function submitChatDecision(approved: boolean) {
    if (!chatTaskId) {
      return;
    }
    try {
      const updatedTask = await dashboardApi.submitTaskDecision(token, chatTaskId, approved);
      setTasks((current) => upsertTask(current, updatedTask));
      setTaskDetail((current) => (
        current?.task_id === updatedTask.task_id ? mergeTask(current, updatedTask) : current
      ));
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  }

  async function deleteChatTask(taskId: string) {
    const target = tasks.find((task) => task.task_id === taskId);
    if (!target || !isTaskDeletable(target)) {
      return;
    }
    if (!window.confirm(`确认删除任务 ${taskId} 的聊天记录吗？`)) {
      return;
    }
    try {
      await dashboardApi.deleteTask(token, taskId);
      setTasks((current) => {
        const nextTasks = removeTask(current, taskId);
        setChatTaskId((currentTaskId) => pickChatTaskId(
          nextTasks,
          currentTaskId === taskId ? null : currentTaskId,
        ));
        return nextTasks;
      });
      setTaskDetail((current) => (
        current?.task_id === taskId ? null : current
      ));
      setBannerMessage(null);
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  }

  async function saveGatewayAiConfig(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setGatewayAiError(null);
    setGatewayAiTestMessage(null);
    try {
      await dashboardApi.saveGatewayAiConfig(token, {
        provider: gatewayAiForm.provider.trim(),
        model: gatewayAiForm.model.trim(),
        api_key: gatewayAiForm.api_key.trim(),
        base_url: gatewayAiForm.base_url.trim() || undefined,
      });
      setGatewayAiForm(createEmptyGatewayAiForm());
      await refreshSystemInfo();
      setBannerMessage("Gateway AI 默认配置已保存，CLI 将自动继承");
    } catch (error) {
      setGatewayAiError(getErrorMessage(error));
    }
  }

  async function clearGatewayAiConfig() {
    try {
      await dashboardApi.clearGatewayAiConfig(token);
      setGatewayAiForm(createEmptyGatewayAiForm());
      setGatewayAiError(null);
      setGatewayAiTestMessage(null);
      await refreshSystemInfo();
      setBannerMessage("Gateway AI 默认配置已清除");
    } catch (error) {
      handleApiError(error);
    }
  }

  async function saveDeviceAiConfig(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setDeviceAiError(null);
    setDeviceAiTestMessage(null);
    if (!deviceAiForm.device_id) {
      setDeviceAiError("请选择需要覆盖的 CLI 设备");
      return;
    }
    try {
      await dashboardApi.saveDeviceAiConfig(token, deviceAiForm.device_id, {
        provider: deviceAiForm.provider.trim(),
        model: deviceAiForm.model.trim(),
        api_key: deviceAiForm.api_key.trim(),
        base_url: deviceAiForm.base_url.trim() || undefined,
      });
      const selectedDeviceId = deviceAiForm.device_id;
      setDeviceAiForm({ ...createEmptyDeviceAiForm(), device_id: selectedDeviceId });
      await refreshSystemInfo();
      setBannerMessage(`CLI 设备 ${selectedDeviceId} 的特殊覆盖已保存`);
    } catch (error) {
      setDeviceAiError(getErrorMessage(error));
    }
  }

  async function clearDeviceAiConfig() {
    if (!deviceAiForm.device_id) {
      setDeviceAiError("请选择需要清除覆盖的 CLI 设备");
      return;
    }
    try {
      const selectedDeviceId = deviceAiForm.device_id;
      await dashboardApi.clearDeviceAiConfig(token, selectedDeviceId);
      setDeviceAiForm({ ...createEmptyDeviceAiForm(), device_id: selectedDeviceId });
      setDeviceAiError(null);
      setDeviceAiTestMessage(null);
      await refreshSystemInfo();
      setBannerMessage(`CLI 设备 ${selectedDeviceId} 的特殊覆盖已清除`);
    } catch (error) {
      handleApiError(error);
    }
  }

  async function testGatewayAiConfig() {
    setGatewayAiError(null);
    try {
      const result = await dashboardApi.testGatewayAiConfig(token);
      setGatewayAiTestMessage(
        `${result.provider} · ${result.model}：${summarizeAiTestResponse(result.response)}`,
      );
      await refreshAiCalls();
      setBannerMessage("Gateway AI 默认配置测试完成");
    } catch (error) {
      setGatewayAiError(getErrorMessage(error));
    }
  }

  async function testDeviceAiConfig() {
    setDeviceAiError(null);
    if (!deviceAiForm.device_id) {
      setDeviceAiError("请选择需要测试的 CLI 设备");
      return;
    }
    try {
      const result = await dashboardApi.testDeviceAiConfig(token, deviceAiForm.device_id);
      setDeviceAiTestMessage(
        `${result.provider} · ${result.model}：${summarizeAiTestResponse(result.response)}`,
      );
      await refreshAiCalls();
      setBannerMessage(`CLI 设备 ${deviceAiForm.device_id} 配置测试完成`);
    } catch (error) {
      setDeviceAiError(getErrorMessage(error));
    }
  }

  return {
    activeTab,
    bannerMessage,
    refreshing,
    overview,
    devices,
    skills,
    tasks,
    aiCalls,
    systemInfo,
    chatTargets,
    chatTaskId,
    chatTask,
    selectedAiCallId,
    aiCallDetail,
    chatDeviceId,
    chatSocketState,
    gatewayAiSummary,
    clientAiSummaries,
    taskStatusFilter,
    taskDeviceFilter,
    deviceEditorMode,
    deviceForm,
    deviceFormError,
    skillEditorMode,
    skillForm,
    skillFormError,
    assignmentDevice,
    assignmentForm,
    assignmentError,
    gatewayAiForm,
    gatewayAiError,
    gatewayAiTestMessage,
    deviceAiForm,
    deviceAiError,
    deviceAiTestMessage,
    clientBootstrapOpen,
    clientBootstrapBusy,
    clientBootstrapForm,
    clientBootstrapError,
    quickDeployDraft,
    quickDeployForm,
    quickDeployBusy,
    quickDeployError,
    taskDetail,
    setTaskStatusFilter,
    setTaskDeviceFilter,
    selectTab,
    refreshTab,
    openDeviceCreate,
    openDeviceEdit,
    closeDeviceEditor,
    patchDeviceForm,
    saveDevice,
    removeDevice,
    openClientBootstrap: openClientDeployment,
    closeClientBootstrap: closeClientDeployment,
    patchClientBootstrapForm: patchClientDeploymentForm,
    toggleClientBootstrapSkill: toggleClientDeploymentSkill,
    downloadClientPackage,
    patchQuickDeployModuleValue,
    patchQuickDeployClientPackage,
    toggleQuickDeployTarget,
    toggleQuickDeploySkill,
    downloadQuickDeployPackage,
    openSkillCreate,
    openSkillEdit,
    closeSkillEditor,
    patchSkillForm,
    saveSkill,
    removeSkill,
    openAssignment,
    closeAssignment,
    patchAssignmentForm,
    submitAssignment,
    removeAssignment,
    patchGatewayAiForm,
    patchDeviceAiForm,
    saveGatewayAiConfig,
    saveDeviceAiConfig,
    clearGatewayAiConfig,
    clearDeviceAiConfig,
    openTaskDetail,
    closeTaskDetail,
    selectChatTask,
    openChatThread: selectChatTask,
    selectChatDevice,
    selectAiCall,
    createChatTask,
    sendChatInstruction: createChatTask,
    submitChatDecision,
    deleteChatTask,
    testGatewayAiConfig,
    testDeviceAiConfig,
  };
}
