import 'dart:async';
import 'dart:math' as math;

import 'package:app/src/state/task_controller.dart';
import 'package:app/src/ui/app_bar.dart';
import 'package:app/src/ui/chat/composer_bar.dart';
import 'package:app/src/ui/chat/conversation_viewport.dart';
import 'package:app/src/ui/components/backdrop.dart';
import 'package:app/src/ui/settings_sheet.dart';
import 'package:app/src/ui/setup_tray.dart';
import 'package:app/src/ui/sidebar/thread_rail.dart';
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
  bool _isSetupExpanded = false;

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
    final availableDeviceIds = controller.devices.map((device) => device.deviceId).toSet();
    if (_selectedDeviceId != null && !availableDeviceIds.contains(_selectedDeviceId)) {
      _selectedDeviceId = null;
    }
    final preferredDeviceId = controller.preferredDeviceId;
    if (_selectedDeviceId == null &&
        preferredDeviceId != null &&
        availableDeviceIds.contains(preferredDeviceId)) {
      _selectedDeviceId = preferredDeviceId;
    }
    _selectedDeviceId ??=
        controller.devices.isNotEmpty ? controller.devices.first.deviceId : null;
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
          onReconnect: () async {
            await controller.reconnect();
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
    setState(() {
      _isSetupExpanded = false;
    });
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

  void _toggleSetupPanel() {
    setState(() {
      _isSetupExpanded = !_isSetupExpanded;
    });
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: controller,
      builder: (context, _) {
        _syncSelectedDevice();
        return LayoutBuilder(
          builder: (context, constraints) {
            final horizontalPadding = constraints.maxWidth >= 900 ? 24.0 : 16.0;
            final rail = ThreadRail(
              controller: controller,
              selectedDeviceId: _selectedDeviceId,
              onDeviceChanged: _handleDeviceChanged,
              onNewChat: () => _startNewChat(closeDrawer: true),
              onSelectTask: (taskId) => _selectTask(taskId, closeDrawer: true),
            );

            return Scaffold(
              key: _scaffoldKey,
              drawer: Drawer(
                key: const Key('threadDrawer'),
                width: math.min(constraints.maxWidth * 0.88, 380),
                child: SafeArea(
                  bottom: false,
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: rail,
                  ),
                ),
              ),
              appBar: JarvisAppBar(
                isWide: false,
                controller: controller,
                selectedDeviceId: _selectedDeviceId,
                onOpenMenu: () => _scaffoldKey.currentState?.openDrawer(),
                onOpenSettings: _openSettingsSheet,
              ),
              body: Backdrop(
                child: SafeArea(
                  top: false,
                  child: Align(
                    alignment: Alignment.topCenter,
                    child: ConstrainedBox(
                      constraints: const BoxConstraints(maxWidth: 960),
                      child: Column(
                        children: [
                          Padding(
                            padding: EdgeInsets.fromLTRB(
                              horizontalPadding,
                              12,
                              horizontalPadding,
                              0,
                            ),
                            child: SetupTray(
                              controller: controller,
                              expanded: _isSetupExpanded,
                              selectedDeviceId: _selectedDeviceId,
                              onToggle: _toggleSetupPanel,
                              onDeviceChanged: _handleDeviceChanged,
                              onPrefillInstruction: _prefillInstruction,
                              onFocusPending: () {
                                if (controller.pendingTasks.isNotEmpty) {
                                  controller.selectTask(
                                    controller.pendingTasks.first.taskId,
                                  );
                                  setState(() {
                                    _isSetupExpanded = false;
                                  });
                                }
                              },
                            ),
                          ),
                          Expanded(
                            child: Padding(
                              padding: EdgeInsets.fromLTRB(
                                horizontalPadding,
                                8,
                                horizontalPadding,
                                8,
                              ),
                              child: ConversationViewport(
                                controller: controller,
                                composerController: _composerController,
                                onPrefillInstruction: _prefillInstruction,
                              ),
                            ),
                          ),
                          Padding(
                            padding: EdgeInsets.fromLTRB(
                              horizontalPadding,
                              0,
                              horizontalPadding,
                              16,
                            ),
                            child: ComposerBar(
                              controller: controller,
                              selectedDeviceId: _selectedDeviceId,
                              composerController: _composerController,
                              onComposerChanged: () => setState(() {}),
                              onSend: _sendInstruction,
                            ),
                          ),
                        ],
                      ),
                    ),
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
