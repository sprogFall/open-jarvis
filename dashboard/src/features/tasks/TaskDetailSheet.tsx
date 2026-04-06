import { KeyValueGrid } from "../../components/KeyValueGrid";
import { SectionHeader } from "../../components/SectionHeader";
import { SideSheet } from "../../components/SideSheet";
import { formatTaskStatus } from "../../lib/format";
import type { Task } from "../../types";

type TaskDetailSheetProps = {
  task: Task;
  onClose: () => void;
};

export function TaskDetailSheet({ task, onClose }: TaskDetailSheetProps) {
  return (
    <SideSheet
      title={`任务 ${task.task_id}`}
      subtitle={`设备 ${task.device_id} · ${formatTaskStatus(task.status)}`}
      onClose={onClose}
    >
      <div className="stack">
        <KeyValueGrid
          items={[
            { label: "指令", value: task.instruction },
            { label: "检查点", value: task.checkpoint_id || "无" },
            { label: "审批命令", value: task.command || "无" },
            { label: "审批原因", value: task.reason || "无" },
            { label: "执行结果", value: task.result || "无" },
            { label: "错误信息", value: task.error || "无" },
          ]}
        />
        <section className="log-panel">
          <SectionHeader compact eyebrow="Realtime Trail" title="日志" />
          {task.logs.length ? (
            <pre>{task.logs.join("\n")}</pre>
          ) : (
            <p className="empty-copy">当前任务还没有日志。</p>
          )}
        </section>
      </div>
    </SideSheet>
  );
}
