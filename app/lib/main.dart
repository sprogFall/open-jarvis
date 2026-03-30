import 'dart:math' as math;

import 'package:app/src/models/task_record.dart';
import 'package:app/src/services/gateway_api.dart';
import 'package:app/src/services/gateway_socket.dart';
import 'package:app/src/state/task_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_highlight/flutter_highlight.dart';
import 'package:flutter_highlight/themes/atom-one-dark.dart';
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
    final bodyTextTheme = GoogleFonts.ibmPlexSansTextTheme();
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'OpenJarvis',
      theme: ThemeData(
        useMaterial3: true,
        scaffoldBackgroundColor: _AppPalette.canvas,
        colorScheme: const ColorScheme.dark(
          primary: _AppPalette.accent,
          secondary: _AppPalette.secondary,
          surface: _AppPalette.surface,
          error: _AppPalette.danger,
        ),
        textTheme: bodyTextTheme.copyWith(
          displayMedium: GoogleFonts.spaceGrotesk(
            fontSize: 38,
            fontWeight: FontWeight.w700,
            height: 1.04,
            color: _AppPalette.textPrimary,
          ),
          displaySmall: GoogleFonts.spaceGrotesk(
            fontSize: 30,
            fontWeight: FontWeight.w700,
            height: 1.08,
            color: _AppPalette.textPrimary,
          ),
          headlineSmall: GoogleFonts.spaceGrotesk(
            fontSize: 24,
            fontWeight: FontWeight.w700,
            color: _AppPalette.textPrimary,
          ),
          titleLarge: bodyTextTheme.titleLarge?.copyWith(
            color: _AppPalette.textPrimary,
            fontWeight: FontWeight.w600,
          ),
          titleMedium: bodyTextTheme.titleMedium?.copyWith(
            color: _AppPalette.textPrimary,
            fontWeight: FontWeight.w600,
          ),
          bodyLarge: bodyTextTheme.bodyLarge?.copyWith(
            color: _AppPalette.textPrimary,
            height: 1.55,
          ),
          bodyMedium: bodyTextTheme.bodyMedium?.copyWith(
            color: _AppPalette.textPrimary,
            height: 1.5,
          ),
          bodySmall: bodyTextTheme.bodySmall?.copyWith(
            color: _AppPalette.textMuted,
            height: 1.45,
          ),
          labelLarge: bodyTextTheme.labelLarge?.copyWith(
            color: _AppPalette.textMuted,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.2,
          ),
        ),
        dividerColor: _AppPalette.divider,
        inputDecorationTheme: InputDecorationTheme(
          hintStyle: bodyTextTheme.bodyMedium?.copyWith(
            color: _AppPalette.textMuted,
          ),
          filled: true,
          fillColor: _AppPalette.surfaceRaised,
          contentPadding: const EdgeInsets.symmetric(
            horizontal: 18,
            vertical: 18,
          ),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(18),
            borderSide: const BorderSide(color: _AppPalette.divider),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(18),
            borderSide: const BorderSide(color: _AppPalette.divider),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(18),
            borderSide: const BorderSide(color: _AppPalette.accent),
          ),
        ),
        filledButtonTheme: FilledButtonThemeData(
          style: FilledButton.styleFrom(
            backgroundColor: _AppPalette.accent,
            foregroundColor: _AppPalette.canvas,
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 18),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(18),
            ),
          ),
        ),
        outlinedButtonTheme: OutlinedButtonThemeData(
          style: OutlinedButton.styleFrom(
            foregroundColor: _AppPalette.textPrimary,
            side: const BorderSide(color: _AppPalette.divider),
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 18),
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
  final _instructionController = TextEditingController();
  String? _selectedDeviceId;

  TaskController get controller => widget.controller;

  @override
  void dispose() {
    _baseUrlController.dispose();
    _usernameController.dispose();
    _passwordController.dispose();
    _instructionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: controller,
      builder: (context, _) {
        _selectedDeviceId ??= controller.devices.isNotEmpty
            ? controller.devices.first.deviceId
            : null;
        final onlineDeviceCount = controller.devices
            .where((device) => device.connected)
            .length;
        return Scaffold(
          body: DecoratedBox(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  _AppPalette.canvas,
                  _AppPalette.canvasMid,
                  _AppPalette.canvas,
                ],
              ),
            ),
            child: Stack(
              children: [
                const Positioned(
                  top: -140,
                  right: -90,
                  child: _AmbientGlow(
                    size: 360,
                    color: _AppPalette.secondaryGlow,
                  ),
                ),
                const Positioned(
                  left: -70,
                  bottom: -120,
                  child: _AmbientGlow(size: 300, color: _AppPalette.accentGlow),
                ),
                SafeArea(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: LayoutBuilder(
                      builder: (context, constraints) {
                        final isWide = constraints.maxWidth >= 1120;
                        final sidebar = _Reveal(
                          beginOffset: const Offset(-20, 0),
                          child: _Sidebar(
                            controller: controller,
                            baseUrlController: _baseUrlController,
                            usernameController: _usernameController,
                            passwordController: _passwordController,
                            instructionController: _instructionController,
                            selectedDeviceId: _selectedDeviceId,
                            onlineDeviceCount: onlineDeviceCount,
                            onDeviceChanged: (value) {
                              setState(() {
                                _selectedDeviceId = value;
                              });
                            },
                          ),
                        );
                        final workspace = _Reveal(
                          beginOffset: const Offset(0, 22),
                          child: _Workspace(
                            controller: controller,
                            onlineDeviceCount: onlineDeviceCount,
                          ),
                        );

                        if (isWide) {
                          return Row(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              SizedBox(width: 340, child: sidebar),
                              const SizedBox(width: 24),
                              Expanded(child: workspace),
                            ],
                          );
                        }

                        return Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            SizedBox(
                              height: math.min(
                                constraints.maxHeight * 0.48,
                                520.0,
                              ),
                              child: sidebar,
                            ),
                            const SizedBox(height: 20),
                            Expanded(child: workspace),
                          ],
                        );
                      },
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

class _Sidebar extends StatelessWidget {
  const _Sidebar({
    required this.controller,
    required this.baseUrlController,
    required this.usernameController,
    required this.passwordController,
    required this.instructionController,
    required this.selectedDeviceId,
    required this.onlineDeviceCount,
    required this.onDeviceChanged,
  });

  final TaskController controller;
  final TextEditingController baseUrlController;
  final TextEditingController usernameController;
  final TextEditingController passwordController;
  final TextEditingController instructionController;
  final String? selectedDeviceId;
  final int onlineDeviceCount;
  final ValueChanged<String?> onDeviceChanged;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final statusColor = _connectionStatusColor(controller.status);
    return _SurfacePanel(
      child: Scrollbar(
        child: ListView(
          padding: const EdgeInsets.all(28),
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('OpenJarvis', style: theme.textTheme.headlineSmall),
                      const SizedBox(height: 8),
                      Text(
                        '控制中枢',
                        style: theme.textTheme.titleMedium?.copyWith(
                          color: _AppPalette.textSoft,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        controller.pendingTasks.isEmpty
                            ? '连接网关、派发任务并持续观察实时日志。'
                            : '检测到挂起任务，优先完成审批并恢复客户端执行。',
                        style: theme.textTheme.bodyMedium?.copyWith(
                          color: _AppPalette.textMuted,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 12),
                _StatusPill(
                  label: switch (controller.status) {
                    ConnectionStatus.connected => '在线',
                    ConnectionStatus.connecting => '连接中',
                    ConnectionStatus.failed => '异常',
                    ConnectionStatus.idle => '未连接',
                  },
                  color: statusColor,
                ),
              ],
            ),
            const SizedBox(height: 24),
            _MetricBand(
              items: [
                _MetricBandItem(
                  label: '待处理审批',
                  value: _formatCount(controller.pendingTasks.length),
                  accent: _AppPalette.warning,
                ),
                _MetricBandItem(
                  label: '在线设备',
                  value: _formatCount(onlineDeviceCount),
                  accent: _AppPalette.secondary,
                ),
                _MetricBandItem(
                  label: '任务总数',
                  value: _formatCount(controller.tasks.length),
                  accent: _AppPalette.accent,
                ),
              ],
            ),
            if (controller.errorMessage case final error?) ...[
              const SizedBox(height: 16),
              Text(
                error,
                style: theme.textTheme.bodySmall?.copyWith(
                  color: _AppPalette.danger,
                ),
              ),
            ],
            const SizedBox(height: 28),
            const _SectionHeader(title: '网关接入', body: '登录后同步待审批任务、设备状态与实时日志。'),
            const SizedBox(height: 16),
            _LabeledField(
              label: 'Gateway URL',
              child: TextField(
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
                controller: usernameController,
                decoration: const InputDecoration(hintText: 'operator'),
              ),
            ),
            const SizedBox(height: 12),
            _LabeledField(
              label: '密码',
              child: TextField(
                controller: passwordController,
                obscureText: true,
                decoration: const InputDecoration(hintText: 'passw0rd'),
              ),
            ),
            const SizedBox(height: 14),
            FilledButton.icon(
              onPressed: () {
                controller.connect(
                  baseUrl: baseUrlController.text.trim(),
                  username: usernameController.text.trim(),
                  password: passwordController.text,
                );
              },
              icon: const Icon(Icons.hub_outlined),
              label: const Text('连接网关'),
            ),
            const SizedBox(height: 8),
            TextButton(
              onPressed: controller.token == null ? null : controller.refresh,
              child: const Text('刷新待处理任务'),
            ),
            const SizedBox(height: 24),
            const Divider(color: _AppPalette.divider),
            const SizedBox(height: 24),
            const _SectionHeader(
              title: '任务派发',
              body: '将指令交给在线客户端执行；命中敏感操作时会自动挂起审批。',
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              initialValue: selectedDeviceId,
              isExpanded: true,
              dropdownColor: _AppPalette.surfaceRaised,
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
            TextField(
              controller: instructionController,
              maxLines: 5,
              decoration: const InputDecoration(
                hintText: '例如：查看系统负载，然后重启容器 api-service',
              ),
            ),
            const SizedBox(height: 14),
            OutlinedButton.icon(
              onPressed: selectedDeviceId == null
                  ? null
                  : () {
                      controller.createTask(
                        deviceId: selectedDeviceId!,
                        instruction: instructionController.text.trim(),
                      );
                    },
              icon: const Icon(Icons.playlist_add_outlined),
              label: const Text('派发任务'),
            ),
            const SizedBox(height: 24),
            const Divider(color: _AppPalette.divider),
            const SizedBox(height: 24),
            const _SectionHeader(
              title: '任务队列',
              body: '选择任务后可查看审批说明、恢复检查点与执行日志。',
            ),
            const SizedBox(height: 16),
            if (controller.tasks.isEmpty)
              const _EmptyQueueHint()
            else
              ...controller.tasks.map(
                (task) => Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: _TaskQueueTile(
                    task: task,
                    selected: controller.selectedTask?.taskId == task.taskId,
                    onTap: () => controller.selectTask(task.taskId),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _Workspace extends StatelessWidget {
  const _Workspace({required this.controller, required this.onlineDeviceCount});

  final TaskController controller;
  final int onlineDeviceCount;

  @override
  Widget build(BuildContext context) {
    final task = controller.selectedTask;
    return _SurfacePanel(
      child: task == null
          ? _EmptyWorkspace(
              pendingCount: controller.pendingTasks.length,
              onlineDeviceCount: onlineDeviceCount,
            )
          : LayoutBuilder(
              builder: (context, constraints) {
                final isWide = constraints.maxWidth >= 980;
                final header = Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Wrap(
                      spacing: 12,
                      runSpacing: 12,
                      crossAxisAlignment: WrapCrossAlignment.center,
                      children: [
                        const _InfoChip(
                          label: '任务指挥台',
                          icon: Icons.radar_outlined,
                        ),
                        _StatusPill(
                          label: task.status.label,
                          color: _taskStatusColor(task.status),
                        ),
                        _InfoChip(
                          label:
                              '${_formatCount(controller.pendingTasks.length)} 待处理审批',
                          icon: Icons.schedule_send_outlined,
                        ),
                      ],
                    ),
                    const SizedBox(height: 22),
                    Text(
                      task.instruction,
                      style: Theme.of(context).textTheme.displaySmall,
                    ),
                    const SizedBox(height: 10),
                    Text(
                      '设备 ${task.deviceId} · ${_taskNarrative(task.status)}',
                      style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                        color: _AppPalette.textMuted,
                      ),
                    ),
                    const SizedBox(height: 24),
                    _MetricBand(
                      items: [
                        _MetricBandItem(
                          label: '待处理审批',
                          value: _formatCount(controller.pendingTasks.length),
                          accent: _AppPalette.warning,
                        ),
                        _MetricBandItem(
                          label: '恢复检查点',
                          value: task.checkpointId ?? '未写入',
                          accent: _AppPalette.secondary,
                        ),
                        _MetricBandItem(
                          label: '在线设备',
                          value: _formatCount(onlineDeviceCount),
                          accent: _AppPalette.accent,
                        ),
                      ],
                    ),
                  ],
                );

                if (!isWide) {
                  return SingleChildScrollView(
                    padding: const EdgeInsets.all(28),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        header,
                        const SizedBox(height: 24),
                        _NarrativePanel(task: task),
                        const SizedBox(height: 18),
                        _CommandPanel(task: task),
                        const SizedBox(height: 18),
                        SizedBox(height: 320, child: _LogConsole(task: task)),
                        const SizedBox(height: 18),
                        _RecoveryPanel(
                          task: task,
                          pendingCount: controller.pendingTasks.length,
                        ),
                        const SizedBox(height: 18),
                        _ActionPanel(controller: controller, task: task),
                      ],
                    ),
                  );
                }

                return Padding(
                  padding: const EdgeInsets.all(32),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      header,
                      const SizedBox(height: 28),
                      Expanded(
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            Expanded(
                              flex: 9,
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.stretch,
                                children: [
                                  _NarrativePanel(task: task),
                                  const SizedBox(height: 20),
                                  _CommandPanel(task: task),
                                  const SizedBox(height: 20),
                                  Expanded(child: _LogConsole(task: task)),
                                ],
                              ),
                            ),
                            const SizedBox(width: 24),
                            SizedBox(
                              width: 320,
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.stretch,
                                children: [
                                  Expanded(
                                    child: SingleChildScrollView(
                                      child: _RecoveryPanel(
                                        task: task,
                                        pendingCount:
                                            controller.pendingTasks.length,
                                      ),
                                    ),
                                  ),
                                  const SizedBox(height: 20),
                                  _ActionPanel(
                                    controller: controller,
                                    task: task,
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),
    );
  }
}

class _NarrativePanel extends StatelessWidget {
  const _NarrativePanel({required this.task});

  final TaskRecord task;

  @override
  Widget build(BuildContext context) {
    return _InnerPanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const _SectionHeader(title: '审批判断', body: '先确认风险和执行意图，再决定是否允许客户端恢复。'),
          const SizedBox(height: 14),
          Text(
            task.reason ?? '当前任务未命中敏感操作，可继续关注客户端回传的执行状态。',
            style: Theme.of(
              context,
            ).textTheme.bodyLarge?.copyWith(color: _AppPalette.textSoft),
          ),
        ],
      ),
    );
  }
}

class _CommandPanel extends StatelessWidget {
  const _CommandPanel({required this.task});

  final TaskRecord task;

  @override
  Widget build(BuildContext context) {
    final command = task.command ?? task.instruction;
    return _InnerPanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const _SectionHeader(
            title: '命令预览',
            body: '审批通过后，客户端会从对应检查点继续执行这条指令。',
          ),
          const SizedBox(height: 16),
          SelectableText(
            command,
            style: GoogleFonts.ibmPlexMono(
              fontSize: 13,
              color: _AppPalette.textPrimary,
            ),
          ),
          const SizedBox(height: 12),
          ClipRRect(
            borderRadius: BorderRadius.circular(22),
            child: HighlightView(
              command,
              language: 'bash',
              theme: atomOneDarkTheme,
              padding: const EdgeInsets.all(20),
              textStyle: GoogleFonts.ibmPlexMono(fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }
}

class _LogConsole extends StatelessWidget {
  const _LogConsole({required this.task});

  final TaskRecord task;

  @override
  Widget build(BuildContext context) {
    final latestLog = task.logs.isEmpty ? '等待客户端输出...' : task.logs.last;
    return _InnerPanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              const Expanded(
                child: _SectionHeader(
                  title: '执行日志',
                  body: '审批后自动切换到终端视图，持续接收客户端 stdout。',
                ),
              ),
              _InfoChip(
                label: '${task.logs.length} 行',
                icon: Icons.terminal_outlined,
              ),
            ],
          ),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: _AppPalette.canvas.withValues(alpha: 0.55),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(
                color: _AppPalette.divider.withValues(alpha: 0.8),
              ),
            ),
            child: Text(
              latestLog,
              style: GoogleFonts.ibmPlexMono(
                fontSize: 13,
                color: _AppPalette.textPrimary,
              ),
            ),
          ),
          const SizedBox(height: 14),
          Expanded(
            child: Scrollbar(
              child: ListView.separated(
                itemCount: task.logs.length,
                separatorBuilder: (_, _) => const SizedBox(height: 8),
                itemBuilder: (context, index) {
                  return Text(
                    task.logs[index],
                    style: GoogleFonts.ibmPlexMono(
                      fontSize: 13,
                      color: index == task.logs.length - 1
                          ? _AppPalette.textPrimary
                          : _AppPalette.textMuted,
                    ),
                  );
                },
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _RecoveryPanel extends StatelessWidget {
  const _RecoveryPanel({required this.task, required this.pendingCount});

  final TaskRecord task;
  final int pendingCount;

  @override
  Widget build(BuildContext context) {
    return _InnerPanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const _SectionHeader(
            title: '恢复上下文',
            body: '保持审批链路连续，APP 重连后可以直接继续处理挂起任务。',
          ),
          const SizedBox(height: 18),
          _DataRow(label: '恢复检查点', value: task.checkpointId ?? '未写入'),
          const SizedBox(height: 12),
          _DataRow(label: '目标设备', value: task.deviceId),
          const SizedBox(height: 12),
          _DataRow(label: '当前状态', value: task.status.label),
          const SizedBox(height: 12),
          _DataRow(label: '待处理审批', value: _formatCount(pendingCount)),
          const SizedBox(height: 12),
          _DataRow(
            label: '最近输出',
            value: task.logs.isEmpty ? '等待客户端输出' : task.logs.last,
          ),
          if (task.result case final result?) ...[
            const SizedBox(height: 12),
            _DataRow(label: '执行结果', value: result),
          ],
          if (task.error case final error?) ...[
            const SizedBox(height: 12),
            _DataRow(label: '错误信息', value: error, accent: _AppPalette.danger),
          ],
          const SizedBox(height: 22),
          Text('离线恢复', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          Text(
            '网关会持久化挂起请求；审批完成后，客户端从本地 checkpoint 恢复执行。',
            style: Theme.of(
              context,
            ).textTheme.bodyMedium?.copyWith(color: _AppPalette.textMuted),
          ),
        ],
      ),
    );
  }
}

class _ActionPanel extends StatelessWidget {
  const _ActionPanel({required this.controller, required this.task});

  final TaskController controller;
  final TaskRecord task;

  @override
  Widget build(BuildContext context) {
    return _InnerPanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text('审批操作', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          Text(
            task.isAwaitingApproval
                ? '确认后，网关会更新任务状态并通知客户端从检查点恢复。'
                : _taskNarrative(task.status),
            style: Theme.of(
              context,
            ).textTheme.bodyMedium?.copyWith(color: _AppPalette.textMuted),
          ),
          const SizedBox(height: 20),
          if (task.isAwaitingApproval) ...[
            FilledButton(
              onPressed: () => controller.submitDecision(true),
              child: const Text('批准执行'),
            ),
            const SizedBox(height: 12),
            OutlinedButton(
              onPressed: () => controller.submitDecision(false),
              style: OutlinedButton.styleFrom(
                side: const BorderSide(color: _AppPalette.danger),
              ),
              child: const Text('拒绝执行'),
            ),
          ] else
            _InfoChip(
              label: task.status.label,
              icon: task.status == TaskStatus.failed
                  ? Icons.error_outline
                  : Icons.check_circle_outline,
              color: _taskStatusColor(task.status),
            ),
        ],
      ),
    );
  }
}

class _EmptyWorkspace extends StatelessWidget {
  const _EmptyWorkspace({
    required this.pendingCount,
    required this.onlineDeviceCount,
  });

  final int pendingCount;
  final int onlineDeviceCount;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const _InfoChip(label: '任务指挥台', icon: Icons.radar_outlined),
          const SizedBox(height: 20),
          Text(
            '连接网关后，这里会集中展示待审批任务、恢复检查点和执行日志。',
            style: Theme.of(context).textTheme.displaySmall,
          ),
          const SizedBox(height: 14),
          Text(
            '当前没有选中的任务。先连接网关，或从左侧派发新的指令。',
            style: Theme.of(
              context,
            ).textTheme.bodyLarge?.copyWith(color: _AppPalette.textMuted),
          ),
          const SizedBox(height: 24),
          _MetricBand(
            items: [
              _MetricBandItem(
                label: '待处理审批',
                value: _formatCount(pendingCount),
                accent: _AppPalette.warning,
              ),
              _MetricBandItem(
                label: '在线设备',
                value: _formatCount(onlineDeviceCount),
                accent: _AppPalette.secondary,
              ),
              _MetricBandItem(
                label: '实时日志',
                value: '待命',
                accent: _AppPalette.accent,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _SurfacePanel extends StatelessWidget {
  const _SurfacePanel({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: _AppPalette.surface.withValues(alpha: 0.88),
        borderRadius: BorderRadius.circular(34),
        border: Border.all(color: _AppPalette.divider.withValues(alpha: 0.9)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.28),
            blurRadius: 48,
            offset: const Offset(0, 28),
          ),
        ],
      ),
      child: child,
    );
  }
}

class _InnerPanel extends StatelessWidget {
  const _InnerPanel({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: _AppPalette.surfaceRaised.withValues(alpha: 0.8),
        borderRadius: BorderRadius.circular(28),
        border: Border.all(color: _AppPalette.divider.withValues(alpha: 0.75)),
      ),
      child: Padding(padding: const EdgeInsets.all(22), child: child),
    );
  }
}

class _MetricBand extends StatelessWidget {
  const _MetricBand({required this.items});

  final List<_MetricBandItem> items;

  @override
  Widget build(BuildContext context) {
    final children = <Widget>[];
    for (var index = 0; index < items.length; index++) {
      if (index > 0) {
        children.add(
          const VerticalDivider(
            width: 1,
            thickness: 1,
            color: _AppPalette.divider,
          ),
        );
      }
      children.add(
        Expanded(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  items[index].label,
                  style: Theme.of(context).textTheme.labelLarge,
                ),
                const SizedBox(height: 10),
                Text(
                  items[index].value,
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    color: items[index].accent,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
          ),
        ),
      );
    }

    return DecoratedBox(
      decoration: BoxDecoration(
        color: _AppPalette.surfaceRaised.withValues(alpha: 0.65),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: _AppPalette.divider.withValues(alpha: 0.85)),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 18),
        child: Row(children: children),
      ),
    );
  }
}

class _MetricBandItem {
  const _MetricBandItem({
    required this.label,
    required this.value,
    required this.accent,
  });

  final String label;
  final String value;
  final Color accent;
}

class _TaskQueueTile extends StatelessWidget {
  const _TaskQueueTile({
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
        borderRadius: BorderRadius.circular(22),
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 220),
          curve: Curves.easeOutCubic,
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: selected
                ? accent.withValues(alpha: 0.12)
                : _AppPalette.surfaceRaised.withValues(alpha: 0.35),
            borderRadius: BorderRadius.circular(22),
            border: Border.all(
              color: selected
                  ? accent.withValues(alpha: 0.4)
                  : _AppPalette.divider.withValues(alpha: 0.6),
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
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
            ],
          ),
        ),
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
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.14),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: color.withValues(alpha: 0.38)),
      ),
      child: Text(
        label,
        style: Theme.of(context).textTheme.labelLarge?.copyWith(
          color: color,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}

class _InfoChip extends StatelessWidget {
  const _InfoChip({
    required this.label,
    required this.icon,
    this.color = _AppPalette.textSoft,
  });

  final String label;
  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: color.withValues(alpha: 0.24)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: color),
          const SizedBox(width: 8),
          Text(
            label,
            style: Theme.of(
              context,
            ).textTheme.labelLarge?.copyWith(color: color),
          ),
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
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(label, style: Theme.of(context).textTheme.labelLarge),
        const SizedBox(height: 8),
        child,
      ],
    );
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({required this.title, required this.body});

  final String title;
  final String body;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 6),
        Text(
          body,
          style: Theme.of(
            context,
          ).textTheme.bodyMedium?.copyWith(color: _AppPalette.textMuted),
        ),
      ],
    );
  }
}

class _DataRow extends StatelessWidget {
  const _DataRow({
    required this.label,
    required this.value,
    this.accent = _AppPalette.textSoft,
  });

  final String label;
  final String value;
  final Color accent;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: Theme.of(
            context,
          ).textTheme.labelLarge?.copyWith(color: accent),
        ),
        const SizedBox(height: 6),
        Text(value, style: Theme.of(context).textTheme.bodyMedium),
      ],
    );
  }
}

class _EmptyQueueHint extends StatelessWidget {
  const _EmptyQueueHint();

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: _AppPalette.surfaceRaised.withValues(alpha: 0.5),
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: _AppPalette.divider.withValues(alpha: 0.7)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Text(
          '连接网关后，待审批任务和离线恢复请求会显示在这里。',
          style: Theme.of(
            context,
          ).textTheme.bodyMedium?.copyWith(color: _AppPalette.textMuted),
        ),
      ),
    );
  }
}

class _AmbientGlow extends StatelessWidget {
  const _AmbientGlow({required this.size, required this.color});

  final double size;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          gradient: RadialGradient(
            colors: [color.withValues(alpha: 0.22), Colors.transparent],
          ),
        ),
      ),
    );
  }
}

class _Reveal extends StatelessWidget {
  const _Reveal({required this.child, required this.beginOffset});

  final Widget child;
  final Offset beginOffset;

  @override
  Widget build(BuildContext context) {
    return TweenAnimationBuilder<double>(
      duration: const Duration(milliseconds: 520),
      curve: Curves.easeOutCubic,
      tween: Tween(begin: 0, end: 1),
      child: child,
      builder: (context, value, child) {
        return Opacity(
          opacity: value,
          child: Transform.translate(
            offset: Offset(
              beginOffset.dx * (1 - value),
              beginOffset.dy * (1 - value),
            ),
            child: child,
          ),
        );
      },
    );
  }
}

class _AppPalette {
  static const canvas = Color(0xFF071018);
  static const canvasMid = Color(0xFF0D1720);
  static const surface = Color(0xFF101A24);
  static const surfaceRaised = Color(0xFF15212D);
  static const divider = Color(0xFF263646);
  static const textPrimary = Color(0xFFF4EDDE);
  static const textSoft = Color(0xFFD8CDB8);
  static const textMuted = Color(0xFF9BA9B7);
  static const accent = Color(0xFFF28B54);
  static const accentGlow = Color(0xFFF28B54);
  static const secondary = Color(0xFF7AC3B7);
  static const secondaryGlow = Color(0xFF4DA6B4);
  static const warning = Color(0xFFF1B956);
  static const danger = Color(0xFFF56B5C);
  static const idle = Color(0xFF7E8B9A);
}

Color _connectionStatusColor(ConnectionStatus status) {
  switch (status) {
    case ConnectionStatus.connected:
      return _AppPalette.secondary;
    case ConnectionStatus.connecting:
      return _AppPalette.warning;
    case ConnectionStatus.failed:
      return _AppPalette.danger;
    case ConnectionStatus.idle:
      return _AppPalette.idle;
  }
}

Color _taskStatusColor(TaskStatus status) {
  switch (status) {
    case TaskStatus.awaitingApproval:
      return _AppPalette.warning;
    case TaskStatus.approved:
    case TaskStatus.running:
    case TaskStatus.resuming:
    case TaskStatus.completed:
      return _AppPalette.secondary;
    case TaskStatus.rejected:
    case TaskStatus.failed:
      return _AppPalette.danger;
    case TaskStatus.pendingDispatch:
      return _AppPalette.accent;
    case TaskStatus.unknown:
      return _AppPalette.idle;
  }
}

String _taskNarrative(TaskStatus status) {
  switch (status) {
    case TaskStatus.awaitingApproval:
      return '客户端已挂起，等待人工审批';
    case TaskStatus.approved:
      return '审批已通过，等待客户端继续';
    case TaskStatus.rejected:
      return '审批已拒绝，客户端不会恢复';
    case TaskStatus.running:
      return '客户端正在执行低风险步骤';
    case TaskStatus.resuming:
      return '客户端正在从检查点恢复';
    case TaskStatus.completed:
      return '任务已经完成';
    case TaskStatus.failed:
      return '任务执行失败，需要人工复核';
    case TaskStatus.pendingDispatch:
      return '任务已创建，等待客户端接收';
    case TaskStatus.unknown:
      return '状态未识别';
  }
}

String _formatCount(int value) => value.toString().padLeft(2, '0');
