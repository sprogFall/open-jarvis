import { taskStatuses } from "../../app/model";
import { SectionHeader } from "../../components/SectionHeader";
import { StatusPill } from "../../components/StatusPill";
import { formatTaskStatus } from "../../lib/format";
import type { Device, Task } from "../../types";

type TasksTabProps = {
  tasks: Task[];
  devices: Device[];
  taskStatusFilter: string;
  taskDeviceFilter: string;
  onStatusFilterChange: (value: string) => void;
  onDeviceFilterChange: (value: string) => void;
  onRefresh: () => void | Promise<void>;
  onSelectTask: (task: Task) => void;
};

export function TasksTab({
  tasks,
  devices,
  taskStatusFilter,
  taskDeviceFilter,
  onStatusFilterChange,
  onDeviceFilterChange,
  onRefresh,
  onSelectTask,
}: TasksTabProps) {
  const visibleTasks = tasks.filter((task) => {
    if (taskStatusFilter && task.status !== taskStatusFilter) {
      return false;
    }
    if (taskDeviceFilter && task.device_id !== taskDeviceFilter) {
      return false;
    }
    return true;
  });

  return (
    <section className="panel">
      <SectionHeader
        actions={
          <div className="task-filters">
            <select
              value={taskStatusFilter}
              onChange={(event) => onStatusFilterChange(event.target.value)}
            >
              <option value="">全部状态</option>
              {taskStatuses.map((status) => (
                <option key={status} value={status}>
                  {formatTaskStatus(status)}
                </option>
              ))}
            </select>
            <select
              value={taskDeviceFilter}
              onChange={(event) => onDeviceFilterChange(event.target.value)}
            >
              <option value="">全部设备</option>
              {devices.map((device) => (
                <option key={device.device_id} value={device.device_id}>
                  {device.device_id}
                </option>
              ))}
            </select>
            <button className="ghost-button" onClick={() => void onRefresh()} type="button">
              刷新数据
            </button>
          </div>
        }
        className="tasks-head"
        eyebrow="Monitor"
        title="任务监控"
      />
      <div className="table-shell">
        <table>
          <thead>
            <tr>
              <th>任务</th>
              <th>设备</th>
              <th>状态</th>
              <th>摘要</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {visibleTasks.map((task) => (
              <tr key={task.task_id}>
                <td>
                  <strong>{task.task_id}</strong>
                  <span className="cell-subtle">{task.instruction}</span>
                </td>
                <td>{task.device_id}</td>
                <td>
                  <StatusPill status={task.status} />
                </td>
                <td>{task.command || task.result || task.error || task.reason || "等待详情"}</td>
                <td>
                  <button
                    className="ghost-button"
                    onClick={() => onSelectTask(task)}
                    type="button"
                  >
                    查看详情
                  </button>
                </td>
              </tr>
            ))}
            {!visibleTasks.length ? (
              <tr>
                <td colSpan={5}>
                  <p className="empty-copy">当前筛选条件下没有任务。</p>
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </section>
  );
}
