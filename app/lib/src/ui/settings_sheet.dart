import 'package:app/src/state/task_controller.dart';
import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/components/glass_card.dart';
import 'package:app/src/ui/components/labeled_field.dart';
import 'package:app/src/ui/components/metric_chip.dart';
import 'package:app/src/ui/helpers.dart';
import 'package:flutter/material.dart';

class SettingsSheet extends StatefulWidget {
  const SettingsSheet({
    super.key,
    required this.controller,
    required this.baseUrlController,
    required this.usernameController,
    required this.passwordController,
    required this.onConnect,
    required this.onReconnect,
    required this.onRefresh,
  });

  final TaskController controller;
  final TextEditingController baseUrlController;
  final TextEditingController usernameController;
  final TextEditingController passwordController;
  final Future<void> Function() onConnect;
  final Future<void> Function() onReconnect;
  final Future<void> Function() onRefresh;

  @override
  State<SettingsSheet> createState() => _SettingsSheetState();
}

class _SettingsSheetState extends State<SettingsSheet> {
  late bool _isEditing = !widget.controller.hasSavedSession;

  TaskController get controller => widget.controller;

  @override
  Widget build(BuildContext context) {
    final tokens = JarvisThemeTokens.of(context);
    final insets = MediaQuery.viewInsetsOf(context);

    return AnimatedBuilder(
      animation: controller,
      builder: (context, _) {
        final hasSavedSession = controller.hasSavedSession;
        final showEditForm = _isEditing || !hasSavedSession;

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
                              showEditForm ? '连接设置' : '当前连接',
                              style: Theme.of(context).textTheme.headlineSmall,
                            ),
                            const SizedBox(height: 6),
                            Text(
                              showEditForm
                                  ? '填写服务器、账号和密码。'
                                  : '查看当前连接并同步任务。',
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
                  if (!showEditForm) ...[
                    _ConnectionSummary(
                      controller: controller,
                      onEdit: () {
                        setState(() {
                          _isEditing = true;
                        });
                      },
                      onReconnect: widget.onReconnect,
                      onRefresh: widget.onRefresh,
                    ),
                  ] else ...[
                    LabeledField(
                      label: 'Gateway URL',
                      child: TextField(
                        key: const Key('settingsBaseUrlField'),
                        controller: widget.baseUrlController,
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
                        controller: widget.usernameController,
                        decoration: const InputDecoration(hintText: 'operator'),
                      ),
                    ),
                    const SizedBox(height: 14),
                    LabeledField(
                      label: '密码',
                      child: TextField(
                        key: const Key('settingsPasswordField'),
                        controller: widget.passwordController,
                        obscureText: true,
                        decoration: const InputDecoration(hintText: 'passw0rd'),
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
                        style: Theme.of(
                          context,
                        ).textTheme.bodySmall?.copyWith(color: tokens.danger),
                      ),
                    ],
                    const SizedBox(height: 24),
                    Row(
                      children: [
                        if (hasSavedSession) ...[
                          Expanded(
                            child: OutlinedButton(
                              key: const Key('settingsBackButton'),
                              onPressed: () {
                                setState(() {
                                  _isEditing = false;
                                });
                              },
                              child: const Text('返回当前连接'),
                            ),
                          ),
                          const SizedBox(width: 12),
                        ],
                        Expanded(
                          child: FilledButton(
                            key: const Key('settingsConnectButton'),
                            onPressed:
                                controller.status == ConnectionStatus.connecting
                                ? null
                                : widget.onConnect,
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
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}

class _ConnectionSummary extends StatelessWidget {
  const _ConnectionSummary({
    required this.controller,
    required this.onEdit,
    required this.onReconnect,
    required this.onRefresh,
  });

  final TaskController controller;
  final VoidCallback onEdit;
  final Future<void> Function() onReconnect;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) {
    final tokens = JarvisThemeTokens.of(context);
    final shapes = JarvisShapeTokens.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          key: const Key('settingsConnectionSummary'),
          width: double.infinity,
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: tokens.surface,
            borderRadius: shapes.lg,
            border: Border.all(color: tokens.border),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
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
              const SizedBox(height: 16),
              _ConnectionDetail(
                label: '服务器',
                value: controller.savedBaseUrl ?? '未设置',
              ),
              const SizedBox(height: 12),
              _ConnectionDetail(
                label: '账号',
                value: controller.savedUsername ?? '未设置',
              ),
            ],
          ),
        ),
        if (controller.errorMessage case final error?) ...[
          const SizedBox(height: 12),
          Text(
            error,
            style: Theme.of(
              context,
            ).textTheme.bodySmall?.copyWith(color: tokens.danger),
          ),
        ],
        if (controller.token != null) ...[
          const SizedBox(height: 12),
          TextButton.icon(
            key: const Key('settingsRefreshButton'),
            onPressed: onRefresh,
            icon: const Icon(Icons.sync_rounded),
            label: const Text('同步任务'),
          ),
        ],
        const SizedBox(height: 16),
        Row(
          children: [
            Expanded(
              child: OutlinedButton(
                key: const Key('settingsEditConnectionButton'),
                onPressed: onEdit,
                child: const Text('修改连接'),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: FilledButton(
                key: const Key('settingsReconnectButton'),
                onPressed:
                    controller.status == ConnectionStatus.connecting ||
                        !controller.canReconnect
                    ? null
                    : onReconnect,
                child: Text(
                  controller.status == ConnectionStatus.connected
                      ? '重新连接'
                      : '连接当前配置',
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }
}

class _ConnectionDetail extends StatelessWidget {
  const _ConnectionDetail({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: Theme.of(context).textTheme.labelMedium),
        const SizedBox(height: 4),
        Text(value, style: Theme.of(context).textTheme.bodyLarge),
      ],
    );
  }
}
