import 'package:app/src/models/task_record.dart';
import 'package:app/src/state/task_controller.dart';
import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/components/glass_card.dart';
import 'package:app/src/ui/components/metric_chip.dart';
import 'package:app/src/ui/components/status_pill.dart';
import 'package:app/src/ui/helpers.dart';
import 'package:app/src/ui/sidebar/empty_thread_state.dart';
import 'package:app/src/ui/sidebar/task_section.dart';
import 'package:flutter/material.dart';

class ThreadRail extends StatelessWidget {
  const ThreadRail({
    required this.controller,
    required this.selectedDeviceId,
    required this.onDeviceChanged,
    required this.onNewChat,
    required this.onSelectTask,
    super.key,
  });

  final TaskController controller;
  final String? selectedDeviceId;
  final ValueChanged<String?> onDeviceChanged;
  final VoidCallback onNewChat;
  final ValueChanged<String> onSelectTask;

  @override
  Widget build(BuildContext context) {
    final tokens = JarvisThemeTokens.of(context);
    final pendingTasks = controller.tasks
        .where((task) => task.status == TaskStatus.awaitingApproval)
        .toList(growable: false);
    final recentTasks = controller.tasks
        .where((task) => task.status != TaskStatus.awaitingApproval)
        .toList(growable: false);
    final onlineDevices = controller.devices
        .where((device) => device.connected)
        .length;

    return GlassCard(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: tokens.accentSoft,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Icon(Icons.auto_awesome_rounded, color: tokens.accent),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('任务线程', style: Theme.of(context).textTheme.titleLarge),
                    const SizedBox(height: 4),
                    Text(
                      '审批、恢复与历史会话',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
              StatusPill(
                label: connectionStatusLabel(controller.status),
                color: connectionStatusColor(controller.status, tokens),
              ),
            ],
          ),
          const SizedBox(height: 16),
          FilledButton.icon(
            key: const Key('drawerNewChatButton'),
            onPressed: onNewChat,
            icon: const Icon(Icons.edit_note_rounded),
            label: const Text('新对话'),
          ),
          const SizedBox(height: 16),
          GlassCard(
            padding: const EdgeInsets.all(16),
            backgroundColor: tokens.surface,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('当前路由', style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 8),
                Text(
                  '任务会发送到这里选中的执行端。',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                const SizedBox(height: 16),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    MetricChip(
                      icon: Icons.devices_rounded,
                      label: '$onlineDevices 台在线',
                    ),
                    MetricChip(
                      icon: Icons.pending_actions_rounded,
                      label: '${controller.pendingTasks.length} 待审批',
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                DropdownButtonFormField<String>(
                  key: ValueKey<String?>(selectedDeviceId),
                  initialValue: selectedDeviceId,
                  isExpanded: true,
                  decoration: const InputDecoration(hintText: '选择要协作的设备'),
                  items: controller.devices
                      .map(
                        (device) => DropdownMenuItem<String>(
                          value: device.deviceId,
                          child: Text(
                            device.connected
                                ? '${device.deviceId} · 在线'
                                : '${device.deviceId} · 离线',
                          ),
                        ),
                      )
                      .toList(growable: false),
                  onChanged: onDeviceChanged,
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          Expanded(
            child: Scrollbar(
              child: ListView(
                padding: EdgeInsets.zero,
                children: [
                  if (pendingTasks.isNotEmpty)
                    TaskSection(
                      title: '待处理线程',
                      body: '先处理敏感操作审批，再继续任务。',
                      tasks: pendingTasks,
                      selectedTaskId: controller.selectedTask?.taskId,
                      onSelectTask: onSelectTask,
                    ),
                  if (pendingTasks.isNotEmpty && recentTasks.isNotEmpty)
                    const SizedBox(height: 14),
                  if (recentTasks.isNotEmpty)
                    TaskSection(
                      title: '最近会话',
                      body: '已经跑过的任务和主动发起的聊天。',
                      tasks: recentTasks,
                      selectedTaskId: controller.selectedTask?.taskId,
                      onSelectTask: onSelectTask,
                    ),
                  if (controller.tasks.isEmpty) const EmptyThreadState(),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
