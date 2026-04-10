import 'package:app/src/state/task_controller.dart';
import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/components/jarvis_dropdown_field.dart';
import 'package:app/src/ui/helpers.dart';
import 'package:flutter/material.dart';

class SetupTray extends StatelessWidget {
  const SetupTray({
    super.key,
    required this.controller,
    required this.expanded,
    required this.selectedDeviceId,
    required this.onToggle,
    required this.onDeviceChanged,
    required this.onPrefillInstruction,
    required this.onFocusPending,
  });

  final TaskController controller;
  final bool expanded;
  final String? selectedDeviceId;
  final VoidCallback onToggle;
  final ValueChanged<String?> onDeviceChanged;
  final ValueChanged<String> onPrefillInstruction;
  final VoidCallback onFocusPending;

  @override
  Widget build(BuildContext context) {
    final tokens = JarvisThemeTokens.of(context);
    final onlineCount = controller.devices
        .where((device) => device.connected)
        .length;
    final summary = <String>[
      selectedDeviceId == null ? '未选择设备' : '设备 $selectedDeviceId',
      '${controller.pendingTasks.length} 待审批',
    ].join(' · ');
    const quickPrompts = <(String, String)>[
      ('巡检容器', '检查 docker 容器状态并汇总异常'),
      ('恢复挂起任务', '检查当前所有挂起任务并给出恢复建议'),
      ('查看网关日志', '查看网关最近 100 行日志并标出异常'),
    ];

    return AnimatedContainer(
      duration: motionDuration(context),
      curve: Curves.easeOutCubic,
      padding: EdgeInsets.fromLTRB(20, 18, 20, expanded ? 20 : 18),
      decoration: BoxDecoration(
        color: tokens.shell.withValues(alpha: 0.84),
        borderRadius: BorderRadius.circular(32),
        border: Border.all(
          color: expanded ? tokens.borderStrong : tokens.border,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          InkWell(
            key: const Key('setupToggleButton'),
            borderRadius: BorderRadius.circular(24),
            onTap: onToggle,
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '会话设置',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        expanded ? '选择设备并填充常用起手任务。' : summary,
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 10,
                    vertical: 8,
                  ),
                  decoration: BoxDecoration(
                    color: tokens.surface,
                    borderRadius: BorderRadius.circular(999),
                    border: Border.all(color: tokens.border),
                  ),
                  child: Text(
                    '${connectionStatusLabel(controller.status)} · $onlineCount 在线',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ),
                const SizedBox(width: 8),
                AnimatedRotation(
                  turns: expanded ? 0.5 : 0,
                  duration: motionDuration(context),
                  child: Icon(
                    Icons.keyboard_arrow_down_rounded,
                    color: tokens.textMuted,
                  ),
                ),
              ],
            ),
          ),
          ClipRect(
            child: AnimatedSize(
              duration: motionDuration(context),
              curve: Curves.easeOutCubic,
              child: expanded
                  ? Column(
                      key: const Key('setupPanelBody'),
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const SizedBox(height: 16),
                        Divider(color: tokens.border, height: 1),
                        const SizedBox(height: 16),
                        Text(
                          '任务会发往选中的执行端，常用提示词可直接回填到底部输入框。',
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                        const SizedBox(height: 14),
                        JarvisDropdownField<String>(
                          key: const Key('setupDeviceField'),
                          initialValue: selectedDeviceId,
                          hintText: '选择要协作的设备',
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
                        const SizedBox(height: 16),
                        Wrap(
                          spacing: 10,
                          runSpacing: 10,
                          children: quickPrompts
                              .map(
                                (prompt) => ActionChip(
                                  onPressed: () =>
                                      onPrefillInstruction(prompt.$2),
                                  avatar: const Icon(
                                    Icons.north_east_rounded,
                                    size: 16,
                                  ),
                                  label: Text(prompt.$1),
                                ),
                              )
                              .toList(growable: false),
                        ),
                        if (controller.pendingTasks.isNotEmpty &&
                            controller.selectedTask == null) ...[
                          const SizedBox(height: 12),
                          TextButton.icon(
                            onPressed: onFocusPending,
                            icon: const Icon(Icons.playlist_play_rounded),
                            label: Text(
                              '恢复 ${controller.pendingTasks.length} 个挂起任务',
                            ),
                          ),
                        ],
                      ],
                    )
                  : const SizedBox.shrink(),
            ),
          ),
        ],
      ),
    );
  }
}
