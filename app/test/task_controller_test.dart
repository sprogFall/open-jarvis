import 'package:app/src/models/device_record.dart';
import 'package:app/src/models/task_record.dart';
import 'package:app/src/services/gateway_api.dart';
import 'package:app/src/services/gateway_socket.dart';
import 'package:app/src/state/task_controller.dart';
import 'package:flutter_test/flutter_test.dart';

class FakeGatewayApi implements GatewayApi {
  @override
  Future<String> login({
    required String baseUrl,
    required String username,
    required String password,
  }) async {
    return 'jwt-token';
  }

  @override
  Future<List<TaskRecord>> fetchPendingApprovals({
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

void main() {
  test('connect loads pending approvals and selects the first task', () async {
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
}
