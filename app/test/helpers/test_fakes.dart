import 'package:app/main.dart';
import 'package:app/src/models/device_record.dart';
import 'package:app/src/models/task_record.dart';
import 'package:app/src/services/gateway_api.dart';
import 'package:app/src/services/gateway_socket.dart';
import 'package:app/src/state/task_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class FakeGatewayApi implements GatewayApi {
  static TaskRecord _defaultPendingTask() => TaskRecord.fromJson({
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
  });

  FakeGatewayApi({List<TaskRecord>? pendingApprovals})
      : pendingApprovals = pendingApprovals ?? [_defaultPendingTask()];

  final List<TaskRecord> pendingApprovals;
  String? lastInstruction;
  String? lastBaseUrl;
  String? lastUsername;
  String? lastPassword;

  @override
  Future<String> login({
    required String baseUrl,
    required String username,
    required String password,
  }) async {
    lastBaseUrl = baseUrl;
    lastUsername = username;
    lastPassword = password;
    return 'jwt-token';
  }

  @override
  Future<List<TaskRecord>> fetchPendingApprovals({
    required String baseUrl,
    required String token,
  }) async {
    return pendingApprovals;
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
    lastInstruction = instruction;
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

Future<TaskController> connectController({
  List<TaskRecord> pendingApprovals = const <TaskRecord>[],
  FakeGatewayApi? api,
}) async {
  final gatewayApi = api ?? FakeGatewayApi(pendingApprovals: pendingApprovals);
  final controller = TaskController(
    api: gatewayApi,
    socket: FakeGatewaySocket(),
  );
  await controller.connect(
    baseUrl: 'http://127.0.0.1:8000',
    username: 'operator',
    password: 'passw0rd',
  );
  return controller;
}

Future<void> pumpApp(
  WidgetTester tester,
  TaskController controller, {
  Size size = const Size(390, 844),
}) async {
  tester.view.physicalSize = size;
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);

  await tester.pumpWidget(OmniAgentApp(controller: controller));
  // Use pump instead of pumpAndSettle because the app may contain widgets
  // with repeating animations (e.g. WelcomeView breathing, StreamingIndicator).
  await tester.pump();
}
