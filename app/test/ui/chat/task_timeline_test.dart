import 'package:app/src/models/task_record.dart';
import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/chat/task_timeline.dart';
import 'package:app/src/ui/components/message_bubble.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import '../../helpers/test_fakes.dart';

Future<void> pumpWidget(WidgetTester tester, Widget child) async {
  await tester.pumpWidget(MaterialApp(
    theme: JarvisAppTheme.light(),
    home: Scaffold(body: child),
  ));
  // Use pump instead of pumpAndSettle because TaskTimeline may contain a
  // StreamingIndicator with a repeating animation that never settles.
  await tester.pump();
}

void main() {
  testWidgets('renders status hero for a task', (tester) async {
    final controller = await connectController();
    final task = TaskRecord.fromJson(const {
      'task_id': 'task-1',
      'device_id': 'dev-1',
      'instruction': 'check system load',
      'status': 'PENDING_DISPATCH',
      'checkpoint_id': null,
      'command': null,
      'reason': null,
      'result': null,
      'error': null,
      'logs': <String>[],
    });

    await pumpWidget(
      tester,
      SizedBox(
        height: 800,
        child: TaskTimeline(controller: controller, task: task),
      ),
    );

    expect(find.text('任务已进入派发队列'), findsOneWidget);
  });

  testWidgets('renders approval card when task is awaiting approval',
      (tester) async {
    final controller = await connectController();
    final task = TaskRecord.fromJson(const {
      'task_id': 'task-2',
      'device_id': 'dev-1',
      'instruction': 'restart container',
      'status': 'AWAITING_APPROVAL',
      'checkpoint_id': null,
      'command': null,
      'reason': null,
      'result': null,
      'error': null,
      'logs': <String>[],
    });

    await pumpWidget(
      tester,
      SizedBox(
        height: 800,
        child: TaskTimeline(controller: controller, task: task),
      ),
    );

    expect(find.text('需要审批后继续'), findsOneWidget);
  });

  testWidgets('renders user and assistant message bubbles', (tester) async {
    final controller = await connectController();
    final task = TaskRecord.fromJson(const {
      'task_id': 'task-3',
      'device_id': 'dev-1',
      'instruction': 'check docker status',
      'status': 'COMPLETED',
      'checkpoint_id': null,
      'command': null,
      'reason': null,
      'result': null,
      'error': null,
      'logs': <String>[],
    });

    await pumpWidget(
      tester,
      SizedBox(
        height: 800,
        child: TaskTimeline(controller: controller, task: task),
      ),
    );

    expect(find.byType(MessageBubble), findsAtLeast(2));
    expect(find.text('check docker status'), findsOneWidget);
  });
}
