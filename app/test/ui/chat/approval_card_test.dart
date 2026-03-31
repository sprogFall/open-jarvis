import 'package:app/src/models/task_record.dart';
import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/chat/approval_card.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import '../../helpers/test_fakes.dart';

Future<void> pumpWidget(WidgetTester tester, Widget child) async {
  await tester.pumpWidget(MaterialApp(
    theme: JarvisAppTheme.light(),
    home: Scaffold(body: child),
  ));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('shows approval title and buttons when awaiting approval',
      (tester) async {
    final controller = await connectController();
    final task = TaskRecord.fromJson(const {
      'task_id': 'task-a',
      'device_id': 'dev-1',
      'instruction': 'restart api-service',
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
      ApprovalCard(controller: controller, task: task),
    );

    expect(find.text('需要审批后继续'), findsOneWidget);
    expect(find.text('批准继续'), findsOneWidget);
    expect(find.text('拒绝执行'), findsOneWidget);
  });

  testWidgets('shows command text when present', (tester) async {
    final controller = await connectController();
    final task = TaskRecord.fromJson(const {
      'task_id': 'task-b',
      'device_id': 'dev-1',
      'instruction': 'restart api-service',
      'status': 'AWAITING_APPROVAL',
      'checkpoint_id': null,
      'command': 'docker restart api-service',
      'reason': null,
      'result': null,
      'error': null,
      'logs': <String>[],
    });

    await pumpWidget(
      tester,
      ApprovalCard(controller: controller, task: task),
    );

    // The command appears twice: once as SelectableText and once inside
    // the HighlightView code block.
    expect(find.text('docker restart api-service'), findsWidgets);
  });

  testWidgets('shows checkpoint ID when present', (tester) async {
    final controller = await connectController();
    final task = TaskRecord.fromJson(const {
      'task_id': 'task-c',
      'device_id': 'dev-1',
      'instruction': 'restart api-service',
      'status': 'APPROVED',
      'checkpoint_id': 'cp_42',
      'command': 'docker restart api-service',
      'reason': null,
      'result': null,
      'error': null,
      'logs': <String>[],
    });

    await pumpWidget(
      tester,
      ApprovalCard(controller: controller, task: task),
    );

    expect(find.text('恢复检查点 cp_42'), findsOneWidget);
  });

  testWidgets('shows status pill when not awaiting approval', (tester) async {
    final controller = await connectController();
    final task = TaskRecord.fromJson(const {
      'task_id': 'task-d',
      'device_id': 'dev-1',
      'instruction': 'restart api-service',
      'status': 'APPROVED',
      'checkpoint_id': null,
      'command': null,
      'reason': null,
      'result': null,
      'error': null,
      'logs': <String>[],
    });

    await pumpWidget(
      tester,
      ApprovalCard(controller: controller, task: task),
    );

    // The card should show the status label instead of approve/reject buttons.
    expect(find.text('已批准'), findsOneWidget);
    expect(find.text('批准继续'), findsNothing);
    expect(find.text('拒绝执行'), findsNothing);
  });

  testWidgets('requires two taps to approve: first tap changes button text',
      (tester) async {
    final controller = await connectController();
    final task = TaskRecord.fromJson(const {
      'task_id': 'task-e',
      'device_id': 'dev-1',
      'instruction': 'restart api-service',
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
      ApprovalCard(controller: controller, task: task),
    );

    // Initially shows "批准继续"
    expect(find.text('批准继续'), findsOneWidget);
    expect(find.text('确认批准?'), findsNothing);

    // First tap changes to confirmation state
    await tester.tap(find.text('批准继续'));
    await tester.pumpAndSettle();

    expect(find.text('确认批准?'), findsOneWidget);
    expect(find.text('批准继续'), findsNothing);
  });
}
