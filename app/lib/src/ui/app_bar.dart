import 'package:app/src/state/task_controller.dart';
import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/helpers.dart';
import 'package:flutter/material.dart';

class JarvisAppBar extends StatelessWidget implements PreferredSizeWidget {
  const JarvisAppBar({
    super.key,
    required this.isWide,
    required this.controller,
    required this.selectedDeviceId,
    required this.onOpenMenu,
    required this.onOpenSettings,
  });

  final bool isWide;
  final TaskController controller;
  final String? selectedDeviceId;
  final VoidCallback onOpenMenu;
  final VoidCallback onOpenSettings;

  @override
  Size get preferredSize => const Size.fromHeight(72);

  @override
  Widget build(BuildContext context) {
    final tokens = JarvisThemeTokens.of(context);
    final onlineCount = controller.devices
        .where((device) => device.connected)
        .length;

    return AppBar(
      leading: isWide
          ? null
          : IconButton(
              key: const Key('appBarMenuButton'),
              tooltip: '线程列表',
              onPressed: onOpenMenu,
              icon: const Icon(Icons.menu_rounded),
            ),
      title: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text('OpenJarvis', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 2),
          Text(
            selectedDeviceId == null
                ? 'AI 任务控制台'
                : '当前设备 $selectedDeviceId',
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
      actions: [
        Padding(
          padding: const EdgeInsets.only(right: 8),
          child: Center(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
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
          ),
        ),
        IconButton(
          key: const Key('appBarSettingsButton'),
          tooltip: '连接设置',
          onPressed: onOpenSettings,
          icon: const Icon(Icons.tune_rounded),
        ),
        const SizedBox(width: 8),
      ],
    );
  }
}
