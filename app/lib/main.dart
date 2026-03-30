import 'package:app/src/models/task_record.dart';
import 'package:app/src/services/gateway_api.dart';
import 'package:app/src/services/gateway_socket.dart';
import 'package:app/src/state/task_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_highlight/flutter_highlight.dart';
import 'package:flutter_highlight/themes/github.dart';
import 'package:google_fonts/google_fonts.dart';

void main() {
  runApp(const OmniAgentApp());
}

class OmniAgentApp extends StatefulWidget {
  const OmniAgentApp({super.key, this.controller});

  final TaskController? controller;

  @override
  State<OmniAgentApp> createState() => _OmniAgentAppState();
}

class _OmniAgentAppState extends State<OmniAgentApp> {
  late final TaskController _controller =
      widget.controller ??
      TaskController(api: HttpGatewayApi(), socket: ChannelGatewaySocket());

  @override
  void dispose() {
    if (widget.controller == null) {
      _controller.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final baseTextTheme = GoogleFonts.interTextTheme();
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'OpenJarvis',
      theme: ThemeData(
        useMaterial3: true,
        scaffoldBackgroundColor: _ChatPalette.pageBackground,
        colorScheme: const ColorScheme.light(
          primary: _ChatPalette.primary,
          onPrimary: Colors.white,
          secondary: _ChatPalette.primarySoft,
          onSecondary: _ChatPalette.textPrimary,
          surface: _ChatPalette.shellBackground,
          onSurface: _ChatPalette.textPrimary,
          error: _ChatPalette.danger,
          onError: Colors.white,
        ),
        dividerColor: _ChatPalette.border,
        textTheme: baseTextTheme.copyWith(
          displayMedium: baseTextTheme.displayMedium?.copyWith(
            fontSize: 32,
            fontWeight: FontWeight.w700,
            color: _ChatPalette.textPrimary,
            height: 1.12,
          ),
          displaySmall: baseTextTheme.displaySmall?.copyWith(
            fontSize: 24,
            fontWeight: FontWeight.w700,
            color: _ChatPalette.textPrimary,
            height: 1.2,
          ),
          headlineSmall: baseTextTheme.headlineSmall?.copyWith(
            fontSize: 20,
            fontWeight: FontWeight.w700,
            color: _ChatPalette.textPrimary,
          ),
          titleLarge: baseTextTheme.titleLarge?.copyWith(
            fontWeight: FontWeight.w700,
            color: _ChatPalette.textPrimary,
          ),
          titleMedium: baseTextTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w600,
            color: _ChatPalette.textPrimary,
          ),
          bodyLarge: baseTextTheme.bodyLarge?.copyWith(
            color: _ChatPalette.textPrimary,
            height: 1.55,
          ),
          bodyMedium: baseTextTheme.bodyMedium?.copyWith(
            color: _ChatPalette.textPrimary,
            height: 1.5,
          ),
          bodySmall: baseTextTheme.bodySmall?.copyWith(
            color: _ChatPalette.textMuted,
            height: 1.45,
          ),
          labelLarge: baseTextTheme.labelLarge?.copyWith(
            color: _ChatPalette.textMuted,
            fontWeight: FontWeight.w600,
          ),
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: _ChatPalette.cardSubtle,
          hintStyle: baseTextTheme.bodyMedium?.copyWith(
            color: _ChatPalette.textMuted,
          ),
          contentPadding: const EdgeInsets.symmetric(
            horizontal: 16,
            vertical: 16,
          ),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(18),
            borderSide: const BorderSide(color: _ChatPalette.border),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(18),
            borderSide: const BorderSide(color: _ChatPalette.border),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(18),
            borderSide: const BorderSide(
              color: _ChatPalette.primary,
              width: 1.2,
            ),
          ),
        ),
        filledButtonTheme: FilledButtonThemeData(
          style: FilledButton.styleFrom(
            backgroundColor: _ChatPalette.primary,
            foregroundColor: Colors.white,
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(18),
            ),
          ),
        ),
        outlinedButtonTheme: OutlinedButtonThemeData(
          style: OutlinedButton.styleFrom(
            foregroundColor: _ChatPalette.textPrimary,
            side: const BorderSide(color: _ChatPalette.border),
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(18),
            ),
          ),
        ),
      ),
      home: OmniAgentHome(controller: _controller),
    );
  }
}

class OmniAgentHome extends StatefulWidget {
  const OmniAgentHome({super.key, required this.controller});

  final TaskController controller;

  @override
  State<OmniAgentHome> createState() => _OmniAgentHomeState();
}

class _OmniAgentHomeState extends State<OmniAgentHome> {
  final _baseUrlController = TextEditingController(
    text: 'http://127.0.0.1:8000',
  );
  final _usernameController = TextEditingController(text: 'operator');
  final _passwordController = TextEditingController(text: 'passw0rd');
  final _composerController = TextEditingController();
  String? _selectedDeviceId;

  TaskController get controller => widget.controller;

  @override
  void dispose() {
    _baseUrlController.dispose();
    _usernameController.dispose();
    _passwordController.dispose();
    _composerController.dispose();
    super.dispose();
  }

  Future<void> _connectGateway() async {
    await controller.connect(
      baseUrl: _baseUrlController.text.trim(),
      username: _usernameController.text.trim(),
      password: _passwordController.text,
    );
  }

  Future<void> _openSettings() async {
    await showDialog<void>(
      context: context,
      builder: (dialogContext) => _SettingsDialog(
        controller: controller,
        baseUrlController: _baseUrlController,
        usernameController: _usernameController,
        passwordController: _passwordController,
        onConnect: () async {
          await _connectGateway();
          if (!mounted || !dialogContext.mounted) {
            return;
          }
          if (controller.status == ConnectionStatus.connected) {
            Navigator.of(dialogContext).pop();
          }
        },
        onRefresh: controller.refresh,
      ),
    );
  }

  Future<void> _sendInstruction() async {
    final instruction = _composerController.text.trim();
    final deviceId = _selectedDeviceId;
    if (instruction.isEmpty || deviceId == null) {
      return;
    }
    await controller.createTask(deviceId: deviceId, instruction: instruction);
    _composerController.clear();
    if (mounted) {
      setState(() {});
      FocusScope.of(context).unfocus();
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: controller,
      builder: (context, _) {
        final availableDeviceIds = controller.devices
            .map((device) => device.deviceId)
            .toSet();
        if (_selectedDeviceId != null &&
            !availableDeviceIds.contains(_selectedDeviceId)) {
          _selectedDeviceId = null;
        }
        _selectedDeviceId ??= controller.devices.isNotEmpty
            ? controller.devices.first.deviceId
            : null;

        return Scaffold(
          body: DecoratedBox(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [Color(0xFFF8F8F5), Color(0xFFF3F5F7)],
              ),
            ),
            child: Stack(
              children: [
                Positioned(
                  top: -80,
                  right: -40,
                  child: IgnorePointer(
                    child: Container(
                      width: 260,
                      height: 260,
                      decoration: const BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: RadialGradient(
                          colors: [Color(0x1419C37D), Color(0x0019C37D)],
                        ),
                      ),
                    ),
                  ),
                ),
                Positioned(
                  bottom: -120,
                  left: -60,
                  child: IgnorePointer(
                    child: Container(
                      width: 300,
                      height: 300,
                      decoration: const BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: RadialGradient(
                          colors: [Color(0x10256BFA), Color(0x00256BFA)],
                        ),
                      ),
                    ),
                  ),
                ),
                SafeArea(
                  child: Center(
                    child: ConstrainedBox(
                      constraints: const BoxConstraints(maxWidth: 1280),
                      child: Padding(
                        padding: const EdgeInsets.all(20),
                        child: _AppShell(
                          child: LayoutBuilder(
                            builder: (context, constraints) {
                              final isWide = constraints.maxWidth >= 1100;
                              final sidebar = _SidebarPanel(
                                controller: controller,
                                selectedDeviceId: _selectedDeviceId,
                                onOpenSettings: () {
                                  _openSettings();
                                },
                                onClearSelection: controller.clearSelection,
                                onDeviceChanged: (value) {
                                  setState(() {
                                    _selectedDeviceId = value;
                                  });
                                },
                              );
                              final conversation = _ConversationPanel(
                                controller: controller,
                                composerController: _composerController,
                                selectedDeviceId: _selectedDeviceId,
                                onComposerChanged: () => setState(() {}),
                                onSend: _sendInstruction,
                              );

                              if (!isWide) {
                                return Column(
                                  children: [
                                    SizedBox(height: 360, child: sidebar),
                                    const SizedBox(height: 16),
                                    Expanded(child: conversation),
                                  ],
                                );
                              }

                              return Row(
                                crossAxisAlignment: CrossAxisAlignment.stretch,
                                children: [
                                  SizedBox(width: 320, child: sidebar),
                                  const SizedBox(width: 20),
                                  Expanded(child: conversation),
                                ],
                              );
                            },
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _AppShell extends StatelessWidget {
  const _AppShell({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: _ChatPalette.shellBackground.withValues(alpha: 0.94),
        borderRadius: BorderRadius.circular(30),
        border: Border.all(color: _ChatPalette.border),
        boxShadow: const [
          BoxShadow(
            color: Color(0x140F172A),
            blurRadius: 32,
            offset: Offset(0, 18),
          ),
        ],
      ),
      child: child,
    );
  }
}

class _SidebarPanel extends StatelessWidget {
  const _SidebarPanel({
    required this.controller,
    required this.selectedDeviceId,
    required this.onOpenSettings,
    required this.onClearSelection,
    required this.onDeviceChanged,
  });

  final TaskController controller;
  final String? selectedDeviceId;
  final VoidCallback onOpenSettings;
  final VoidCallback onClearSelection;
  final ValueChanged<String?> onDeviceChanged;

  @override
  Widget build(BuildContext context) {
    final pendingHistory = controller.tasks
        .where((task) => task.status == TaskStatus.awaitingApproval)
        .toList(growable: false);
    final recentHistory = controller.tasks
        .where((task) => task.status != TaskStatus.awaitingApproval)
        .toList(growable: false);

    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _SidebarBrand(controller: controller),
          const SizedBox(height: 12),
          FilledButton.icon(
            key: const Key('sidebarNewChatButton'),
            onPressed: onClearSelection,
            icon: const Icon(Icons.add_comment_outlined),
            label: const Text('新对话'),
          ),
          const SizedBox(height: 12),
          _SectionCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const _SectionTitle(
                  title: '当前路由',
                  body: '你的消息会通过这里选择的客户端进入执行链路。',
                ),
                const SizedBox(height: 14),
                Row(
                  children: [
                    Expanded(
                      child: _StatusBadge(
                        label:
                            '${controller.devices.where((device) => device.connected).length} 台在线设备',
                        color: _ChatPalette.primary,
                      ),
                    ),
                    const SizedBox(width: 10),
                    _StatusBadge(
                      label: '${controller.pendingTasks.length} 待审批',
                      color: _ChatPalette.warning,
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                DropdownButtonFormField<String>(
                  key: ValueKey<String?>(selectedDeviceId),
                  initialValue: selectedDeviceId,
                  isExpanded: true,
                  decoration: const InputDecoration(hintText: '选择设备'),
                  items: controller.devices
                      .map(
                        (device) => DropdownMenuItem<String>(
                          value: device.deviceId,
                          child: Text(
                            device.connected
                                ? '${device.deviceId} · 在线'
                                : '${device.deviceId} · 离线',
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      )
                      .toList(growable: false),
                  onChanged: onDeviceChanged,
                ),
                const SizedBox(height: 12),
                Text(
                  selectedDeviceId == null
                      ? '暂无可用设备，先在设置里完成服务端连接。'
                      : '当前设备：$selectedDeviceId',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),
          Expanded(
            child: Scrollbar(
              child: ListView(
                padding: EdgeInsets.zero,
                children: [
                  if (controller.tasks.isEmpty)
                    const _SidebarEmptyState()
                  else ...[
                    if (pendingHistory.isNotEmpty)
                      _HistorySection(
                        title: '待处理',
                        body: '优先处理需要确认的线程。',
                        tasks: pendingHistory,
                        selectedTaskId: controller.selectedTask?.taskId,
                        onTaskTap: controller.selectTask,
                      ),
                    if (pendingHistory.isNotEmpty && recentHistory.isNotEmpty)
                      const SizedBox(height: 14),
                    if (recentHistory.isNotEmpty)
                      _HistorySection(
                        title: '最近聊天',
                        body: '最近执行过的任务和对话线程。',
                        tasks: recentHistory,
                        selectedTaskId: controller.selectedTask?.taskId,
                        onTaskTap: controller.selectTask,
                      ),
                  ],
                ],
              ),
            ),
          ),
          const SizedBox(height: 14),
          _SidebarFooter(
            controller: controller,
            selectedDeviceId: selectedDeviceId,
            onOpenSettings: onOpenSettings,
          ),
        ],
      ),
    );
  }
}

class _SidebarBrand extends StatelessWidget {
  const _SidebarBrand({required this.controller});

  final TaskController controller;

  @override
  Widget build(BuildContext context) {
    return _SectionCard(
      padding: const EdgeInsets.all(18),
      child: Row(
        children: [
          Container(
            width: 46,
            height: 46,
            decoration: BoxDecoration(
              color: _ChatPalette.primary.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(14),
            ),
            child: const Icon(
              Icons.auto_awesome_outlined,
              color: _ChatPalette.primary,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'OpenJarvis',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 4),
                Text(
                  'AI 执行与审批终端',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
          _StatusBadge(
            label: _connectionStatusLabel(controller.status),
            color: _connectionStatusColor(controller.status),
          ),
        ],
      ),
    );
  }
}

class _HistorySection extends StatelessWidget {
  const _HistorySection({
    required this.title,
    required this.body,
    required this.tasks,
    required this.selectedTaskId,
    required this.onTaskTap,
  });

  final String title;
  final String body;
  final List<TaskRecord> tasks;
  final String? selectedTaskId;
  final ValueChanged<String> onTaskTap;

  @override
  Widget build(BuildContext context) {
    return _SectionCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 6),
          Text(body, style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(height: 16),
          ...tasks.map(
            (task) => Padding(
              padding: EdgeInsets.only(bottom: task == tasks.last ? 0 : 10),
              child: _TaskThreadTile(
                task: task,
                selected: selectedTaskId == task.taskId,
                onTap: () => onTaskTap(task.taskId),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _SidebarFooter extends StatelessWidget {
  const _SidebarFooter({
    required this.controller,
    required this.selectedDeviceId,
    required this.onOpenSettings,
  });

  final TaskController controller;
  final String? selectedDeviceId;
  final VoidCallback onOpenSettings;

  @override
  Widget build(BuildContext context) {
    final serverStatus = switch (controller.status) {
      ConnectionStatus.connected => '服务端已连接',
      ConnectionStatus.connecting => '正在连接服务端',
      ConnectionStatus.failed => '服务端连接异常',
      ConnectionStatus.idle => '尚未连接服务端',
    };

    return _SectionCard(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  serverStatus,
                  style: Theme.of(context).textTheme.labelLarge,
                ),
                const SizedBox(height: 4),
                Text(
                  selectedDeviceId == null
                      ? '在设置里配置服务端后开始新会话。'
                      : '当前默认使用 $selectedDeviceId 发起新会话。',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
          IconButton(
            key: const Key('sidebarSettingsButton'),
            tooltip: '设置',
            onPressed: onOpenSettings,
            style: IconButton.styleFrom(
              backgroundColor: _ChatPalette.cardSubtle,
              foregroundColor: _ChatPalette.textPrimary,
            ),
            icon: const Icon(Icons.tune_outlined),
          ),
        ],
      ),
    );
  }
}

class _SettingsDialog extends StatelessWidget {
  const _SettingsDialog({
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
    return AnimatedBuilder(
      animation: controller,
      builder: (context, _) {
        return AlertDialog(
          title: Text('设置', style: Theme.of(context).textTheme.titleLarge),
          content: SizedBox(
            width: 440,
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const _SectionTitle(
                    title: '服务端配置',
                    body: '在这里配置网关地址和登录信息，保存后左侧历史聊天会继续复用同一条连接。',
                  ),
                  const SizedBox(height: 18),
                  _LabeledField(
                    label: 'Gateway URL',
                    child: TextField(
                      key: const Key('settingsBaseUrlField'),
                      controller: baseUrlController,
                      decoration: const InputDecoration(
                        hintText: 'http://127.0.0.1:8000',
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  _LabeledField(
                    label: '用户名',
                    child: TextField(
                      key: const Key('settingsUsernameField'),
                      controller: usernameController,
                      decoration: const InputDecoration(hintText: 'operator'),
                    ),
                  ),
                  const SizedBox(height: 12),
                  _LabeledField(
                    label: '密码',
                    child: TextField(
                      key: const Key('settingsPasswordField'),
                      controller: passwordController,
                      obscureText: true,
                      decoration: const InputDecoration(hintText: 'passw0rd'),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Wrap(
                    spacing: 10,
                    runSpacing: 10,
                    children: [
                      _MetaChip(
                        icon: Icons.wifi_tethering_outlined,
                        label: _connectionStatusLabel(controller.status),
                      ),
                      _MetaChip(
                        icon: Icons.devices_outlined,
                        label:
                            '${controller.devices.where((device) => device.connected).length} 台在线设备',
                      ),
                    ],
                  ),
                  if (controller.errorMessage case final error?) ...[
                    const SizedBox(height: 12),
                    Text(
                      error,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: _ChatPalette.danger,
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('关闭'),
            ),
            TextButton(
              onPressed: controller.token == null
                  ? null
                  : () {
                      onRefresh();
                    },
              child: const Text('同步任务'),
            ),
            FilledButton.icon(
              key: const Key('settingsConnectButton'),
              onPressed: controller.status == ConnectionStatus.connecting
                  ? null
                  : () {
                      onConnect();
                    },
              icon: const Icon(Icons.hub_outlined),
              label: Text(
                controller.status == ConnectionStatus.connected
                    ? '保存并重连'
                    : '保存并连接',
              ),
            ),
          ],
        );
      },
    );
  }
}

class _ConversationPanel extends StatelessWidget {
  const _ConversationPanel({
    required this.controller,
    required this.composerController,
    required this.selectedDeviceId,
    required this.onComposerChanged,
    required this.onSend,
  });

  final TaskController controller;
  final TextEditingController composerController;
  final String? selectedDeviceId;
  final VoidCallback onComposerChanged;
  final Future<void> Function() onSend;

  @override
  Widget build(BuildContext context) {
    final task = controller.selectedTask;
    final canSend =
        controller.status == ConnectionStatus.connected &&
        selectedDeviceId != null;

    return Padding(
      padding: const EdgeInsets.fromLTRB(0, 20, 20, 20),
      child: _SectionCard(
        padding: EdgeInsets.zero,
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 22, 24, 18),
              child: _ConversationHeader(
                controller: controller,
                selectedDeviceId: selectedDeviceId,
                selectedTask: task,
              ),
            ),
            const Divider(height: 1),
            Expanded(
              child: task == null
                  ? _ConversationEmptyState(
                      controller: controller,
                      selectedDeviceId: selectedDeviceId,
                    )
                  : _ConversationTimeline(controller: controller, task: task),
            ),
            const Divider(height: 1),
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 18, 24, 24),
              child: Column(
                children: [
                  Row(
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
                          maxLines: 4,
                          decoration: InputDecoration(
                            hintText:
                                controller.status == ConnectionStatus.connected
                                ? '给 AI 下达任务，过程、审批和恢复都会回到这个对话里'
                                : '先连接网关，再开始对话',
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      FilledButton(
                        key: const Key('chatSendButton'),
                        onPressed: canSend ? onSend : null,
                        child: const Text('发送'),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  Align(
                    alignment: Alignment.centerLeft,
                    child: Text(
                      selectedDeviceId == null
                          ? '未选择设备，暂时无法发送。'
                          : '当前会话会通过 $selectedDeviceId 与客户端协同。',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ConversationHeader extends StatelessWidget {
  const _ConversationHeader({
    required this.controller,
    required this.selectedDeviceId,
    required this.selectedTask,
  });

  final TaskController controller;
  final String? selectedDeviceId;
  final TaskRecord? selectedTask;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '连接网关后的 AI 对话',
                    style: Theme.of(context).textTheme.displaySmall,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    selectedTask == null
                        ? '默认进入对话框。直接发送任务，AI 的执行过程、二次确认和恢复状态都会在这里连续展示。'
                        : '当前查看的是一段任务会话，右下角可以继续追问或发起新任务。',
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: _ChatPalette.textMuted,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 16),
            _StatusBadge(
              label: _connectionStatusLabel(controller.status),
              color: _connectionStatusColor(controller.status),
            ),
          ],
        ),
        const SizedBox(height: 18),
        Wrap(
          spacing: 10,
          runSpacing: 10,
          children: [
            _MetaChip(
              icon: Icons.pending_actions_outlined,
              label: '${controller.pendingTasks.length} 个待审批',
            ),
            _MetaChip(
              icon: Icons.devices_outlined,
              label:
                  '${controller.devices.where((device) => device.connected).length} 台在线设备',
            ),
            _MetaChip(
              icon: Icons.route_outlined,
              label: selectedDeviceId == null
                  ? '未选设备'
                  : '当前设备 $selectedDeviceId',
            ),
            if (selectedTask?.checkpointId case final checkpointId?)
              _MetaChip(
                icon: Icons.restore_outlined,
                label: '检查点 $checkpointId',
              ),
          ],
        ),
      ],
    );
  }
}

class _ConversationEmptyState extends StatelessWidget {
  const _ConversationEmptyState({
    required this.controller,
    required this.selectedDeviceId,
  });

  final TaskController controller;
  final String? selectedDeviceId;

  @override
  Widget build(BuildContext context) {
    final cards = [
      const _HintCard(
        icon: Icons.send_to_mobile_outlined,
        title: '任务下发',
        body: '在输入框直接给 AI 下指令，系统会自动路由到所选客户端。',
      ),
      const _HintCard(
        icon: Icons.shield_outlined,
        title: '会话内审批',
        body: '敏感操作触发后会在对话里出现确认卡片，无需切换页面。',
      ),
      const _HintCard(
        icon: Icons.terminal_outlined,
        title: '实时过程',
        body: '运行日志和恢复状态持续回流到同一条会话，便于追踪上下文。',
      ),
    ];

    return SingleChildScrollView(
      padding: const EdgeInsets.all(32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 52,
            height: 52,
            decoration: BoxDecoration(
              color: _ChatPalette.primary.withValues(alpha: 0.08),
              borderRadius: BorderRadius.circular(18),
            ),
            child: const Icon(
              Icons.chat_bubble_outline,
              color: _ChatPalette.primary,
            ),
          ),
          const SizedBox(height: 20),
          Text(
            '现在可以直接向 AI 下发任务',
            style: Theme.of(context).textTheme.displayMedium,
          ),
          const SizedBox(height: 12),
          Text(
            controller.status == ConnectionStatus.connected
                ? selectedDeviceId == null
                      ? '网关已连接，但还没有可用设备。设备上线后即可开始会话。'
                      : '默认进入普通对话模式。选择设备后，直接在下方输入框发起任务。'
                : '连接网关后，这里会自动切到聊天工作区，并恢复所有离线待审批任务。',
            style: Theme.of(
              context,
            ).textTheme.bodyLarge?.copyWith(color: _ChatPalette.textMuted),
          ),
          const SizedBox(height: 28),
          Wrap(
            spacing: 14,
            runSpacing: 14,
            children: cards
                .map((card) => SizedBox(width: 240, child: card))
                .toList(growable: false),
          ),
        ],
      ),
    );
  }
}

class _ConversationTimeline extends StatelessWidget {
  const _ConversationTimeline({required this.controller, required this.task});

  final TaskController controller;
  final TaskRecord task;

  @override
  Widget build(BuildContext context) {
    return Scrollbar(
      child: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          _SystemNotice(
            message: '会话已绑定到 ${task.deviceId}，后续日志、审批结果与恢复状态都会回流到这里。',
          ),
          const SizedBox(height: 18),
          _ChatBubble(
            alignment: Alignment.centerRight,
            tone: _BubbleTone.user,
            header: '你',
            body: task.instruction,
            footer: '已发送给 ${task.deviceId}',
          ),
          const SizedBox(height: 18),
          _ChatBubble(
            alignment: Alignment.centerLeft,
            tone: _BubbleTone.assistant,
            header: 'AI',
            body: _taskNarrative(task),
            footer: task.status.label,
          ),
          const SizedBox(height: 18),
          _ProcessCard(task: task),
          if (task.command != null ||
              task.reason != null ||
              task.checkpointId != null) ...[
            const SizedBox(height: 18),
            _ApprovalCard(controller: controller, task: task),
          ],
          if (task.result case final result?) ...[
            const SizedBox(height: 18),
            _ChatBubble(
              alignment: Alignment.centerLeft,
              tone: _BubbleTone.success,
              header: '执行结果',
              body: result,
            ),
          ],
          if (task.error case final error?) ...[
            const SizedBox(height: 18),
            _ChatBubble(
              alignment: Alignment.centerLeft,
              tone: _BubbleTone.danger,
              header: '错误',
              body: error,
            ),
          ],
        ],
      ),
    );
  }
}

class _ProcessCard extends StatelessWidget {
  const _ProcessCard({required this.task});

  final TaskRecord task;

  @override
  Widget build(BuildContext context) {
    final entries = <String>[
      '任务已下发到 ${task.deviceId}',
      '当前状态：${task.status.label}',
      if (task.checkpointId case final checkpointId?) '已写入检查点 $checkpointId',
      ...task.logs,
    ];

    return _TimelineCard(
      title: 'AI 操作过程',
      subtitle: '会话持续展示当前阶段与最新执行日志。',
      child: Column(
        children: [
          for (var index = 0; index < entries.length; index++)
            Padding(
              padding: EdgeInsets.only(
                bottom: index == entries.length - 1 ? 0 : 12,
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 22,
                    height: 22,
                    margin: const EdgeInsets.only(top: 2),
                    decoration: BoxDecoration(
                      color: index == entries.length - 1
                          ? _ChatPalette.primary.withValues(alpha: 0.12)
                          : _ChatPalette.cardSubtle,
                      borderRadius: BorderRadius.circular(999),
                    ),
                    child: Center(
                      child: Text(
                        '${index + 1}',
                        style: Theme.of(context).textTheme.labelLarge?.copyWith(
                          color: index == entries.length - 1
                              ? _ChatPalette.primary
                              : _ChatPalette.textMuted,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      entries[index],
                      style: GoogleFonts.ibmPlexMono(
                        fontSize: 13,
                        height: 1.5,
                        color: index == entries.length - 1
                            ? _ChatPalette.textPrimary
                            : _ChatPalette.textMuted,
                      ),
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

class _ApprovalCard extends StatelessWidget {
  const _ApprovalCard({required this.controller, required this.task});

  final TaskController controller;
  final TaskRecord task;

  @override
  Widget build(BuildContext context) {
    return _TimelineCard(
      title: '需要二次确认',
      subtitle: '敏感操作已暂停，确认后客户端会从检查点恢复。',
      accent: _ChatPalette.warning,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            task.reason ?? 'AI 认为当前操作具有潜在风险，请先确认。',
            style: Theme.of(context).textTheme.bodyLarge,
          ),
          if (task.command case final command?) ...[
            const SizedBox(height: 16),
            SelectableText(
              command,
              style: GoogleFonts.ibmPlexMono(
                fontSize: 13,
                height: 1.5,
                color: _ChatPalette.textPrimary,
              ),
            ),
            const SizedBox(height: 12),
            Container(
              decoration: BoxDecoration(
                color: const Color(0xFFF8FAFC),
                borderRadius: BorderRadius.circular(18),
                border: Border.all(color: _ChatPalette.border),
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(18),
                child: HighlightView(
                  command,
                  language: 'bash',
                  theme: githubTheme,
                  padding: const EdgeInsets.all(18),
                  textStyle: GoogleFonts.ibmPlexMono(fontSize: 13, height: 1.5),
                ),
              ),
            ),
          ],
          if (task.checkpointId case final checkpointId?) ...[
            const SizedBox(height: 12),
            Text(
              '恢复检查点 $checkpointId',
              style: Theme.of(
                context,
              ).textTheme.bodySmall?.copyWith(color: _ChatPalette.textMuted),
            ),
          ],
          const SizedBox(height: 18),
          if (task.isAwaitingApproval)
            Wrap(
              spacing: 12,
              runSpacing: 12,
              children: [
                FilledButton(
                  onPressed: () => controller.submitDecision(true),
                  child: const Text('确认执行'),
                ),
                OutlinedButton(
                  onPressed: () => controller.submitDecision(false),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: _ChatPalette.danger,
                    side: const BorderSide(color: _ChatPalette.dangerSoft),
                  ),
                  child: const Text('拒绝执行'),
                ),
              ],
            )
          else
            _StatusBadge(
              label: task.status.label,
              color: _taskStatusColor(task.status),
            ),
        ],
      ),
    );
  }
}

class _TimelineCard extends StatelessWidget {
  const _TimelineCard({
    required this.title,
    required this.subtitle,
    required this.child,
    this.accent = _ChatPalette.primary,
  });

  final String title;
  final String subtitle;
  final Widget child;
  final Color accent;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: _ChatPalette.shellBackground,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: accent.withValues(alpha: 0.18)),
        boxShadow: const [
          BoxShadow(
            color: Color(0x0A0F172A),
            blurRadius: 20,
            offset: Offset(0, 10),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 12,
                height: 12,
                decoration: BoxDecoration(
                  color: accent,
                  borderRadius: BorderRadius.circular(999),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  title,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(subtitle, style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(height: 18),
          child,
        ],
      ),
    );
  }
}

class _SystemNotice extends StatelessWidget {
  const _SystemNotice({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: _ChatPalette.cardSubtle,
          borderRadius: BorderRadius.circular(999),
          border: Border.all(color: _ChatPalette.border),
        ),
        child: Text(
          message,
          style: Theme.of(context).textTheme.bodySmall,
          textAlign: TextAlign.center,
        ),
      ),
    );
  }
}

enum _BubbleTone { user, assistant, success, danger }

class _ChatBubble extends StatelessWidget {
  const _ChatBubble({
    required this.alignment,
    required this.tone,
    required this.header,
    required this.body,
    this.footer,
  });

  final Alignment alignment;
  final _BubbleTone tone;
  final String header;
  final String body;
  final String? footer;

  @override
  Widget build(BuildContext context) {
    final palette = switch (tone) {
      _BubbleTone.user => (
        background: _ChatPalette.userBubble,
        border: _ChatPalette.userBubbleBorder,
        text: _ChatPalette.textPrimary,
      ),
      _BubbleTone.assistant => (
        background: _ChatPalette.shellBackground,
        border: _ChatPalette.border,
        text: _ChatPalette.textPrimary,
      ),
      _BubbleTone.success => (
        background: _ChatPalette.successSoft,
        border: _ChatPalette.successSoftBorder,
        text: _ChatPalette.textPrimary,
      ),
      _BubbleTone.danger => (
        background: _ChatPalette.dangerSoftest,
        border: _ChatPalette.dangerSoft,
        text: _ChatPalette.textPrimary,
      ),
    };

    return Align(
      alignment: alignment,
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 640),
        child: Container(
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            color: palette.background,
            borderRadius: BorderRadius.circular(24),
            border: Border.all(color: palette.border),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                header,
                style: Theme.of(context).textTheme.labelLarge?.copyWith(
                  color: tone == _BubbleTone.user
                      ? _ChatPalette.primary
                      : _ChatPalette.textMuted,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                body,
                style: Theme.of(
                  context,
                ).textTheme.bodyLarge?.copyWith(color: palette.text),
              ),
              if (footer case final value?) ...[
                const SizedBox(height: 12),
                Text(value, style: Theme.of(context).textTheme.bodySmall),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _TaskThreadTile extends StatelessWidget {
  const _TaskThreadTile({
    required this.task,
    required this.selected,
    required this.onTap,
  });

  final TaskRecord task;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final accent = _taskStatusColor(task.status);
    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(18),
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeOutCubic,
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: selected
                ? accent.withValues(alpha: 0.06)
                : _ChatPalette.cardSubtle,
            borderRadius: BorderRadius.circular(18),
            border: Border.all(
              color: selected
                  ? accent.withValues(alpha: 0.22)
                  : _ChatPalette.border,
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(
                      color: accent,
                      borderRadius: BorderRadius.circular(999),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      task.status.label,
                      style: Theme.of(
                        context,
                      ).textTheme.labelLarge?.copyWith(color: accent),
                    ),
                  ),
                  Text(
                    task.deviceId,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                task.instruction,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const SizedBox(height: 10),
              Text(
                task.reason ??
                    (task.logs.isNotEmpty ? task.logs.last : '打开继续查看线程细节'),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _SidebarEmptyState extends StatelessWidget {
  const _SidebarEmptyState();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _ChatPalette.cardSubtle,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: _ChatPalette.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('还没有历史聊天', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          Text(
            '连接网关后，点击上方“新对话”，右侧就会进入新的 AI 会话线程。',
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
    );
  }
}

class _HintCard extends StatelessWidget {
  const _HintCard({
    required this.icon,
    required this.title,
    required this.body,
  });

  final IconData icon;
  final String title;
  final String body;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: _ChatPalette.shellBackground,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: _ChatPalette.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: _ChatPalette.primary),
          const SizedBox(height: 12),
          Text(title, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          Text(body, style: Theme.of(context).textTheme.bodySmall),
        ],
      ),
    );
  }
}

class _SectionCard extends StatelessWidget {
  const _SectionCard({
    required this.child,
    this.padding = const EdgeInsets.all(20),
  });

  final Widget child;
  final EdgeInsetsGeometry padding;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: _ChatPalette.shellBackground,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: _ChatPalette.border),
      ),
      child: Padding(padding: padding, child: child),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  const _SectionTitle({required this.title, required this.body});

  final String title;
  final String body;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 6),
        Text(body, style: Theme.of(context).textTheme.bodySmall),
      ],
    );
  }
}

class _LabeledField extends StatelessWidget {
  const _LabeledField({required this.label, required this.child});

  final String label;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: Theme.of(context).textTheme.labelLarge),
        const SizedBox(height: 8),
        child,
      ],
    );
  }
}

class _StatusBadge extends StatelessWidget {
  const _StatusBadge({required this.label, required this.color});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: color.withValues(alpha: 0.22)),
      ),
      child: Text(
        label,
        style: Theme.of(context).textTheme.labelLarge?.copyWith(color: color),
      ),
    );
  }
}

class _MetaChip extends StatelessWidget {
  const _MetaChip({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: _ChatPalette.cardSubtle,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: _ChatPalette.border),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: _ChatPalette.textMuted),
          const SizedBox(width: 8),
          Text(label, style: Theme.of(context).textTheme.bodySmall),
        ],
      ),
    );
  }
}

String _taskNarrative(TaskRecord task) {
  switch (task.status) {
    case TaskStatus.pendingDispatch:
      return '任务已经进入网关队列，等待客户端领取执行。';
    case TaskStatus.running:
      return 'AI 已经开始执行任务，新的过程日志会继续写入当前会话。';
    case TaskStatus.awaitingApproval:
      return 'AI 在执行过程中命中了敏感操作，已暂停并等待你的二次确认。';
    case TaskStatus.approved:
      return '这次敏感操作已经获批，客户端会从中断点继续执行。';
    case TaskStatus.rejected:
      return '这次敏感操作被拒绝，任务会保持停止状态，等待新的指令。';
    case TaskStatus.resuming:
      return '客户端正在从检查点恢复，继续关注后续输出。';
    case TaskStatus.completed:
      return '任务已经完成，所有结果都保留在当前会话中。';
    case TaskStatus.failed:
      return '任务执行失败，请结合最近日志和错误信息继续处理。';
    case TaskStatus.unknown:
      return '任务状态未知，建议刷新任务列表或检查网关事件流。';
  }
}

String _connectionStatusLabel(ConnectionStatus status) {
  return switch (status) {
    ConnectionStatus.connected => '已连接',
    ConnectionStatus.connecting => '连接中',
    ConnectionStatus.failed => '异常',
    ConnectionStatus.idle => '未连接',
  };
}

Color _connectionStatusColor(ConnectionStatus status) {
  return switch (status) {
    ConnectionStatus.connected => _ChatPalette.primary,
    ConnectionStatus.connecting => _ChatPalette.warning,
    ConnectionStatus.failed => _ChatPalette.danger,
    ConnectionStatus.idle => _ChatPalette.textMuted,
  };
}

Color _taskStatusColor(TaskStatus status) {
  return switch (status) {
    TaskStatus.pendingDispatch => _ChatPalette.textMuted,
    TaskStatus.running => _ChatPalette.primary,
    TaskStatus.awaitingApproval => _ChatPalette.warning,
    TaskStatus.approved => _ChatPalette.primary,
    TaskStatus.rejected => _ChatPalette.danger,
    TaskStatus.resuming => const Color(0xFF2563EB),
    TaskStatus.completed => _ChatPalette.primary,
    TaskStatus.failed => _ChatPalette.danger,
    TaskStatus.unknown => _ChatPalette.textMuted,
  };
}

class _ChatPalette {
  static const pageBackground = Color(0xFFF5F6F3);
  static const shellBackground = Color(0xFFFFFFFF);
  static const cardSubtle = Color(0xFFF7F7F8);
  static const border = Color(0xFFE5E7EB);
  static const primary = Color(0xFF10A37F);
  static const primarySoft = Color(0xFFE6F7F1);
  static const textPrimary = Color(0xFF111827);
  static const textMuted = Color(0xFF6B7280);
  static const userBubble = Color(0xFFF2FBF7);
  static const userBubbleBorder = Color(0xFFCDEEE2);
  static const warning = Color(0xFFB7791F);
  static const danger = Color(0xFFDC2626);
  static const dangerSoft = Color(0xFFFECACA);
  static const dangerSoftest = Color(0xFFFEF2F2);
  static const successSoft = Color(0xFFECFDF5);
  static const successSoftBorder = Color(0xFFA7F3D0);
}
