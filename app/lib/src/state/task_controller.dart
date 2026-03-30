import 'package:app/src/models/device_record.dart';
import 'package:app/src/models/task_record.dart';
import 'package:app/src/services/gateway_api.dart';
import 'package:app/src/services/gateway_socket.dart';
import 'package:flutter/foundation.dart';

enum ConnectionStatus { idle, connecting, connected, failed }

class TaskController extends ChangeNotifier {
  TaskController({required this.api, required this.socket});

  final GatewayApi api;
  final GatewaySocket socket;

  ConnectionStatus _status = ConnectionStatus.idle;
  String? _token;
  String? _baseUrl;
  String? _errorMessage;
  String? _selectedTaskId;
  List<DeviceRecord> _devices = const <DeviceRecord>[];
  List<TaskRecord> _tasks = const <TaskRecord>[];

  ConnectionStatus get status => _status;
  String? get token => _token;
  String? get errorMessage => _errorMessage;
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
    _status = ConnectionStatus.connecting;
    _errorMessage = null;
    notifyListeners();

    try {
      final token = await api.login(
        baseUrl: baseUrl,
        username: username,
        password: password,
      );
      final devices = await api.fetchDevices(baseUrl: baseUrl, token: token);
      final pendingApprovals = await api.fetchPendingApprovals(
        baseUrl: baseUrl,
        token: token,
      );

      _baseUrl = baseUrl;
      _token = token;
      _devices = devices;
      _tasks = pendingApprovals;
      _selectedTaskId = pendingApprovals.isNotEmpty
          ? pendingApprovals.first.taskId
          : null;

      await socket.connect(
        baseUrl: baseUrl,
        token: token,
        onEvent: handleSocketEvent,
      );
      _status = ConnectionStatus.connected;
    } catch (error) {
      _status = ConnectionStatus.failed;
      _errorMessage = error.toString();
    }

    notifyListeners();
  }

  Future<void> refresh() async {
    if (_baseUrl == null || _token == null) {
      return;
    }
    _devices = await api.fetchDevices(baseUrl: _baseUrl!, token: _token!);
    final pending = await api.fetchPendingApprovals(
      baseUrl: _baseUrl!,
      token: _token!,
    );
    for (final task in pending) {
      _upsertTask(task, selectIfMissing: _selectedTaskId == null);
    }
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
