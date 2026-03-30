import 'package:app/main.dart';
import 'package:app/src/models/device_record.dart';
import 'package:app/src/models/task_record.dart';
import 'package:app/src/services/gateway_api.dart';
import 'package:app/src/services/gateway_socket.dart';
import 'package:app/src/state/task_controller.dart';
import 'package:flutter/material.dart';
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
      'logs': const <String>[],
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
  @override
  Future<void> connect({
    required String baseUrl,
    required String token,
    required void Function(Map<String, dynamic> event) onEvent,
  }) async {}

  @override
  Future<void> disconnect() async {}
}

void main() {
  testWidgets('shows approval workspace for pending tasks', (tester) async {
    tester.view.physicalSize = const Size(1440, 1024);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final controller = TaskController(
      api: FakeGatewayApi(),
      socket: FakeGatewaySocket(),
    );
    await controller.connect(
      baseUrl: 'http://127.0.0.1:8000',
      username: 'operator',
      password: 'passw0rd',
    );

    await tester.pumpWidget(OmniAgentApp(controller: controller));
    await tester.pumpAndSettle();

    expect(find.text('OpenJarvis'), findsAtLeastNWidgets(1));
    expect(find.text('任务指挥台'), findsAtLeastNWidgets(1));
    expect(find.text('待处理审批'), findsAtLeastNWidgets(1));
    expect(find.text('恢复检查点'), findsAtLeastNWidgets(1));
    expect(find.text('docker restart api-service'), findsOneWidget);
    expect(find.text('批准执行'), findsOneWidget);
    expect(find.text('拒绝执行'), findsOneWidget);
    expect(find.text('load1=0.42'), findsAtLeastNWidgets(1));
  });
}
