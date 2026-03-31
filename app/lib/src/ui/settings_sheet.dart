import 'package:app/src/state/task_controller.dart';
import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/components/glass_card.dart';
import 'package:app/src/ui/components/labeled_field.dart';
import 'package:app/src/ui/components/metric_chip.dart';
import 'package:app/src/ui/helpers.dart';
import 'package:flutter/material.dart';

class SettingsSheet extends StatelessWidget {
  const SettingsSheet({
    super.key,
    required this.controller,
    required this.baseUrlController,
    required this.usernameController,
    required this.passwordController,
    required this.onConnect,
    required this.onRefresh,
  });

  final TaskController controller;
  final TextEditingController baseUrlController;
  final TextEditingController usernameController;
  final TextEditingController passwordController;
  final Future<void> Function() onConnect;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) {
    final tokens = JarvisThemeTokens.of(context);
    final insets = MediaQuery.viewInsetsOf(context);

    return AnimatedBuilder(
      animation: controller,
      builder: (context, _) {
        return Padding(
          padding: EdgeInsets.fromLTRB(20, 12, 20, insets.bottom + 20),
          child: GlassCard(
            padding: const EdgeInsets.all(24),
            backgroundColor: tokens.shellRaised,
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '连接设置',
                              style:
                                  Theme.of(context).textTheme.headlineSmall,
                            ),
                            const SizedBox(height: 6),
                            Text(
                              '配置网关地址和账号后，聊天线程会沿用同一条连接。',
                              style: Theme.of(context).textTheme.bodyMedium,
                            ),
                          ],
                        ),
                      ),
                      IconButton(
                        onPressed: () => Navigator.of(context).pop(),
                        icon: const Icon(Icons.close_rounded),
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),
                  LabeledField(
                    label: 'Gateway URL',
                    child: TextField(
                      key: const Key('settingsBaseUrlField'),
                      controller: baseUrlController,
                      decoration: const InputDecoration(
                        hintText: 'http://127.0.0.1:8000',
                      ),
                    ),
                  ),
                  const SizedBox(height: 14),
                  LabeledField(
                    label: '用户名',
                    child: TextField(
                      key: const Key('settingsUsernameField'),
                      controller: usernameController,
                      decoration:
                          const InputDecoration(hintText: 'operator'),
                    ),
                  ),
                  const SizedBox(height: 14),
                  LabeledField(
                    label: '密码',
                    child: TextField(
                      key: const Key('settingsPasswordField'),
                      controller: passwordController,
                      obscureText: true,
                      decoration:
                          const InputDecoration(hintText: 'passw0rd'),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      MetricChip(
                        icon: Icons.wifi_tethering_rounded,
                        label: connectionStatusLabel(controller.status),
                      ),
                      MetricChip(
                        icon: Icons.devices_rounded,
                        label:
                            '${controller.devices.where((device) => device.connected).length} 台在线设备',
                      ),
                    ],
                  ),
                  if (controller.errorMessage case final error?) ...[
                    const SizedBox(height: 12),
                    Text(
                      error,
                      style: Theme.of(context)
                          .textTheme
                          .bodySmall
                          ?.copyWith(color: tokens.danger),
                    ),
                  ],
                  const SizedBox(height: 24),
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton(
                          onPressed:
                              controller.token == null ? null : onRefresh,
                          child: const Text('同步任务'),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: FilledButton(
                          key: const Key('settingsConnectButton'),
                          onPressed:
                              controller.status == ConnectionStatus.connecting
                              ? null
                              : onConnect,
                          child: Text(
                            controller.status == ConnectionStatus.connected
                                ? '保存并重连'
                                : '保存并连接',
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}
