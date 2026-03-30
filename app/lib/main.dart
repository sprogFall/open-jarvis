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
    final baseTextTheme = GoogleFonts.ibmPlexSansTextTheme();
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Omni-Agent',
      theme: ThemeData(
        useMaterial3: true,
        scaffoldBackgroundColor: const Color(0xFF101112),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFFF46A4E),
          secondary: Color(0xFF90CAF9),
          surface: Color(0xFF17191C),
          error: Color(0xFFF7685B),
        ),
        textTheme: baseTextTheme.apply(
          bodyColor: const Color(0xFFF3EBDD),
          displayColor: const Color(0xFFF3EBDD),
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
        return Scaffold(
          body: DecoratedBox(
            decoration: const BoxDecoration(
              gradient: RadialGradient(
                center: Alignment.topLeft,
                radius: 1.1,
                colors: [Color(0xFF22272C), Color(0xFF101112)],
              ),
            ),
            child: SafeArea(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: LayoutBuilder(
                  builder: (context, constraints) {
                    final isWide = constraints.maxWidth >= 980;
                    final sidebar = _Sidebar(
                      controller: controller,
                      baseUrlController: _baseUrlController,
                      usernameController: _usernameController,
                      passwordController: _passwordController,
                      instructionController: _instructionController,
                      selectedDeviceId: _selectedDeviceId,
                      onDeviceChanged: (value) {
                        setState(() {
                          _selectedDeviceId = value;
                        });
                      },
                    );
                    final workspace = _Workspace(controller: controller);
                    if (isWide) {
                      return Row(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          SizedBox(width: 320, child: sidebar),
                          const SizedBox(width: 20),
                          Expanded(child: workspace),
                        ],
                      );
                    }
                    return Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        SizedBox(height: 520, child: sidebar),
                        const SizedBox(height: 16),
                        Expanded(child: workspace),
                      ],
                    );
                  },
                ),
              ),
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
    required this.onDeviceChanged,
  });

  final TaskController controller;
  final TextEditingController baseUrlController;
  final TextEditingController usernameController;
  final TextEditingController passwordController;
  final TextEditingController instructionController;
  final String? selectedDeviceId;
  final ValueChanged<String?> onDeviceChanged;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final statusColor = switch (controller.status) {
      ConnectionStatus.connected => const Color(0xFF2DB785),
      ConnectionStatus.connecting => const Color(0xFFF5A524),
      ConnectionStatus.failed => const Color(0xFFF7685B),
      ConnectionStatus.idle => const Color(0xFF708090),
    };

    return AnimatedSlide(
      duration: const Duration(milliseconds: 280),
      offset: const Offset(-0.02, 0),
      child: DecoratedBox(
        decoration: BoxDecoration(
          color: const Color(0xFF17191C).withValues(alpha: 0.94),
          borderRadius: BorderRadius.circular(28),
          border: Border.all(color: const Color(0xFF2A2F35)),
        ),
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Row(
                  children: [
                    Text(
                      'Omni-Agent',
                      style: theme.textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const Spacer(),
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
                const SizedBox(height: 8),
                Text(
                  controller.pendingTasks.isEmpty
                      ? '普通调度模式'
                      : '存在待审批任务，优先恢复执行。',
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: const Color(0xFFC8C1B4),
                  ),
                ),
                if (controller.errorMessage case final error?)
                  Padding(
                    padding: const EdgeInsets.only(top: 12),
                    child: Text(
                      error,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: const Color(0xFFF7685B),
                      ),
                    ),
                  ),
                const SizedBox(height: 24),
                _LabeledField(
                  label: 'Gateway URL',
                  child: TextField(
                    controller: baseUrlController,
                    decoration: _inputDecoration('http://127.0.0.1:8000'),
                  ),
                ),
                const SizedBox(height: 12),
                _LabeledField(
                  label: '用户名',
                  child: TextField(
                    controller: usernameController,
                    decoration: _inputDecoration('operator'),
                  ),
                ),
                const SizedBox(height: 12),
                _LabeledField(
                  label: '密码',
                  child: TextField(
                    controller: passwordController,
                    obscureText: true,
                    decoration: _inputDecoration('passw0rd'),
                  ),
                ),
                const SizedBox(height: 12),
                FilledButton(
                  onPressed: () {
                    controller.connect(
                      baseUrl: baseUrlController.text.trim(),
                      username: usernameController.text.trim(),
                      password: passwordController.text,
                    );
                  },
                  style: FilledButton.styleFrom(
                    backgroundColor: const Color(0xFFF46A4E),
                    foregroundColor: const Color(0xFF101112),
                    padding: const EdgeInsets.symmetric(vertical: 16),
                  ),
                  child: const Text('连接网关'),
                ),
                const SizedBox(height: 28),
                Text(
                  '任务派发',
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  value: selectedDeviceId,
                  dropdownColor: const Color(0xFF202328),
                  decoration: _inputDecoration('选择设备'),
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
                const SizedBox(height: 12),
                TextField(
                  controller: instructionController,
                  maxLines: 5,
                  decoration: _inputDecoration('例如：查看系统负载，然后重启容器 api-service'),
                ),
                const SizedBox(height: 12),
                OutlinedButton(
                  onPressed: selectedDeviceId == null
                      ? null
                      : () {
                          controller.createTask(
                            deviceId: selectedDeviceId!,
                            instruction: instructionController.text.trim(),
                          );
                        },
                  style: OutlinedButton.styleFrom(
                    foregroundColor: const Color(0xFFF3EBDD),
                    side: const BorderSide(color: Color(0xFF3A414A)),
                    padding: const EdgeInsets.symmetric(vertical: 16),
                  ),
                  child: const Text('派发任务'),
                ),
                const SizedBox(height: 24),
                Text(
                  '任务队列',
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 8),
                SizedBox(
                  height: 180,
                  child: ListView.separated(
                    itemCount: controller.tasks.length,
                    separatorBuilder: (_, _) =>
                        const Divider(color: Color(0xFF2A2F35)),
                    itemBuilder: (context, index) {
                      final task = controller.tasks[index];
                      final selected =
                          controller.selectedTask?.taskId == task.taskId;
                      return InkWell(
                        onTap: () => controller.selectTask(task.taskId),
                        child: AnimatedContainer(
                          duration: const Duration(milliseconds: 220),
                          padding: const EdgeInsets.symmetric(
                            vertical: 12,
                            horizontal: 12,
                          ),
                          decoration: BoxDecoration(
                            color: selected
                                ? const Color(0x26F46A4E)
                                : Colors.transparent,
                            borderRadius: BorderRadius.circular(14),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                task.status.label,
                                style: theme.textTheme.labelLarge?.copyWith(
                                  color: const Color(0xFFF46A4E),
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                task.instruction,
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  InputDecoration _inputDecoration(String hintText) {
    return InputDecoration(
      hintText: hintText,
      filled: true,
      fillColor: const Color(0xFF111317),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: const BorderSide(color: Color(0xFF2A2F35)),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: const BorderSide(color: Color(0xFF2A2F35)),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: const BorderSide(color: Color(0xFFF46A4E)),
      ),
    );
  }
}

class _Workspace extends StatelessWidget {
  const _Workspace({required this.controller});

  final TaskController controller;

  @override
  Widget build(BuildContext context) {
    final task = controller.selectedTask;
    if (task == null) {
      return DecoratedBox(
        decoration: BoxDecoration(
          color: const Color(0xFF17191C).withValues(alpha: 0.86),
          borderRadius: BorderRadius.circular(28),
          border: Border.all(color: const Color(0xFF2A2F35)),
        ),
        child: const Center(child: Text('连接网关后，在这里处理待审批任务与实时日志。')),
      );
    }

    return DecoratedBox(
      decoration: BoxDecoration(
        color: const Color(0xFF17191C).withValues(alpha: 0.86),
        borderRadius: BorderRadius.circular(28),
        border: Border.all(color: const Color(0xFF2A2F35)),
      ),
      child: AnimatedSwitcher(
        duration: const Duration(milliseconds: 240),
        child: Padding(
          key: ValueKey<String>(task.taskId),
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      task.instruction,
                      style: Theme.of(context).textTheme.headlineSmall
                          ?.copyWith(fontWeight: FontWeight.w700),
                    ),
                  ),
                  const SizedBox(width: 16),
                  _StatusPill(
                    label: task.status.label,
                    color: task.isAwaitingApproval
                        ? const Color(0xFFF5A524)
                        : const Color(0xFFF46A4E),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                '设备 ${task.deviceId}',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: const Color(0xFFC8C1B4),
                ),
              ),
              const SizedBox(height: 20),
              if (controller.pendingTasks.isNotEmpty)
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: const Color(0x14F5A524),
                    borderRadius: BorderRadius.circular(18),
                    border: Border.all(color: const Color(0x33F5A524)),
                  ),
                  child: const Text(
                    '待审批任务',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                  ),
                ),
              const SizedBox(height: 20),
              _SectionTitle(
                title: '审批说明',
                body: task.reason ?? '当前任务无需人工审批，可继续观察日志输出。',
              ),
              const SizedBox(height: 16),
              _SectionTitle(title: '命令预览', body: '审批通过后，客户端会从对应检查点继续执行这条命令。'),
              const SizedBox(height: 8),
              SelectableText(
                task.command ?? task.instruction,
                style: GoogleFonts.ibmPlexMono(color: const Color(0xFFF3EBDD)),
              ),
              const SizedBox(height: 8),
              ClipRRect(
                borderRadius: BorderRadius.circular(18),
                child: HighlightView(
                  task.command ?? task.instruction,
                  language: 'bash',
                  theme: atomOneDarkTheme,
                  padding: const EdgeInsets.all(18),
                  textStyle: GoogleFonts.ibmPlexMono(fontSize: 13),
                ),
              ),
              const SizedBox(height: 20),
              Expanded(
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    color: const Color(0xFF111317),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: const Color(0xFF2A2F35)),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(18),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        const Text(
                          '实时日志',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        if (task.logs.isNotEmpty) ...[
                          const SizedBox(height: 8),
                          Text(
                            task.logs.last,
                            style: GoogleFonts.ibmPlexMono(
                              fontSize: 13,
                              color: const Color(0xFFF3EBDD),
                            ),
                          ),
                        ],
                        const SizedBox(height: 12),
                        Expanded(
                          child: ListView.builder(
                            itemCount: task.logs.length,
                            itemBuilder: (context, index) {
                              return Padding(
                                padding: const EdgeInsets.only(bottom: 8),
                                child: Text(
                                  task.logs[index],
                                  style: GoogleFonts.ibmPlexMono(
                                    fontSize: 13,
                                    color: const Color(0xFFC8C1B4),
                                  ),
                                ),
                              );
                            },
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              if (task.isAwaitingApproval) ...[
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton(
                        onPressed: () => controller.submitDecision(false),
                        style: OutlinedButton.styleFrom(
                          foregroundColor: const Color(0xFFF3EBDD),
                          side: const BorderSide(color: Color(0xFFF7685B)),
                          padding: const EdgeInsets.symmetric(vertical: 16),
                        ),
                        child: const Text('拒绝执行'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: FilledButton(
                        onPressed: () => controller.submitDecision(true),
                        style: FilledButton.styleFrom(
                          backgroundColor: const Color(0xFFF46A4E),
                          foregroundColor: const Color(0xFF101112),
                          padding: const EdgeInsets.symmetric(vertical: 16),
                        ),
                        child: const Text('批准执行'),
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
        border: Border.all(color: color.withValues(alpha: 0.4)),
      ),
      child: Text(
        label,
        style: TextStyle(color: color, fontWeight: FontWeight.w600),
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
        Text(
          label,
          style: Theme.of(
            context,
          ).textTheme.labelLarge?.copyWith(color: const Color(0xFFC8C1B4)),
        ),
        const SizedBox(height: 8),
        child,
      ],
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
        Text(
          title,
          style: Theme.of(
            context,
          ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 6),
        Text(
          body,
          style: Theme.of(
            context,
          ).textTheme.bodyMedium?.copyWith(color: const Color(0xFFC8C1B4)),
        ),
      ],
    );
  }
}
