import 'package:app/src/state/task_controller.dart';
import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/components/glass_card.dart';
import 'package:flutter/material.dart';

class ComposerBar extends StatelessWidget {
  const ComposerBar({
    required this.controller,
    required this.selectedDeviceId,
    required this.composerController,
    required this.onComposerChanged,
    required this.onSend,
    super.key,
  });

  final TaskController controller;
  final String? selectedDeviceId;
  final TextEditingController composerController;
  final VoidCallback onComposerChanged;
  final Future<void> Function() onSend;

  @override
  Widget build(BuildContext context) {
    final tokens = JarvisThemeTokens.of(context);
    final canSend =
        controller.status == ConnectionStatus.connected &&
        selectedDeviceId != null;

    return GlassCard(
      padding: const EdgeInsets.all(18),
      backgroundColor: tokens.shell,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (selectedDeviceId != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: Chip(
                avatar: Icon(Icons.devices_rounded, size: 16, color: tokens.accent),
                label: Text(selectedDeviceId!),
                visualDensity: VisualDensity.compact,
              ),
            ),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Expanded(
                child: TextField(
                  key: const Key('chatComposerField'),
                  controller: composerController,
                  onChanged: (_) => onComposerChanged(),
                  onSubmitted: (_) {
                    if (canSend) {
                      onSend();
                    }
                  },
                  minLines: 1,
                  maxLines: 5,
                  decoration: InputDecoration(
                    hintText: controller.status == ConnectionStatus.connected
                        ? '输入一个任务，例如：检查 api-service 并在必要时重启'
                        : '先完成网关连接，再开始下发任务',
                  ),
                ),
              ),
              const SizedBox(width: 12),
              SizedBox(
                width: 44,
                height: 44,
                child: Material(
                  key: const Key('chatSendButton'),
                  color: canSend ? tokens.accent : tokens.surfaceMuted,
                  borderRadius: BorderRadius.circular(22),
                  child: InkWell(
                    borderRadius: BorderRadius.circular(22),
                    onTap: canSend ? onSend : null,
                    child: Icon(
                      Icons.arrow_upward_rounded,
                      color: canSend ? Colors.white : tokens.textMuted,
                      size: 22,
                    ),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            selectedDeviceId == null
                ? '还没有可用设备，暂时无法把任务发出去。'
                : '这条消息会路由到 $selectedDeviceId，并把后续审批和日志回收到当前线程。',
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
    );
  }
}
