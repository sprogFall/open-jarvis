import 'package:app/main.dart';
import 'package:app/src/models/connection_session.dart';
import 'package:app/src/models/device_record.dart';
import 'package:app/src/models/task_record.dart';
import 'package:app/src/services/connection_session_store.dart';
import 'package:app/src/services/gateway_api.dart';
import 'package:app/src/services/gateway_socket.dart';
import 'package:app/src/state/task_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class FakeGatewayApi implements GatewayApi {
  FakeGatewayApi({this.pendingApprovals = const <TaskRecord>[]});

  final List<TaskRecord> pendingApprovals;
  int loginCallCount = 0;
  int fetchDevicesCallCount = 0;
  int fetchPendingApprovalsCallCount = 0;
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
    loginCallCount += 1;
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
    fetchPendingApprovalsCallCount += 1;
    return pendingApprovals;
  }

  @override
  Future<List<DeviceRecord>> fetchDevices({
    required String baseUrl,
    required String token,
  }) async {
    fetchDevicesCallCount += 1;
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

/// Pump enough frames for navigation and bottom sheet animations to finish,
/// without relying on pumpAndSettle (which hangs on repeating animations).
Future<void> pumpFrames(WidgetTester tester, [int frames = 40]) async {
  for (var i = 0; i < frames; i++) {
    await tester.pump(const Duration(milliseconds: 16));
  }
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
  // Use pump instead of pumpAndSettle because the app contains widgets
  // with repeating animations (e.g. WelcomeView breathing, StreamingIndicator).
  await tester.pump();
}

void main() {
  setUp(() {
    TestWidgetsFlutterBinding.ensureInitialized();
  });

  testWidgets('renders a clean chat-first shell and toggles the setup tray', (
    tester,
  ) async {
    final api = FakeGatewayApi(pendingApprovals: []);
    final controller = await connectController(api: api);

    await pumpApp(tester, controller);

    expect(find.byKey(const Key('appBarMenuButton')), findsOneWidget);
    expect(find.byKey(const Key('appBarSettingsButton')), findsOneWidget);
    expect(find.text('开始一个任务'), findsOneWidget);
    expect(find.text('移动端 AI 工作台'), findsNothing);
    expect(find.text('给 Jarvis 一个目标'), findsNothing);
    expect(find.byKey(const Key('setupToggleButton')), findsOneWidget);
    expect(find.byKey(const Key('setupPanelBody')), findsNothing);
    expect(find.byKey(const Key('setupDeviceField')), findsNothing);
    expect(find.text('恢复挂起任务'), findsNothing);
    expect(find.byKey(const Key('chatComposerField')), findsOneWidget);
    expect(find.byKey(const Key('chatSendButton')), findsOneWidget);

    await tester.tap(find.byKey(const Key('setupToggleButton')));
    await pumpFrames(tester);

    expect(find.byKey(const Key('setupPanelBody')), findsOneWidget);
    expect(find.byKey(const Key('setupDeviceField')), findsOneWidget);
    expect(find.text('巡检容器'), findsOneWidget);
    expect(find.text('恢复挂起任务'), findsOneWidget);
    expect(find.text('查看网关日志'), findsOneWidget);

    await tester.enterText(
      find.byKey(const Key('chatComposerField')),
      '查看系统负载',
    );
    await tester.tap(find.byKey(const Key('chatSendButton')));
    await pumpFrames(tester);

    expect(api.lastInstruction, '查看系统负载');
    expect(find.text('查看系统负载'), findsAtLeastNWidgets(1));
  });

  testWidgets('shows approval and live log cards inside the conversation', (
    tester,
  ) async {
    final controller = await connectController(
      pendingApprovals: [
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
      ],
    );

    await pumpApp(tester, controller);
    await pumpFrames(tester);

    expect(find.text('需要审批后继续'), findsOneWidget);
    expect(find.text('docker restart api-service'), findsOneWidget);
    expect(find.textContaining('恢复检查点 cp_001'), findsOneWidget);
    expect(find.text('实时日志'), findsOneWidget);
    expect(find.text('load1=0.42'), findsOneWidget);
    expect(find.text('批准继续'), findsOneWidget);
    expect(find.text('拒绝执行'), findsOneWidget);
  });

  testWidgets(
    'opens the thread drawer, switches sessions, and starts a new chat',
    (tester) async {
      final controller = await connectController(
        pendingApprovals: [
          TaskRecord.fromJson({
            'task_id': 'task-1',
            'device_id': 'device-alpha',
            'instruction': '重启 api-service',
            'status': 'AWAITING_APPROVAL',
            'checkpoint_id': 'cp_001',
            'command': 'docker restart api-service',
            'reason': '会影响现有服务',
            'result': null,
            'error': null,
            'logs': ['pending approval'],
          }),
        ],
      );
      controller.handleSocketEvent({
        'type': 'TASK_SNAPSHOT',
        'task': {
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
      });

      await pumpApp(tester, controller);

      await tester.tap(find.byKey(const Key('appBarMenuButton')));
      await pumpFrames(tester);

      expect(find.byKey(const Key('threadDrawer')), findsOneWidget);
      expect(find.text('待处理线程'), findsOneWidget);
      expect(find.text('最近会话'), findsOneWidget);
      expect(find.byKey(const Key('drawerNewChatButton')), findsOneWidget);

      await tester.tap(find.text('查看系统负载').last);
      await pumpFrames(tester);

      expect(find.text('执行已完成'), findsOneWidget);
      expect(find.text('ok'), findsOneWidget);
      expect(find.text('completed'), findsOneWidget);

      await tester.tap(find.byKey(const Key('appBarMenuButton')));
      await pumpFrames(tester);
      await tester.tap(find.byKey(const Key('drawerNewChatButton')));
      await pumpFrames(tester);

      expect(find.text('开始一个任务'), findsOneWidget);
    },
  );

  testWidgets(
    'opens the settings sheet from the app bar and saves gateway config',
    (tester) async {
      final api = FakeGatewayApi();
      final controller = TaskController(api: api, socket: FakeGatewaySocket());

      await pumpApp(tester, controller);

      await tester.tap(find.byKey(const Key('appBarSettingsButton')));
      await pumpFrames(tester);

      expect(find.text('连接设置'), findsOneWidget);
      expect(find.byKey(const Key('settingsBaseUrlField')), findsOneWidget);
      expect(find.byKey(const Key('settingsConnectButton')), findsOneWidget);

      await tester.enterText(
        find.byKey(const Key('settingsBaseUrlField')),
        'http://10.0.0.8:8000',
      );
      await tester.enterText(
        find.byKey(const Key('settingsUsernameField')),
        'root',
      );
      await tester.enterText(
        find.byKey(const Key('settingsPasswordField')),
        'secret',
      );
      await tester.tap(find.byKey(const Key('settingsConnectButton')));
      await pumpFrames(tester);

      expect(api.lastBaseUrl, 'http://10.0.0.8:8000');
      expect(api.lastUsername, 'root');
      expect(api.lastPassword, 'secret');
    },
  );

  testWidgets(
    'shows saved server and account info before entering the edit form',
    (tester) async {
      final controller = TaskController(
        api: FakeGatewayApi(),
        socket: FakeGatewaySocket(),
        sessionStore: FakeConnectionSessionStore(
          session: const ConnectionSession(
            baseUrl: 'http://10.0.0.8:8000',
            username: 'root',
            password: 'secret',
            token: 'jwt-token',
          ),
        ),
      );

      await controller.restoreSavedSession();
      await pumpApp(tester, controller);

      await tester.tap(find.byKey(const Key('appBarSettingsButton')));
      await pumpFrames(tester);

      expect(find.text('当前连接'), findsOneWidget);
      expect(find.text('http://10.0.0.8:8000'), findsOneWidget);
      expect(find.text('root'), findsOneWidget);
      expect(find.byKey(const Key('settingsReconnectButton')), findsOneWidget);
      expect(
        find.byKey(const Key('settingsEditConnectionButton')),
        findsOneWidget,
      );
      expect(find.byKey(const Key('settingsBaseUrlField')), findsNothing);

      await tester.tap(find.byKey(const Key('settingsEditConnectionButton')));
      await pumpFrames(tester);

      expect(find.byKey(const Key('settingsBaseUrlField')), findsOneWidget);
      expect(find.byKey(const Key('settingsUsernameField')), findsOneWidget);
      expect(find.byKey(const Key('settingsPasswordField')), findsOneWidget);
    },
  );

  testWidgets('reconnects from the saved connection summary', (tester) async {
    final api = FakeGatewayApi();
    final controller = TaskController(
      api: api,
      socket: FakeGatewaySocket(),
      sessionStore: FakeConnectionSessionStore(
        session: const ConnectionSession(
          baseUrl: 'http://10.0.0.8:8000',
          username: 'root',
          password: 'secret',
          token: 'jwt-token',
        ),
      ),
    );

    await controller.restoreSavedSession();
    expect(api.fetchDevicesCallCount, 1);
    expect(api.fetchPendingApprovalsCallCount, 1);

    await pumpApp(tester, controller);

    await tester.tap(find.byKey(const Key('appBarSettingsButton')));
    await pumpFrames(tester);
    await tester.tap(find.byKey(const Key('settingsReconnectButton')));
    await pumpFrames(tester);

    expect(api.fetchDevicesCallCount, 2);
    expect(api.fetchPendingApprovalsCallCount, 2);
    expect(controller.status, ConnectionStatus.connected);
  });

  testWidgets('restores saved connection settings after app restart', (
    tester,
  ) async {
    final controller = TaskController(
      api: FakeGatewayApi(),
      socket: FakeGatewaySocket(),
      sessionStore: FakeConnectionSessionStore(
        session: const ConnectionSession(
          baseUrl: 'http://10.0.0.8:8000',
          username: 'root',
          token: 'jwt-token',
        ),
      ),
    );

    await controller.restoreSavedSession();
    await pumpApp(tester, controller);

    await tester.tap(find.byKey(const Key('appBarSettingsButton')));
    await pumpFrames(tester);

    expect(find.text('http://10.0.0.8:8000'), findsOneWidget);
    expect(find.text('root'), findsOneWidget);
    expect(find.text('已连接'), findsWidgets);
  });

  testWidgets(
    'keeps a single chat canvas on wide layouts and opens the drawer on demand',
    (tester) async {
      final controller = await connectController();

      await pumpApp(tester, controller, size: const Size(1440, 1024));

      expect(find.byKey(const Key('desktopThreadRail')), findsNothing);
      expect(find.byKey(const Key('appBarMenuButton')), findsOneWidget);

      await tester.tap(find.byKey(const Key('appBarMenuButton')));
      await pumpFrames(tester);

      expect(find.byKey(const Key('threadDrawer')), findsOneWidget);
    },
  );
}
