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
        <div className="detail-grid">
          <div>
            <span>指令</span>
            <strong>{task.instruction}</strong>
          </div>
          <div>
            <span>检查点</span>
            <strong>{task.checkpoint_id || "无"}</strong>
          </div>
          <div>
            <span>审批命令</span>
            <strong>{task.command || "无"}</strong>
          </div>
          <div>
            <span>审批原因</span>
            <strong>{task.reason || "无"}</strong>
          </div>
          <div>
            <span>执行结果</span>
            <strong>{task.result || "无"}</strong>
          </div>
          <div>
            <span>错误信息</span>
            <strong>{task.error || "无"}</strong>
          </div>
        </div>
        <section className="log-panel">
          <div className="panel-head compact">
            <div>
              <p className="eyebrow">Realtime Trail</p>
              <h3>日志</h3>
            </div>
          </div>
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
