import 'package:app/src/models/connection_session.dart';
import 'package:app/src/models/device_record.dart';
import 'package:app/src/models/task_record.dart';
import 'package:app/src/services/connection_session_store.dart';
import 'package:app/src/services/gateway_api.dart';
import 'package:app/src/services/gateway_socket.dart';
import 'package:flutter/foundation.dart';

enum ConnectionStatus { idle, connecting, connected, failed }

class TaskController extends ChangeNotifier {
  TaskController({
    required this.api,
    required this.socket,
    ConnectionSessionStore? sessionStore,
  }) : sessionStore = sessionStore ?? const NoopConnectionSessionStore();

  final GatewayApi api;
  final GatewaySocket socket;
  final ConnectionSessionStore sessionStore;

  ConnectionStatus _status = ConnectionStatus.idle;
  String? _token;
  String? _baseUrl;
  String? _errorMessage;
  String? _selectedTaskId;
  ConnectionSession? _session;
  List<DeviceRecord> _devices = const <DeviceRecord>[];
  List<TaskRecord> _tasks = const <TaskRecord>[];

  ConnectionStatus get status => _status;
  String? get token => _token;
  String? get errorMessage => _errorMessage;
  bool get hasSavedSession => _session != null;
  String? get savedBaseUrl => _session?.baseUrl;
  String? get savedUsername => _session?.username;
  String? get savedPassword => _session?.password;
  String? get preferredDeviceId => _session?.preferredDeviceId;
  bool get canReconnect {
    final savedToken = _token ?? _session?.token;
    final savedPassword = _session?.password;
    return _session != null &&
        ((savedToken != null && savedToken.isNotEmpty) ||
            (savedPassword != null && savedPassword.isNotEmpty));
  }

  List<DeviceRecord> get devices => List<DeviceRecord>.unmodifiable(_devices);
  List<TaskRecord> get tasks => List<TaskRecord>.unmodifiable(_tasks);
  List<TaskRecord> get pendingTasks => _tasks
      .where((task) => task.status == TaskStatus.awaitingApproval)
      .toList(growable: false);

  TaskRecord? get selectedTask {
    if (_tasks.isEmpty || _selectedTaskId == null) {
      return null;
    }
    for (final task in _tasks) {
      if (task.taskId == _selectedTaskId) {
        return task;
      }
    }
    return _tasks.first;
  }

  Future<void> connect({
    required String baseUrl,
    required String username,
    required String password,
  }) async {
    final resolvedPassword = password.isNotEmpty ? password : null;
    final sessionDraft = ConnectionSession(
      baseUrl: baseUrl,
      username: username,
      password: resolvedPassword,
      preferredDeviceId: _session?.preferredDeviceId,
    );
    await _saveSession(sessionDraft);

    _status = ConnectionStatus.connecting;
    _errorMessage = null;
    notifyListeners();

    try {
      final token = await api.login(
        baseUrl: baseUrl,
        username: username,
        password: password,
      );
      await _connectWithToken(
        sessionDraft.copyWith(token: token),
        notifyOnStart: false,
      );
    } catch (error) {
      await _clearConnectedState();
      _status = ConnectionStatus.failed;
      _errorMessage = error.toString();
    }

    notifyListeners();
  }

  Future<void> restoreSavedSession() async {
    final session = await sessionStore.load();
    if (session == null) {
      return;
    }
    _session = session;
    final token = session.token;
    if (token != null && token.isNotEmpty) {
      final restoredError = await _connectWithToken(session);
      if (restoredError == null) {
        return;
      }
      if (!_shouldRetryWithPassword(restoredError, session)) {
        return;
      }
    }
    final password = session.password;
    if (password == null || password.isEmpty) {
      notifyListeners();
      return;
    }
    await _restoreWithPassword(session, password);
  }

  Future<void> refresh() async {
    if (_baseUrl == null || _token == null) {
      return;
    }
    _devices = await api.fetchDevices(baseUrl: _baseUrl!, token: _token!);
    await _reconcilePreferredDevice();
    final pending = await api.fetchPendingApprovals(
      baseUrl: _baseUrl!,
      token: _token!,
    );
    for (final task in pending) {
      _upsertTask(task, selectIfMissing: _selectedTaskId == null);
    }
    notifyListeners();
  }

  Future<void> reconnect() async {
    final session = _session;
    if (session == null) {
      _status = ConnectionStatus.failed;
      _errorMessage = '当前还没有保存连接信息，请先修改连接。';
      notifyListeners();
      return;
    }

    final activeToken = _token ?? session.token;
    final password = session.password;
    final hasPassword = password != null && password.isNotEmpty;
    final hasToken = activeToken != null && activeToken.isNotEmpty;
    final reconnectSession = hasToken
        ? session.copyWith(token: activeToken)
        : session;

    if (_status != ConnectionStatus.connected && hasPassword) {
      await _restoreWithPassword(reconnectSession, password);
      return;
    }
    if (hasToken) {
      await _connectWithToken(reconnectSession);
      return;
    }
    if (hasPassword) {
      await _restoreWithPassword(reconnectSession, password);
      return;
    }

    _status = ConnectionStatus.failed;
    _errorMessage = '当前连接缺少可用的登录信息，请修改连接后重新登录。';
    notifyListeners();
  }

  Future<void> savePreferredDeviceId(String? deviceId) async {
    final session = _session;
    if (session == null) {
      return;
    }
    await _saveSession(
      deviceId == null
          ? session.copyWith(clearPreferredDeviceId: true)
          : session.copyWith(preferredDeviceId: deviceId),
    );
    notifyListeners();
  }

  Future<void> createTask({
    required String deviceId,
    required String instruction,
  }) async {
    final baseUrl = _baseUrl;
    final token = _token;
    if (baseUrl == null || token == null) {
      throw StateError('Gateway connection is not ready');
    }
    final task = await api.createTask(
      baseUrl: baseUrl,
      token: token,
      deviceId: deviceId,
      instruction: instruction,
    );
    _upsertTask(task, select: true);
    notifyListeners();
  }

  Future<void> submitDecision(bool approved) async {
    final baseUrl = _baseUrl;
    final token = _token;
    final selectedTask = this.selectedTask;
    if (baseUrl == null || token == null || selectedTask == null) {
      throw StateError('No task selected');
    }
    final task = await api.submitDecision(
      baseUrl: baseUrl,
      token: token,
      taskId: selectedTask.taskId,
      approved: approved,
    );
    _upsertTask(task, select: true);
    notifyListeners();
  }

  List<String> logsFor(String taskId) {
    final task = _findTask(taskId);
    return task?.logs ?? const <String>[];
  }

  void selectTask(String taskId) {
    _selectedTaskId = taskId;
    notifyListeners();
  }

  void clearSelection() {
    _selectedTaskId = null;
    notifyListeners();
  }

  void handleSocketEvent(Map<String, dynamic> event) {
    final type = event['type'];
    if (type == 'TASK_SNAPSHOT') {
      final incoming = TaskRecord.fromJson(
        event['task'] as Map<String, dynamic>,
      );
      final existing = _findTask(incoming.taskId);
      final merged = incoming.copyWith(
        logs: incoming.logs.isNotEmpty ? incoming.logs : existing?.logs,
      );
      _upsertTask(merged, selectIfMissing: _selectedTaskId == null);
      notifyListeners();
      return;
    }
    if (type == 'TASK_LOG') {
      final taskId = event['task_id'] as String;
      final existing = _findTask(taskId);
      if (existing == null) {
        return;
      }
      _upsertTask(
        existing.copyWith(logs: [...existing.logs, event['message'] as String]),
      );
      notifyListeners();
    }
  }

  Future<Object?> _connectWithToken(
    ConnectionSession session, {
    bool notifyOnStart = true,
  }) async {
    _status = ConnectionStatus.connecting;
    _errorMessage = null;
    if (notifyOnStart) {
      notifyListeners();
    }

    try {
      final token = session.token;
      if (token == null || token.isEmpty) {
        throw StateError('Saved gateway session is missing token');
      }
      final devices = await api.fetchDevices(
        token: token,
        baseUrl: session.baseUrl,
      );
      final pendingApprovals = await api.fetchPendingApprovals(
        baseUrl: session.baseUrl,
        token: token,
      );
      await socket.connect(
        baseUrl: session.baseUrl,
        token: token,
        onEvent: handleSocketEvent,
      );

      _baseUrl = session.baseUrl;
      _token = token;
      _devices = devices;
      _tasks = pendingApprovals;
      _selectedTaskId = pendingApprovals.isNotEmpty
          ? pendingApprovals.first.taskId
          : null;
      await _saveSession(session);
      await _reconcilePreferredDevice();
      _status = ConnectionStatus.connected;
    } catch (error) {
      await _clearConnectedState();
      _status = ConnectionStatus.failed;
      _errorMessage = _savedSessionError(error);
      _session = session;
      notifyListeners();
      return error;
    }

    notifyListeners();
    return null;
  }

  Future<void> _saveSession(ConnectionSession session) async {
    _session = session;
    await sessionStore.save(session);
  }

  Future<void> _restoreWithPassword(
    ConnectionSession session,
    String password,
  ) async {
    _status = ConnectionStatus.connecting;
    _errorMessage = null;
    notifyListeners();

    try {
      final token = await api.login(
        baseUrl: session.baseUrl,
        username: session.username,
        password: password,
      );
      await _connectWithToken(
        session.copyWith(password: password, token: token),
        notifyOnStart: false,
      );
    } catch (error) {
      await _clearConnectedState();
      _status = ConnectionStatus.failed;
      _errorMessage = _savedSessionError(error);
      _session = session.copyWith(password: password);
      notifyListeners();
    }
  }

  bool _shouldRetryWithPassword(Object error, ConnectionSession session) {
    final password = session.password;
    if (password == null || password.isEmpty) {
      return false;
    }
    final message = error.toString();
    return message.contains('401') ||
        message.contains('403') ||
        message.contains('missing token');
  }

  Future<void> _reconcilePreferredDevice() async {
    final session = _session;
    if (session == null) {
      return;
    }
    final savedDeviceId = session.preferredDeviceId;
    final availableDeviceIds = _devices
        .map((device) => device.deviceId)
        .toSet();
    final nextDeviceId = availableDeviceIds.contains(savedDeviceId)
        ? savedDeviceId
        : (_devices.isNotEmpty ? _devices.first.deviceId : null);
    if (nextDeviceId == savedDeviceId) {
      return;
    }
    await _saveSession(
      nextDeviceId == null
          ? session.copyWith(clearPreferredDeviceId: true)
          : session.copyWith(preferredDeviceId: nextDeviceId),
    );
  }

  Future<void> _clearConnectedState() async {
    await socket.disconnect();
    _baseUrl = null;
    _token = null;
    _devices = const <DeviceRecord>[];
    _tasks = const <TaskRecord>[];
    _selectedTaskId = null;
  }

  String _savedSessionError(Object error) {
    final message = error.toString();
    if (message.contains('401')) {
      return '已保存的登录态失效，请重新连接或修改连接信息。';
    }
    return message;
  }

  TaskRecord? _findTask(String taskId) {
    for (final task in _tasks) {
      if (task.taskId == taskId) {
        return task;
      }
    }
    return null;
  }

  void _upsertTask(
    TaskRecord task, {
    bool select = false,
    bool selectIfMissing = false,
  }) {
    final nextTasks = [..._tasks];
    final index = nextTasks.indexWhere((item) => item.taskId == task.taskId);
    if (index >= 0) {
      nextTasks[index] = task;
    } else {
      nextTasks.insert(0, task);
    }
    _tasks = nextTasks;
    if (select || (_selectedTaskId == null && selectIfMissing)) {
      _selectedTaskId = task.taskId;
    }
  }

  @override
  void dispose() {
    socket.disconnect();
    super.dispose();
  }
}
