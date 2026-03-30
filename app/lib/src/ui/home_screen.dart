import 'dart:math' as math;

import 'package:app/src/models/task_record.dart';
import 'package:app/src/state/task_controller.dart';
import 'package:app/src/ui/app_theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter_highlight/flutter_highlight.dart';
import 'package:flutter_highlight/themes/atom-one-dark.dart';
import 'package:google_fonts/google_fonts.dart';

class OpenJarvisHome extends StatefulWidget {
  const OpenJarvisHome({super.key, required this.controller});

  final TaskController controller;

  @override
  State<OpenJarvisHome> createState() => _OpenJarvisHomeState();
}

class _OpenJarvisHomeState extends State<OpenJarvisHome> {
  final _scaffoldKey = GlobalKey<ScaffoldState>();
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

  void _syncSelectedDevice() {
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
  }

  Future<void> _connectGateway() async {
    await controller.connect(
      baseUrl: _baseUrlController.text.trim(),
      username: _usernameController.text.trim(),
      password: _passwordController.text,
    );
  }

  Future<void> _openSettingsSheet() async {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (sheetContext) {
        return _SettingsSheet(
          controller: controller,
          baseUrlController: _baseUrlController,
          usernameController: _usernameController,
          passwordController: _passwordController,
          onConnect: () async {
            await _connectGateway();
            if (!mounted || !sheetContext.mounted) {
              return;
            }
            if (controller.status == ConnectionStatus.connected) {
              Navigator.of(sheetContext).pop();
            }
          },
          onRefresh: controller.refresh,
        );
      },
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
    if (!mounted) {
      return;
    }
    setState(() {});
    FocusScope.of(context).unfocus();
  }

  void _selectTask(String taskId, {required bool closeDrawer}) {
    controller.selectTask(taskId);
    if (closeDrawer && Navigator.of(context).canPop()) {
      Navigator.of(context).pop();
    }
  }

  void _startNewChat({required bool closeDrawer}) {
    controller.clearSelection();
    if (closeDrawer && Navigator.of(context).canPop()) {
      Navigator.of(context).pop();
    }
  }

  void _prefillInstruction(String value) {
    _composerController.value = TextEditingValue(
      text: value,
      selection: TextSelection.collapsed(offset: value.length),
    );
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: controller,
      builder: (context, _) {
        _syncSelectedDevice();
        return LayoutBuilder(
          builder: (context, constraints) {
            final isWide = constraints.maxWidth >= 1120;
            final rail = _ThreadRail(
              controller: controller,
              selectedDeviceId: _selectedDeviceId,
              onDeviceChanged: (value) {
                setState(() {
                  _selectedDeviceId = value;
                });
              },
              onNewChat: () => _startNewChat(closeDrawer: !isWide),
              onSelectTask: (taskId) =>
                  _selectTask(taskId, closeDrawer: !isWide),
            );

            return Scaffold(
              key: _scaffoldKey,
              drawer: isWide
                  ? null
                  : Drawer(
                      key: const Key('threadDrawer'),
                      width: math.min(constraints.maxWidth * 0.88, 360),
                      child: SafeArea(
                        bottom: false,
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: rail,
                        ),
                      ),
                    ),
              appBar: _JarvisAppBar(
                isWide: isWide,
                controller: controller,
                selectedDeviceId: _selectedDeviceId,
                onOpenMenu: () => _scaffoldKey.currentState?.openDrawer(),
                onOpenSettings: _openSettingsSheet,
              ),
              body: _Backdrop(
                child: SafeArea(
                  top: false,
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      if (isWide)
                        Padding(
                          padding: const EdgeInsets.fromLTRB(20, 20, 0, 20),
                          child: SizedBox(
                            width: 320,
                            child: KeyedSubtree(
                              key: const Key('desktopThreadRail'),
                              child: rail,
                            ),
                          ),
                        ),
                      Expanded(
                        child: Padding(
                          padding: EdgeInsets.fromLTRB(
                            isWide ? 20 : 16,
                            20,
                            16,
                            16,
                          ),
                          child: Align(
                            alignment: Alignment.topCenter,
                            child: ConstrainedBox(
                              constraints: const BoxConstraints(maxWidth: 860),
                              child: Column(
                                children: [
                                  _WorkspaceSummary(
                                    controller: controller,
                                    selectedDeviceId: _selectedDeviceId,
                                    onFocusPending: () {
                                      if (controller.pendingTasks.isNotEmpty) {
                                        controller.selectTask(
                                          controller.pendingTasks.first.taskId,
                                        );
                                      }
                                    },
                                  ),
                                  const SizedBox(height: 16),
                                  Expanded(
                                    child: _ConversationViewport(
                                      controller: controller,
                                      composerController: _composerController,
                                      onPrefillInstruction: _prefillInstruction,
                                    ),
                                  ),
                                  const SizedBox(height: 16),
                                  _ComposerBar(
                                    controller: controller,
                                    selectedDeviceId: _selectedDeviceId,
                                    composerController: _composerController,
                                    onComposerChanged: () => setState(() {}),
                                    onSend: _sendInstruction,
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            );
          },
        );
      },
    );
  }
}

class _JarvisAppBar extends StatelessWidget implements PreferredSizeWidget {
  const _JarvisAppBar({
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
            selectedDeviceId == null ? 'AI 任务控制台' : '当前设备 $selectedDeviceId',
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
                '${_connectionStatusLabel(controller.status)} · $onlineCount 在线',
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

class _Backdrop extends StatelessWidget {
  const _Backdrop({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    final tokens = JarvisThemeTokens.of(context);
    return DecoratedBox(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [tokens.pageTop, tokens.pageBottom],
        ),
      ),
      child: Stack(
        children: [
          Positioned(
            top: -120,
            right: -80,
            child: IgnorePointer(
              child: _GlowOrb(
                size: 320,
                colors: [
                  tokens.accent.withValues(alpha: 0.18),
                  Colors.transparent,
                ],
              ),
            ),
          ),
          Positioned(
            left: -80,
            bottom: -140,
            child: IgnorePointer(
              child: _GlowOrb(
                size: 300,
                colors: [
                  tokens.accentSecondary.withValues(alpha: 0.16),
                  Colors.transparent,
                ],
              ),
            ),
          ),
          child,
        ],
      ),
    );
  }
}

class _GlowOrb extends StatelessWidget {
  const _GlowOrb({required this.size, required this.colors});

  final double size;
  final List<Color> colors;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: RadialGradient(colors: colors),
      ),
    );
  }
}

class _ThreadRail extends StatelessWidget {
  const _ThreadRail({
    required this.controller,
    required this.selectedDeviceId,
    required this.onDeviceChanged,
    required this.onNewChat,
    required this.onSelectTask,
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

    return _GlassCard(
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
              _StatusPill(
                label: _connectionStatusLabel(controller.status),
                color: _connectionStatusColor(controller.status, tokens),
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
          _GlassCard(
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
                    _MetricChip(
                      icon: Icons.devices_rounded,
                      label: '$onlineDevices 台在线',
                    ),
                    _MetricChip(
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
                    _TaskSection(
                      title: '待处理线程',
                      body: '先处理敏感操作审批，再继续任务。',
                      tasks: pendingTasks,
                      selectedTaskId: controller.selectedTask?.taskId,
                      onSelectTask: onSelectTask,
                    ),
                  if (pendingTasks.isNotEmpty && recentTasks.isNotEmpty)
                    const SizedBox(height: 14),
                  if (recentTasks.isNotEmpty)
                    _TaskSection(
                      title: '最近会话',
                      body: '已经跑过的任务和主动发起的聊天。',
                      tasks: recentTasks,
                      selectedTaskId: controller.selectedTask?.taskId,
                      onSelectTask: onSelectTask,
                    ),
                  if (controller.tasks.isEmpty) const _EmptyThreadState(),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _TaskSection extends StatelessWidget {
  const _TaskSection({
    required this.title,
    required this.body,
    required this.tasks,
    required this.selectedTaskId,
    required this.onSelectTask,
  });

  final String title;
  final String body;
  final List<TaskRecord> tasks;
  final String? selectedTaskId;
  final ValueChanged<String> onSelectTask;

  @override
  Widget build(BuildContext context) {
    return _GlassCard(
      padding: const EdgeInsets.all(16),
      backgroundColor: JarvisThemeTokens.of(context).surface,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 6),
          Text(body, style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(height: 14),
          ...tasks.map(
            (task) => Padding(
              padding: EdgeInsets.only(bottom: task == tasks.last ? 0 : 10),
              child: _ThreadTile(
                task: task,
                selected: selectedTaskId == task.taskId,
                onTap: () => onSelectTask(task.taskId),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ThreadTile extends StatelessWidget {
  const _ThreadTile({
    required this.task,
    required this.selected,
    required this.onTap,
  });

  final TaskRecord task;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final tokens = JarvisThemeTokens.of(context);
    final accent = _taskStatusColor(task.status, tokens);
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(18),
        child: AnimatedContainer(
          duration: _motionDuration(context),
          curve: Curves.easeOutCubic,
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: selected
                ? accent.withValues(alpha: 0.14)
                : tokens.shellRaised,
            borderRadius: BorderRadius.circular(18),
            border: Border.all(
              color: selected ? accent.withValues(alpha: 0.5) : tokens.border,
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
              const SizedBox(height: 10),
              Text(
                task.instruction,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const SizedBox(height: 8),
              Text(
                task.reason ??
                    task.result ??
                    (task.logs.isNotEmpty ? task.logs.last : '打开查看详情'),
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

class _EmptyThreadState extends StatelessWidget {
  const _EmptyThreadState();

  @override
  Widget build(BuildContext context) {
    return _GlassCard(
      padding: const EdgeInsets.all(16),
      backgroundColor: JarvisThemeTokens.of(context).surface,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('还没有历史线程', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          Text(
            '连接网关后发出第一条任务，这里会自动形成可恢复的聊天线程。',
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
    );
  }
}

class _WorkspaceSummary extends StatelessWidget {
  const _WorkspaceSummary({
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

    return _GlassCard(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            selectedTask == null ? '移动端 AI 工作台' : '当前线程概览',
            style: Theme.of(context).textTheme.headlineSmall,
          ),
          const SizedBox(height: 8),
          Text(
            selectedTask == null
                ? '对话、审批、恢复和实时日志都收敛在同一条消息流里。'
                : '当前线程状态：${selectedTask.status.label}。后续日志、审批和恢复都会继续写回这里。',
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              _MetricChip(
                icon: Icons.route_rounded,
                label: selectedDeviceId == null
                    ? '未选择设备'
                    : '当前设备 $selectedDeviceId',
              ),
              _MetricChip(
                icon: Icons.devices_rounded,
                label: '$onlineDevices 台在线',
              ),
              _MetricChip(
                icon: Icons.pending_actions_rounded,
                label: '${controller.pendingTasks.length} 个待审批',
              ),
              if (selectedTask?.checkpointId case final checkpointId?)
                _MetricChip(
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

class _ConversationViewport extends StatelessWidget {
  const _ConversationViewport({
    required this.controller,
    required this.composerController,
    required this.onPrefillInstruction,
  });

  final TaskController controller;
  final TextEditingController composerController;
  final ValueChanged<String> onPrefillInstruction;

  @override
  Widget build(BuildContext context) {
    final child = controller.selectedTask == null
        ? _WelcomeView(
            controller: controller,
            onQuickPrompt: onPrefillInstruction,
          )
        : _TaskTimeline(controller: controller, task: controller.selectedTask!);

    return _GlassCard(
      padding: EdgeInsets.zero,
      clipBehavior: Clip.antiAlias,
      child: AnimatedSwitcher(
        duration: _motionDuration(context),
        switchInCurve: Curves.easeOutCubic,
        switchOutCurve: Curves.easeOutCubic,
        child: KeyedSubtree(
          key: ValueKey<String?>(controller.selectedTask?.taskId),
          child: child,
        ),
      ),
    );
  }
}

class _WelcomeView extends StatelessWidget {
  const _WelcomeView({required this.controller, required this.onQuickPrompt});

  final TaskController controller;
  final ValueChanged<String> onQuickPrompt;

  @override
  Widget build(BuildContext context) {
    final tokens = JarvisThemeTokens.of(context);
    final quickPrompts = <(String, String)>[
      ('巡检容器', '检查 docker 容器状态并汇总异常'),
      ('恢复挂起任务', '检查当前所有挂起任务并给出恢复建议'),
      ('查看网关日志', '查看网关最近 100 行日志并标出异常'),
    ];

    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [tokens.shellRaised, tokens.surface],
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 54,
                height: 54,
                decoration: BoxDecoration(
                  color: tokens.accentSoft,
                  borderRadius: BorderRadius.circular(18),
                ),
                child: Icon(
                  Icons.chat_bubble_outline_rounded,
                  color: tokens.accent,
                ),
              ),
              const SizedBox(height: 20),
              Text(
                '给 Jarvis 一个目标',
                style: Theme.of(context).textTheme.headlineSmall,
              ),
              const SizedBox(height: 10),
              Text(
                controller.status == ConnectionStatus.connected
                    ? '直接输入任务，系统会把审批、恢复和执行日志全部回收到这条对话。'
                    : '先完成网关连接，之后这里会变成统一的聊天工作区。',
                style: Theme.of(context).textTheme.bodyLarge,
              ),
              const SizedBox(height: 20),
              Wrap(
                spacing: 10,
                runSpacing: 10,
                children: quickPrompts
                    .map(
                      (prompt) => ActionChip(
                        onPressed: () => onQuickPrompt(prompt.$2),
                        avatar: const Icon(Icons.north_east_rounded, size: 16),
                        label: Text(prompt.$1),
                      ),
                    )
                    .toList(growable: false),
              ),
            ],
          ),
        ),
        const SizedBox(height: 18),
        _HintGrid(
          cards: const [
            _HintData(
              icon: Icons.send_rounded,
              title: '任务下发',
              body: '像聊天一样下发任务，但底层仍然走网关与客户端协议。',
            ),
            _HintData(
              icon: Icons.shield_outlined,
              title: '会话内审批',
              body: '敏感操作以审批卡形式插入消息流，不再跳到独立页面。',
            ),
            _HintData(
              icon: Icons.terminal_rounded,
              title: '实时日志',
              body: 'stdout、恢复状态和执行结果在同一线程内连续展示。',
            ),
          ],
        ),
      ],
    );
  }
}

class _TaskTimeline extends StatelessWidget {
  const _TaskTimeline({required this.controller, required this.task});

  final TaskController controller;
  final TaskRecord task;

  @override
  Widget build(BuildContext context) {
    final timeline = <Widget>[_StatusHero(task: task)];

    if (task.command != null ||
        task.reason != null ||
        task.isAwaitingApproval) {
      timeline.add(const SizedBox(height: 16));
      timeline.add(_ApprovalCard(controller: controller, task: task));
    }

    if (task.logs.length > 2) {
      timeline.add(const SizedBox(height: 16));
      timeline.add(_LiveLogCard(logs: task.logs));
    }

    if (task.result case final result?
        when result.length > 24 || result.contains('\n')) {
      timeline.add(const SizedBox(height: 16));
      timeline.add(
        _InlineNoticeCard(
          icon: Icons.check_circle_outline_rounded,
          title: '执行结果',
          body: result,
          accent: JarvisThemeTokens.of(context).success,
        ),
      );
    }

    if (task.error case final error?) {
      timeline.add(const SizedBox(height: 16));
      timeline.add(
        _InlineNoticeCard(
          icon: Icons.error_outline_rounded,
          title: '执行错误',
          body: error,
          accent: JarvisThemeTokens.of(context).danger,
        ),
      );
    }

    timeline.addAll([
      const SizedBox(height: 16),
      _MessageBubble(
        alignment: Alignment.centerRight,
        tone: _BubbleTone.user,
        role: '你',
        title: '任务已发送',
        body: task.instruction,
        footer: '目标设备 ${task.deviceId}',
      ),
      const SizedBox(height: 16),
      _MessageBubble(
        alignment: Alignment.centerLeft,
        tone: _BubbleTone.assistant,
        role: 'Jarvis',
        title: '任务分析',
        body: _taskNarrative(task),
      ),
    ]);

    return Scrollbar(
      child: ListView(padding: const EdgeInsets.all(24), children: timeline),
    );
  }
}

class _StatusHero extends StatelessWidget {
  const _StatusHero({required this.task});

  final TaskRecord task;

  @override
  Widget build(BuildContext context) {
    final tokens = JarvisThemeTokens.of(context);
    final accent = _taskStatusColor(task.status, tokens);
    return _GlassCard(
      padding: const EdgeInsets.all(20),
      backgroundColor: tokens.surface,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: accent.withValues(alpha: 0.16),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Icon(_taskIcon(task.status), color: accent),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _taskHeadline(task.status),
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 6),
                Text(
                  '任务 ${task.taskId} · ${task.status.label}',
                  style: Theme.of(
                    context,
                  ).textTheme.bodySmall?.copyWith(color: accent),
                ),
                if (task.result case final result?) ...[
                  const SizedBox(height: 6),
                  Text(
                    result,
                    style: Theme.of(
                      context,
                    ).textTheme.titleMedium?.copyWith(color: accent),
                  ),
                ],
                const SizedBox(height: 8),
                Text(
                  '所有状态流转都会在这条线程里持续展开。',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
                if (task.logs.isNotEmpty) ...[
                  const SizedBox(height: 14),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: tokens.terminal,
                      borderRadius: BorderRadius.circular(18),
                      border: Border.all(color: tokens.terminalBorder),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '实时日志',
                          style: Theme.of(context).textTheme.labelLarge
                              ?.copyWith(color: const Color(0xFFF8FAFC)),
                        ),
                        const SizedBox(height: 8),
                        for (final line in task.logs.take(2))
                          Padding(
                            padding: EdgeInsets.only(
                              bottom: line == task.logs.take(2).last ? 0 : 6,
                            ),
                            child: Text(
                              line,
                              style: GoogleFonts.spaceMono(
                                fontSize: 12,
                                height: 1.5,
                                color: const Color(0xFFF8FAFC),
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                ],
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
    final tokens = JarvisThemeTokens.of(context);
    return _GlassCard(
      padding: const EdgeInsets.all(20),
      backgroundColor: tokens.warningSoft,
      borderColor: tokens.warning.withValues(alpha: 0.28),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: tokens.warning.withValues(alpha: 0.16),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Icon(Icons.lock_outline_rounded, color: tokens.warning),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '需要审批后继续',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      task.reason ?? '敏感操作已被挂起，等待你的确认。',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
            ],
          ),
          if (task.command case final command?) ...[
            const SizedBox(height: 16),
            SelectableText(
              command,
              style: GoogleFonts.spaceMono(
                fontSize: 13,
                height: 1.5,
                color: tokens.textPrimary,
              ),
            ),
            const SizedBox(height: 12),
            Container(
              decoration: BoxDecoration(
                color: tokens.terminal,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: tokens.terminalBorder),
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(20),
                child: HighlightView(
                  command,
                  language: 'bash',
                  theme: atomOneDarkTheme,
                  padding: const EdgeInsets.all(18),
                  textStyle: GoogleFonts.spaceMono(fontSize: 13, height: 1.5),
                ),
              ),
            ),
          ],
          if (task.checkpointId case final checkpointId?) ...[
            const SizedBox(height: 12),
            Text(
              '恢复检查点 $checkpointId',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
          if (task.isAwaitingApproval) ...[
            const SizedBox(height: 18),
            Wrap(
              spacing: 12,
              runSpacing: 12,
              children: [
                FilledButton(
                  onPressed: () => controller.submitDecision(true),
                  child: const Text('批准继续'),
                ),
                OutlinedButton(
                  onPressed: () => controller.submitDecision(false),
                  child: const Text('拒绝执行'),
                ),
              ],
            ),
          ] else ...[
            const SizedBox(height: 18),
            _StatusPill(
              label: task.status.label,
              color: _taskStatusColor(task.status, tokens),
            ),
          ],
        ],
      ),
    );
  }
}

class _LiveLogCard extends StatelessWidget {
  const _LiveLogCard({required this.logs});

  final List<String> logs;

  @override
  Widget build(BuildContext context) {
    final tokens = JarvisThemeTokens.of(context);
    return _GlassCard(
      padding: const EdgeInsets.all(20),
      backgroundColor: tokens.shellRaised,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('日志流', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 6),
          Text(
            '客户端 stdout 与恢复信息会不断追加到这里。',
            style: Theme.of(context).textTheme.bodySmall,
          ),
          const SizedBox(height: 16),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: tokens.terminal,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: tokens.terminalBorder),
            ),
            child: SelectionArea(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  for (var index = 0; index < logs.length; index++)
                    Padding(
                      padding: EdgeInsets.only(
                        bottom: index == logs.length - 1 ? 0 : 8,
                      ),
                      child: Text(
                        logs[index],
                        style: GoogleFonts.spaceMono(
                          fontSize: 13,
                          height: 1.5,
                          color: const Color(0xFFF8FAFC),
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _InlineNoticeCard extends StatelessWidget {
  const _InlineNoticeCard({
    required this.icon,
    required this.title,
    required this.body,
    required this.accent,
  });

  final IconData icon;
  final String title;
  final String body;
  final Color accent;

  @override
  Widget build(BuildContext context) {
    return _GlassCard(
      padding: const EdgeInsets.all(18),
      backgroundColor: JarvisThemeTokens.of(context).surface,
      borderColor: accent.withValues(alpha: 0.24),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: accent.withValues(alpha: 0.16),
              borderRadius: BorderRadius.circular(14),
            ),
            child: Icon(icon, color: accent),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 6),
                Text(body, style: Theme.of(context).textTheme.bodyMedium),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

enum _BubbleTone { user, assistant }

class _MessageBubble extends StatelessWidget {
  const _MessageBubble({
    required this.alignment,
    required this.tone,
    required this.role,
    required this.title,
    required this.body,
    this.footer,
  });

  final Alignment alignment;
  final _BubbleTone tone;
  final String role;
  final String title;
  final String body;
  final String? footer;

  @override
  Widget build(BuildContext context) {
    final tokens = JarvisThemeTokens.of(context);
    final background = switch (tone) {
      _BubbleTone.user => tokens.userBubble,
      _BubbleTone.assistant => tokens.assistantBubble,
    };
    final border = switch (tone) {
      _BubbleTone.user => tokens.accent.withValues(alpha: 0.22),
      _BubbleTone.assistant => tokens.border,
    };
    final labelColor = switch (tone) {
      _BubbleTone.user => tokens.accent,
      _BubbleTone.assistant => tokens.accentSecondary,
    };

    return Align(
      alignment: alignment,
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 640),
        child: _GlassCard(
          padding: const EdgeInsets.all(18),
          backgroundColor: background,
          borderColor: border,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                role,
                style: Theme.of(
                  context,
                ).textTheme.labelLarge?.copyWith(color: labelColor),
              ),
              const SizedBox(height: 8),
              Text(title, style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              Text(body, style: Theme.of(context).textTheme.bodyLarge),
              if (footer case final footerText?) ...[
                const SizedBox(height: 10),
                Text(footerText, style: Theme.of(context).textTheme.bodySmall),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _ComposerBar extends StatelessWidget {
  const _ComposerBar({
    required this.controller,
    required this.selectedDeviceId,
    required this.composerController,
    required this.onComposerChanged,
    required this.onSend,
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

    return _GlassCard(
      padding: const EdgeInsets.all(18),
      backgroundColor: tokens.shell,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
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
                  maxLines: 5,
                  decoration: InputDecoration(
                    hintText: controller.status == ConnectionStatus.connected
                        ? '输入一个任务，例如：检查 api-service 并在必要时重启'
                        : '先完成网关连接，再开始下发任务',
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

class _SettingsSheet extends StatelessWidget {
  const _SettingsSheet({
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
          child: _GlassCard(
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
                              style: Theme.of(context).textTheme.headlineSmall,
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
                  const SizedBox(height: 14),
                  _LabeledField(
                    label: '用户名',
                    child: TextField(
                      key: const Key('settingsUsernameField'),
                      controller: usernameController,
                      decoration: const InputDecoration(hintText: 'operator'),
                    ),
                  ),
                  const SizedBox(height: 14),
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
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      _MetricChip(
                        icon: Icons.wifi_tethering_rounded,
                        label: _connectionStatusLabel(controller.status),
                      ),
                      _MetricChip(
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
                      Expanded(
                        child: OutlinedButton(
                          onPressed: controller.token == null
                              ? null
                              : onRefresh,
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

class _HintGrid extends StatelessWidget {
  const _HintGrid({required this.cards});

  final List<_HintData> cards;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final wide = constraints.maxWidth >= 720;
        final itemWidth = wide
            ? (constraints.maxWidth - 20) / 2
            : constraints.maxWidth;
        return Wrap(
          spacing: 12,
          runSpacing: 12,
          children: cards
              .map(
                (card) => SizedBox(
                  width: itemWidth,
                  child: _GlassCard(
                    padding: const EdgeInsets.all(18),
                    backgroundColor: JarvisThemeTokens.of(context).surface,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(card.icon),
                        const SizedBox(height: 12),
                        Text(
                          card.title,
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        const SizedBox(height: 8),
                        Text(
                          card.body,
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                    ),
                  ),
                ),
              )
              .toList(growable: false),
        );
      },
    );
  }
}

class _HintData {
  const _HintData({
    required this.icon,
    required this.title,
    required this.body,
  });

  final IconData icon;
  final String title;
  final String body;
}

class _GlassCard extends StatelessWidget {
  const _GlassCard({
    required this.child,
    this.padding = const EdgeInsets.all(20),
    this.backgroundColor,
    this.borderColor,
    this.clipBehavior = Clip.none,
  });

  final Widget child;
  final EdgeInsetsGeometry padding;
  final Color? backgroundColor;
  final Color? borderColor;
  final Clip clipBehavior;

  @override
  Widget build(BuildContext context) {
    final tokens = JarvisThemeTokens.of(context);
    return DecoratedBox(
      decoration: BoxDecoration(
        color: backgroundColor ?? tokens.shell.withValues(alpha: 0.9),
        borderRadius: BorderRadius.circular(28),
        border: Border.all(color: borderColor ?? tokens.border),
        boxShadow: [
          BoxShadow(
            color: tokens.shadow,
            blurRadius: 28,
            offset: const Offset(0, 18),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(28),
        clipBehavior: clipBehavior,
        child: Padding(padding: padding, child: child),
      ),
    );
  }
}

class _StatusPill extends StatelessWidget {
  const _StatusPill({required this.label, required this.color});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.16),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: color.withValues(alpha: 0.28)),
      ),
      child: Text(
        label,
        style: Theme.of(context).textTheme.labelLarge?.copyWith(color: color),
      ),
    );
  }
}

class _MetricChip extends StatelessWidget {
  const _MetricChip({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    final tokens = JarvisThemeTokens.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: tokens.shellRaised,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: tokens.border),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: tokens.textMuted),
          const SizedBox(width: 8),
          Text(label, style: Theme.of(context).textTheme.bodySmall),
        ],
      ),
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

Duration _motionDuration(BuildContext context) {
  final disableAnimations =
      MediaQuery.maybeOf(context)?.disableAnimations ?? false;
  return disableAnimations ? Duration.zero : const Duration(milliseconds: 220);
}

String _connectionStatusLabel(ConnectionStatus status) {
  return switch (status) {
    ConnectionStatus.connected => '已连接',
    ConnectionStatus.connecting => '连接中',
    ConnectionStatus.failed => '异常',
    ConnectionStatus.idle => '未连接',
  };
}

Color _connectionStatusColor(
  ConnectionStatus status,
  JarvisThemeTokens tokens,
) {
  return switch (status) {
    ConnectionStatus.connected => tokens.success,
    ConnectionStatus.connecting => tokens.warning,
    ConnectionStatus.failed => tokens.danger,
    ConnectionStatus.idle => tokens.textMuted,
  };
}

String _taskHeadline(TaskStatus status) {
  return switch (status) {
    TaskStatus.pendingDispatch => '任务已进入派发队列',
    TaskStatus.running => '任务正在执行',
    TaskStatus.awaitingApproval => '等待你的批准',
    TaskStatus.approved => '审批已通过',
    TaskStatus.rejected => '审批已拒绝',
    TaskStatus.resuming => '任务正在恢复',
    TaskStatus.completed => '执行已完成',
    TaskStatus.failed => '任务执行失败',
    TaskStatus.unknown => '任务状态未知',
  };
}

Color _taskStatusColor(TaskStatus status, JarvisThemeTokens tokens) {
  return switch (status) {
    TaskStatus.pendingDispatch => tokens.textMuted,
    TaskStatus.running => tokens.accentSecondary,
    TaskStatus.awaitingApproval => tokens.warning,
    TaskStatus.approved => tokens.success,
    TaskStatus.rejected => tokens.danger,
    TaskStatus.resuming => tokens.accentSecondary,
    TaskStatus.completed => tokens.success,
    TaskStatus.failed => tokens.danger,
    TaskStatus.unknown => tokens.textMuted,
  };
}

IconData _taskIcon(TaskStatus status) {
  return switch (status) {
    TaskStatus.pendingDispatch => Icons.schedule_send_rounded,
    TaskStatus.running => Icons.motion_photos_on_rounded,
    TaskStatus.awaitingApproval => Icons.shield_outlined,
    TaskStatus.approved => Icons.check_circle_outline_rounded,
    TaskStatus.rejected => Icons.cancel_outlined,
    TaskStatus.resuming => Icons.restore_rounded,
    TaskStatus.completed => Icons.done_all_rounded,
    TaskStatus.failed => Icons.error_outline_rounded,
    TaskStatus.unknown => Icons.help_outline_rounded,
  };
}

String _taskNarrative(TaskRecord task) {
  return switch (task.status) {
    TaskStatus.pendingDispatch => '网关已经接收任务，正在等待客户端拉取并开始执行。',
    TaskStatus.running => '执行链路已经启动，新的日志会实时回到当前会话。',
    TaskStatus.awaitingApproval => 'AI 命中了敏感操作，已经在执行前自动挂起。',
    TaskStatus.approved => '敏感操作已经放行，客户端会从恢复点继续执行。',
    TaskStatus.rejected => '这次敏感操作被拒绝，线程会保留上下文等待新的指令。',
    TaskStatus.resuming => '客户端正在从检查点恢复，后续过程会继续写回当前线程。',
    TaskStatus.completed => '任务已经完成，最终结果和日志都保留在这里。',
    TaskStatus.failed => '任务执行出现错误，建议结合日志继续排查。',
    TaskStatus.unknown => '网关返回了未知状态，建议同步任务或检查事件流。',
  };
}
