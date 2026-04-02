import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import { dashboardApi } from "../api";
import {
  createEmptyAssignmentForm,
  createEmptyDeviceForm,
  createEmptySkillForm,
  type AssignmentForm,
  type DeviceForm,
  type SkillForm,
  type TabId,
} from "./model";
import { getErrorMessage } from "../lib/format";
import { parseJsonInput } from "../lib/json";
import type { Device, DeviceSkill, Overview, Skill, SystemInfo, Task } from "../types";

type UseDashboardControllerArgs = {
  token: string;
  onSessionExpired: (message: string) => void;
};

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
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);

  const [taskStatusFilter, setTaskStatusFilter] = useState("");
  const [taskDeviceFilter, setTaskDeviceFilter] = useState("");

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

  const [taskDetail, setTaskDetail] = useState<Task | null>(null);

  function handleApiError(error: unknown) {
    const message = getErrorMessage(error);
    if (
      message.includes("401") ||
      message.includes("未登录") ||
      message.includes("登录已过期")
    ) {
      onSessionExpired("登录状态已失效，请重新登录");
      return;
    }
    setBannerMessage(message);
  }

  useEffect(() => {
    const activeToken = token;
    let cancelled = false;

    async function bootstrap() {
      setRefreshing(true);
      try {
        const [nextOverview, nextDevices, nextSkills, nextTasks, nextSystemInfo] =
          await Promise.all([
            dashboardApi.getOverview(activeToken),
            dashboardApi.listDevices(activeToken),
            dashboardApi.listSkills(activeToken),
            dashboardApi.listTasks(activeToken, {}),
            dashboardApi.getSystemInfo(activeToken),
          ]);
        if (cancelled) {
          return;
        }
        setOverview(nextOverview);
        setDevices(nextDevices);
        setSkills(nextSkills);
        setTasks(nextTasks);
        setSystemInfo(nextSystemInfo);
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
    const activeToken = token;
    let cancelled = false;

    async function refreshCurrentTab() {
      try {
        const nextOverview = await dashboardApi.getOverview(activeToken);
        if (cancelled) {
          return;
        }
        setOverview(nextOverview);

        if (activeTab === "devices") {
          const nextDevices = await dashboardApi.listDevices(activeToken);
          if (!cancelled) {
            setDevices(nextDevices);
          }
        }

        if (activeTab === "skills") {
          const nextSkills = await dashboardApi.listSkills(activeToken);
          if (!cancelled) {
            setSkills(nextSkills);
          }
        }

        if (activeTab === "tasks") {
          const nextTasks = await dashboardApi.listTasks(activeToken, {
            status: taskStatusFilter || undefined,
            device_id: taskDeviceFilter || undefined,
          });
          if (!cancelled) {
            setTasks(nextTasks);
          }
        }

        if (activeTab === "settings") {
          const nextSystemInfo = await dashboardApi.getSystemInfo(activeToken);
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
  }, [activeTab, onSessionExpired, taskDeviceFilter, taskStatusFilter, token]);

  async function refreshTab(tab: TabId = activeTab) {
    setRefreshing(true);
    try {
      if (tab === "overview") {
        setOverview(await dashboardApi.getOverview(token));
      }
      if (tab === "devices") {
        setDevices(await dashboardApi.listDevices(token));
      }
      if (tab === "skills") {
        setSkills(await dashboardApi.listSkills(token));
      }
      if (tab === "tasks") {
        setTasks(
          await dashboardApi.listTasks(token, {
            status: taskStatusFilter || undefined,
            device_id: taskDeviceFilter || undefined,
          }),
        );
      }
      if (tab === "settings") {
        setSystemInfo(await dashboardApi.getSystemInfo(token));
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
      device_key: device.device_key,
    });
    setDeviceFormError(null);
  }

  function closeDeviceEditor() {
    setDeviceEditorMode(null);
    setDeviceFormError(null);
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
        await dashboardApi.updateDevice(token, deviceForm.device_id, {
          name: deviceForm.name,
          type: deviceForm.type,
          device_key: deviceForm.device_key,
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
      if (skillEditorMode === "create" && !skillForm.archive_file) {
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
      const readySkills = nextSkills.filter((skill) => skill.archive_ready);
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
      setAssignmentError("当前没有可分配的 Skill 压缩包，请先在 Skills 页面上传 zip");
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

  return {
    activeTab,
    bannerMessage,
    refreshing,
    overview,
    devices,
    skills,
    tasks,
    systemInfo,
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
    openTaskDetail,
    closeTaskDetail,
  };
}
