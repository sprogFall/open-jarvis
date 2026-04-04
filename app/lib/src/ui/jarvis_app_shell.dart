import 'dart:async';
import 'dart:math' as math;

import 'package:app/src/state/task_controller.dart';
import 'package:app/src/ui/app_bar.dart';
import 'package:app/src/ui/chat/composer_bar.dart';
import 'package:app/src/ui/chat/conversation_viewport.dart';
import 'package:app/src/ui/components/backdrop.dart';
import 'package:app/src/ui/settings_sheet.dart';
import 'package:app/src/ui/sidebar/thread_rail.dart';
import 'package:app/src/ui/workspace_summary.dart';
import 'package:flutter/material.dart';

class JarvisAppShell extends StatefulWidget {
  const JarvisAppShell({super.key, required this.controller});

  final TaskController controller;

  @override
  State<JarvisAppShell> createState() => _JarvisAppShellState();
}

class _JarvisAppShellState extends State<JarvisAppShell> {
  static const _defaultBaseUrl = 'http://127.0.0.1:8000';
  static const _defaultUsername = 'operator';

  final _scaffoldKey = GlobalKey<ScaffoldState>();
  final _baseUrlController = TextEditingController();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final _composerController = TextEditingController();
  String? _selectedDeviceId;

  TaskController get controller => widget.controller;

  @override
  void initState() {
    super.initState();
    _baseUrlController.text = controller.savedBaseUrl ?? _defaultBaseUrl;
    _usernameController.text = controller.savedUsername ?? _defaultUsername;
    _passwordController.text = controller.savedPassword ?? '';
    _selectedDeviceId = controller.preferredDeviceId;
  }

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
    final preferredDeviceId = controller.preferredDeviceId;
    if (_selectedDeviceId == null &&
        preferredDeviceId != null &&
        availableDeviceIds.contains(preferredDeviceId)) {
      _selectedDeviceId = preferredDeviceId;
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
        return SettingsSheet(
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

  void _handleDeviceChanged(String? value) {
    setState(() {
      _selectedDeviceId = value;
    });
    unawaited(controller.savePreferredDeviceId(value));
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
            final rail = ThreadRail(
              controller: controller,
              selectedDeviceId: _selectedDeviceId,
              onDeviceChanged: _handleDeviceChanged,
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
              appBar: JarvisAppBar(
                isWide: isWide,
                controller: controller,
                selectedDeviceId: _selectedDeviceId,
                onOpenMenu: () => _scaffoldKey.currentState?.openDrawer(),
                onOpenSettings: _openSettingsSheet,
              ),
              body: Backdrop(
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
                                  WorkspaceSummary(
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
                                    child: ConversationViewport(
                                      controller: controller,
                                      composerController: _composerController,
                                      onPrefillInstruction: _prefillInstruction,
                                    ),
                                  ),
                                  const SizedBox(height: 16),
                                  ComposerBar(
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
