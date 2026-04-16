import { render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { TasksTab } from "./TasksTab";

describe("TasksTab", () => {
  it("renders titled task filters inside a shared toolbar row with the refresh action", () => {
    const { container } = render(
      <TasksTab
        tasks={[
          {
            task_id: "task-1",
            device_id: "device-alpha",
            instruction: "检查服务状态",
            status: "RUNNING",
            checkpoint_id: null,
            command: null,
            reason: null,
            result: null,
            error: null,
            logs: [],
          },
        ]}
        devices={[
          {
            device_id: "device-alpha",
            name: "Alpha",
            type: "cli",
            last_seen_at: null,
            connected: true,
          },
        ]}
        taskStatusFilter=""
        taskDeviceFilter=""
        onStatusFilterChange={vi.fn()}
        onDeviceFilterChange={vi.fn()}
        onRefresh={vi.fn()}
        onSelectTask={vi.fn()}
      />,
    );

    const toolbar = container.querySelector(".task-toolbar");
    expect(toolbar).not.toBeNull();
    expect(toolbar).toContainElement(screen.getByRole("button", { name: "刷新数据" }));

    const statusField = within(toolbar as HTMLElement).getByText("任务状态");
    const deviceField = within(toolbar as HTMLElement).getByText("设备");

    expect(statusField).toBeInTheDocument();
    expect(deviceField).toBeInTheDocument();
    expect(within(toolbar as HTMLElement).getByRole("combobox", { name: "任务状态" })).toBeVisible();
    expect(within(toolbar as HTMLElement).getByRole("combobox", { name: "设备" })).toBeVisible();
  });
});
