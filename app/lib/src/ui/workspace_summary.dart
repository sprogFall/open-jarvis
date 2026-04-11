import 'package:app/src/state/task_controller.dart';
import 'package:app/src/ui/components/glass_card.dart';
import 'package:app/src/ui/components/metric_chip.dart';
import 'package:flutter/material.dart';

class WorkspaceSummary extends StatelessWidget {
  const WorkspaceSummary({
    super.key,
    required this.controller,
    required this.selectedDeviceId,
    required this.onFocusPending,
  });

  final TaskController controller;
  final String? selectedDeviceId;
  final VoidCallback onFocusPending;

  @override
  Widget build(BuildContext context) {
    final onlineDevices = controller.devices
        .where((device) => device.connected)
        .length;
    final selectedTask = controller.selectedTask;

    return GlassCard(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            selectedTask == null ? '任务总览' : '当前任务',
            style: Theme.of(context).textTheme.headlineSmall,
          ),
          const SizedBox(height: 8),
          Text(
            selectedTask == null
                ? '查看设备、待审批和挂起任务。'
                : '当前状态：${selectedTask.status.label}',
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              MetricChip(
                icon: Icons.route_rounded,
                label: selectedDeviceId == null
                    ? '未选择设备'
                    : '当前设备 $selectedDeviceId',
              ),
              MetricChip(
                icon: Icons.devices_rounded,
                label: '$onlineDevices 台在线',
              ),
              MetricChip(
                icon: Icons.pending_actions_rounded,
                label: '${controller.pendingTasks.length} 个待审批',
              ),
              if (selectedTask?.checkpointId case final checkpointId?)
                MetricChip(
                  icon: Icons.restore_rounded,
                  label: '检查点 $checkpointId',
                ),
            ],
          ),
          if (controller.pendingTasks.isNotEmpty && selectedTask == null) ...[
            const SizedBox(height: 16),
            OutlinedButton.icon(
              onPressed: onFocusPending,
              icon: const Icon(Icons.playlist_play_rounded),
              label: Text('恢复 ${controller.pendingTasks.length} 个挂起任务'),
            ),
          ],
        ],
      ),
    );
  }
}
