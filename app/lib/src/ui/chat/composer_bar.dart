import 'package:app/src/state/task_controller.dart';
import 'package:app/src/ui/app_theme.dart';
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
    final shapes = JarvisShapeTokens.of(context);
    final canSend =
        controller.status == ConnectionStatus.connected &&
        selectedDeviceId != null;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Expanded(
              child: DecoratedBox(
                decoration: BoxDecoration(
                  color: tokens.shell.withValues(alpha: 0.92),
                  borderRadius: shapes.xl,
                  border: Border.all(color: tokens.borderStrong),
                ),
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
                    filled: false,
                    border: InputBorder.none,
                    enabledBorder: InputBorder.none,
                    focusedBorder: InputBorder.none,
                    contentPadding: const EdgeInsets.symmetric(
                      horizontal: 18,
                      vertical: 16,
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(width: 12),
            SizedBox(
              width: 48,
              height: 48,
              child: Material(
                key: const Key('chatSendButton'),
                color: canSend ? tokens.accent : tokens.surfaceMuted,
                borderRadius: shapes.full,
                child: InkWell(
                  borderRadius: shapes.full,
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
        const SizedBox(height: 8),
        Text(
          selectedDeviceId == null
              ? '请先在顶部展开会话设置并选择设备。'
              : '发送到 $selectedDeviceId，后续审批与日志会继续写回这里。',
          style: Theme.of(context).textTheme.bodySmall,
        ),
      ],
    );
  }
}
