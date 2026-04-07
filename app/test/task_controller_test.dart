import 'package:app/src/models/device_record.dart';
import 'package:app/src/models/connection_session.dart';
import 'package:app/src/models/task_record.dart';
import 'package:app/src/services/connection_session_store.dart';
import 'package:app/src/services/gateway_api.dart';
import 'package:app/src/services/gateway_socket.dart';
import 'package:app/src/state/task_controller.dart';
import 'package:flutter_test/flutter_test.dart';

class FakeGatewayApi implements GatewayApi {
  final List<String> deletedTaskIds = <String>[];

  @override
  Future<String> login({
    required String baseUrl,
    required String username,
    required String password,
  }) async {
    return 'jwt-token';
  }

  @override
  Future<List<TaskRecord>> fetchTasks({
    required String baseUrl,
    required String token,
  }) async {
    return [
      TaskRecord.fromJson({
        'task_id': 'task-1',
        'device_id': 'device-alpha',
        'instruction': '查看系统负载，然后重启容器 api-service',
        'status': 'AWAITING_APPROVAL',
        'checkpoint_id': 'cp_001',
        'command': 'docker restart api-service',
        'reason': '重启容器会打断服务，需要人工确认',
        'result': null,
        'error': null,
        'logs': ['load1=0.42'],
      }),
    ];
  }

  @override
  Future<List<TaskRecord>> fetchPendingApprovals({
    required String baseUrl,
    required String token,
  }) async {
    return (await fetchTasks(baseUrl: baseUrl, token: token))
        .where((task) => task.status == TaskStatus.awaitingApproval)
        .toList(growable: false);
  }

  @override
  Future<List<DeviceRecord>> fetchDevices({
    required String baseUrl,
    required String token,
  }) async {
    return [const DeviceRecord(deviceId: 'device-alpha', connected: true)];
  }

  @override
  Future<TaskRecord> createTask({
    required String baseUrl,
    required String token,
    required String deviceId,
    required String instruction,
  }) async {
    return TaskRecord.fromJson({
      'task_id': 'task-2',
      'device_id': deviceId,
      'instruction': instruction,
      'status': 'PENDING_DISPATCH',
      'checkpoint_id': null,
      'command': null,
      'reason': null,
      'result': null,
      'error': null,
      'logs': <String>[],
    });
  }

  @override
  Future<TaskRecord> submitDecision({
    required String baseUrl,
    required String token,
    required String taskId,
    required bool approved,
  }) async {
    return TaskRecord.fromJson({
      'task_id': taskId,
      'device_id': 'device-alpha',
      'instruction': '查看系统负载，然后重启容器 api-service',
      'status': approved ? 'APPROVED' : 'REJECTED',
      'checkpoint_id': 'cp_001',
      'command': 'docker restart api-service',
      'reason': '重启容器会打断服务，需要人工确认',
      'result': null,
      'error': null,
      'logs': ['load1=0.42'],
    });
  }

  @override
  Future<void> deleteTask({
    required String baseUrl,
    required String token,
    required String taskId,
  }) async {
    deletedTaskIds.add(taskId);
  }
}

class FakeGatewaySocket implements GatewaySocket {
  String? connectedBaseUrl;
  String? connectedToken;
  void Function(Map<String, dynamic> event)? onEvent;

  @override
  Future<void> connect({
    required String baseUrl,
    required String token,
    required void Function(Map<String, dynamic> event) onEvent,
  }) async {
    connectedBaseUrl = baseUrl;
    connectedToken = token;
    this.onEvent = onEvent;
  }

  @override
  Future<void> disconnect() async {}
}

class FakeConnectionSessionStore implements ConnectionSessionStore {
  FakeConnectionSessionStore({this.session});

  ConnectionSession? session;

  @override
  Future<ConnectionSession?> load() async => session;

  @override
  Future<void> save(ConnectionSession nextSession) async {
    session = nextSession;
  }
}

class RestoreGatewayApi extends FakeGatewayApi {
  @override
  Future<String> login({
    required String baseUrl,
    required String username,
    required String password,
  }) {
    throw StateError('restore should not call login');
  }
}

class ExpiringTokenGatewayApi extends FakeGatewayApi {
  String? lastLoginBaseUrl;
  String? lastLoginUsername;
  String? lastLoginPassword;

  @override
  Future<String> login({
    required String baseUrl,
    required String username,
    required String password,
  }) async {
    lastLoginBaseUrl = baseUrl;
    lastLoginUsername = username;
    lastLoginPassword = password;
    return 'fresh-token';
  }

  @override
  Future<List<DeviceRecord>> fetchDevices({
    required String baseUrl,
    required String token,
  }) async {
    if (token != 'fresh-token') {
      throw StateError(
        'Gateway request failed: 401 {"detail":"Invalid token"}',
      );
    }
    return super.fetchDevices(baseUrl: baseUrl, token: token);
  }

  @override
  Future<List<TaskRecord>> fetchTasks({
    required String baseUrl,
    required String token,
  }) async {
    if (token != 'fresh-token') {
      throw StateError(
        'Gateway request failed: 401 {"detail":"Invalid token"}',
      );
    }
    return super.fetchTasks(baseUrl: baseUrl, token: token);
  }
}

class OfflineGatewayApi extends FakeGatewayApi {
  @override
  Future<List<DeviceRecord>> fetchDevices({
    required String baseUrl,
    required String token,
  }) {
    throw StateError('Gateway request failed: network unreachable');
  }
}

class MultiDeviceGatewayApi extends FakeGatewayApi {
  @override
  Future<List<DeviceRecord>> fetchDevices({
    required String baseUrl,
    required String token,
  }) async {
    return const [
      DeviceRecord(deviceId: 'device-alpha', connected: true),
      DeviceRecord(deviceId: 'device-beta', connected: true),
    ];
  }
}

class MultiDeviceRestoreGatewayApi extends MultiDeviceGatewayApi {
  @override
  Future<String> login({
    required String baseUrl,
    required String username,
    required String password,
  }) {
    throw StateError('restore should not call login');
  }
}

void main() {
  test('connect loads task history and selects the first awaiting task', () async {
    final socket = FakeGatewaySocket();
    final controller = TaskController(api: FakeGatewayApi(), socket: socket);

    await controller.connect(
      baseUrl: 'http://127.0.0.1:8000',
      username: 'operator',
      password: 'passw0rd',
    );

    expect(controller.status, ConnectionStatus.connected);
    expect(controller.token, 'jwt-token');
    expect(controller.pendingTasks.single.taskId, 'task-1');
    expect(controller.selectedTask?.taskId, 'task-1');
    expect(socket.connectedToken, 'jwt-token');
  });

  test('connect keeps completed chats in task history after restart', () async {
    final socket = FakeGatewaySocket();
    final controller = TaskController(
      api: _HistoryGatewayApi(),
      socket: socket,
    );

    await controller.connect(
      baseUrl: 'http://127.0.0.1:8000',
      username: 'operator',
      password: 'passw0rd',
    );

    expect(controller.tasks.map((task) => task.taskId), ['task-1', 'task-2']);
    expect(controller.pendingTasks.single.taskId, 'task-1');
    expect(controller.selectedTask?.taskId, 'task-1');
  });

  test('socket events update task snapshots and append logs', () async {
    final socket = FakeGatewaySocket();
    final controller = TaskController(api: FakeGatewayApi(), socket: socket);
    await controller.connect(
      baseUrl: 'http://127.0.0.1:8000',
      username: 'operator',
      password: 'passw0rd',
    );

    controller.handleSocketEvent({
      'type': 'TASK_SNAPSHOT',
      'task': {
        'task_id': 'task-1',
        'device_id': 'device-alpha',
        'instruction': '查看系统负载，然后重启容器 api-service',
        'status': 'APPROVED',
        'checkpoint_id': 'cp_001',
        'command': 'docker restart api-service',
        'reason': '重启容器会打断服务，需要人工确认',
        'result': null,
        'error': null,
        'logs': ['load1=0.42'],
      },
    });
    controller.handleSocketEvent({
      'type': 'TASK_LOG',
      'task_id': 'task-1',
      'message': 'container restarted',
    });

    expect(controller.selectedTask?.status, TaskStatus.approved);
    expect(controller.logsFor('task-1'), contains('container restarted'));
  });

  test('socket history sync backfills missed tasks after reconnect', () async {
    final controller = TaskController(
      api: FakeGatewayApi(),
      socket: FakeGatewaySocket(),
    );
    await controller.connect(
      baseUrl: 'http://127.0.0.1:8000',
      username: 'operator',
      password: 'passw0rd',
    );

    controller.handleSocketEvent({
      'type': 'TASK_HISTORY_SYNC',
      'tasks': [
        {
          'task_id': 'task-2',
          'device_id': 'device-alpha',
          'instruction': '查看系统负载',
          'status': 'COMPLETED',
          'checkpoint_id': null,
          'command': null,
          'reason': null,
          'result': 'ok',
          'error': null,
          'logs': ['completed'],
        },
        {
          'task_id': 'task-1',
          'device_id': 'device-alpha',
          'instruction': '查看系统负载，然后重启容器 api-service',
          'status': 'AWAITING_APPROVAL',
          'checkpoint_id': 'cp_001',
          'command': 'docker restart api-service',
          'reason': '重启容器会打断服务，需要人工确认',
          'result': null,
          'error': null,
          'logs': ['load1=0.42'],
        },
      ],
    });

    expect(controller.tasks.map((task) => task.taskId), ['task-2', 'task-1']);
    expect(controller.selectedTask?.taskId, 'task-1');
  });

  test('createTask stores the dispatched task and selects it', () async {
    final controller = TaskController(
      api: FakeGatewayApi(),
      socket: FakeGatewaySocket(),
    );
    await controller.connect(
      baseUrl: 'http://127.0.0.1:8000',
      username: 'operator',
      password: 'passw0rd',
    );

    await controller.createTask(
      deviceId: 'device-alpha',
      instruction: '查看系统负载',
    );

    expect(controller.selectedTask?.taskId, 'task-2');
    expect(controller.selectedTask?.status, TaskStatus.pendingDispatch);
  });

  test('clearSelection returns the app to empty conversation mode', () async {
    final controller = TaskController(
      api: FakeGatewayApi(),
      socket: FakeGatewaySocket(),
    );
    await controller.connect(
      baseUrl: 'http://127.0.0.1:8000',
      username: 'operator',
      password: 'passw0rd',
    );

    controller.clearSelection();

    expect(controller.selectedTask, isNull);
    expect(controller.tasks, isNotEmpty);
  });

  test('deleteTask removes the selected terminal chat from local history', () async {
    final api = _HistoryGatewayApi();
    final controller = TaskController(
      api: api,
      socket: FakeGatewaySocket(),
    );
    await controller.connect(
      baseUrl: 'http://127.0.0.1:8000',
      username: 'operator',
      password: 'passw0rd',
    );

    controller.selectTask('task-2');
    await controller.deleteTask('task-2');

    expect(api.deletedTaskIds, ['task-2']);
    expect(controller.tasks.map((task) => task.taskId), ['task-1']);
    expect(controller.selectedTask?.taskId, 'task-1');
  });

  test(
    'connect saves a session and restore reconnects after restart',
    () async {
      final store = FakeConnectionSessionStore();
      final controller = TaskController(
        api: FakeGatewayApi(),
        socket: FakeGatewaySocket(),
        sessionStore: store,
      );

      await controller.connect(
        baseUrl: 'http://10.0.0.8:8000',
        username: 'root',
        password: 'secret',
      );

      expect(store.session?.baseUrl, 'http://10.0.0.8:8000');
      expect(store.session?.username, 'root');
      expect(store.session?.token, 'jwt-token');

      final restoredSocket = FakeGatewaySocket();
      final restoredController = TaskController(
        api: RestoreGatewayApi(),
        socket: restoredSocket,
        sessionStore: store,
      );

      await restoredController.restoreSavedSession();

      expect(restoredController.status, ConnectionStatus.connected);
      expect(restoredController.token, 'jwt-token');
      expect(restoredController.selectedTask?.taskId, 'task-1');
      expect(restoredSocket.connectedBaseUrl, 'http://10.0.0.8:8000');
      expect(restoredSocket.connectedToken, 'jwt-token');
    },
  );

  test('preferred device selection is preserved across restart', () async {
    final store = FakeConnectionSessionStore();
    final controller = TaskController(
      api: MultiDeviceGatewayApi(),
      socket: FakeGatewaySocket(),
      sessionStore: store,
    );

    await controller.connect(
      baseUrl: 'http://127.0.0.1:8000',
      username: 'operator',
      password: 'passw0rd',
    );
    await controller.savePreferredDeviceId('device-beta');

    final restoredController = TaskController(
      api: MultiDeviceRestoreGatewayApi(),
      socket: FakeGatewaySocket(),
      sessionStore: store,
    );

    await restoredController.restoreSavedSession();

    expect(restoredController.preferredDeviceId, 'device-beta');
  });

  test(
    'restore re-authenticates with saved password when persisted token expired',
    () async {
      final store = FakeConnectionSessionStore(
        session: const ConnectionSession(
          baseUrl: 'http://10.0.0.8:8000',
          username: 'root',
          password: 'secret',
          token: 'expired-token',
        ),
      );
      final api = ExpiringTokenGatewayApi();
      final socket = FakeGatewaySocket();
      final controller = TaskController(
        api: api,
        socket: socket,
        sessionStore: store,
      );

      await controller.restoreSavedSession();

      expect(controller.status, ConnectionStatus.connected);
      expect(controller.token, 'fresh-token');
      expect(socket.connectedBaseUrl, 'http://10.0.0.8:8000');
      expect(socket.connectedToken, 'fresh-token');
      expect(api.lastLoginBaseUrl, 'http://10.0.0.8:8000');
      expect(api.lastLoginUsername, 'root');
      expect(api.lastLoginPassword, 'secret');
      expect(store.session?.token, 'fresh-token');
    },
  );

  test('restore keeps saved token after transient reconnect failure', () async {
    final store = FakeConnectionSessionStore(
      session: const ConnectionSession(
        baseUrl: 'http://10.0.0.8:8000',
        username: 'root',
        token: 'jwt-token',
      ),
    );
    final controller = TaskController(
      api: OfflineGatewayApi(),
      socket: FakeGatewaySocket(),
      sessionStore: store,
    );

    await controller.restoreSavedSession();

    expect(controller.status, ConnectionStatus.failed);
    expect(store.session?.token, 'jwt-token');
    expect(store.session?.baseUrl, 'http://10.0.0.8:8000');
    expect(store.session?.username, 'root');
  });
}

class _HistoryGatewayApi extends FakeGatewayApi {
  @override
  Future<List<TaskRecord>> fetchTasks({
    required String baseUrl,
    required String token,
  }) async {
    return [
      TaskRecord.fromJson({
        'task_id': 'task-1',
        'device_id': 'device-alpha',
        'instruction': '查看系统负载，然后重启容器 api-service',
        'status': 'AWAITING_APPROVAL',
        'checkpoint_id': 'cp_001',
        'command': 'docker restart api-service',
        'reason': '重启容器会打断服务，需要人工确认',
        'result': null,
        'error': null,
        'logs': ['load1=0.42'],
      }),
      TaskRecord.fromJson({
        'task_id': 'task-2',
        'device_id': 'device-alpha',
        'instruction': '查看系统负载',
        'status': 'COMPLETED',
        'checkpoint_id': null,
        'command': null,
        'reason': null,
        'result': 'ok',
        'error': null,
        'logs': ['completed'],
      }),
    ];
  }
}
