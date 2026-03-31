import 'package:app/src/models/task_record.dart';
import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/chat/conversation_viewport.dart';
import 'package:app/src/ui/chat/welcome_view.dart';
import 'package:app/src/ui/chat/task_timeline.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import '../../helpers/test_fakes.dart';

Future<void> pumpWidget(WidgetTester tester, Widget child) async {
  await tester.pumpWidget(MaterialApp(
    theme: JarvisAppTheme.light(),
    home: Scaffold(body: child),
  ));
  // Use pump instead of pumpAndSettle: WelcomeView has a breathing animation
  // and TaskTimeline may contain a StreamingIndicator, both of which repeat
  // forever and prevent pumpAndSettle from completing.
  await tester.pump();
}

void main() {
  testWidgets('shows welcome view when no task selected', (tester) async {
    // Use default connectController with empty pendingApprovals so that
    // selectedTask is null and WelcomeView is displayed.
    final controller = await connectController();
    controller.clearSelection();
    await pumpWidget(
      tester,
      ConversationViewport(
        controller: controller,
        composerController: TextEditingController(),
        onPrefillInstruction: (_) {},
      ),
    );

    expect(find.byType(WelcomeView), findsOneWidget);
    expect(find.text('给 Jarvis 一个目标'), findsOneWidget);
  });

  testWidgets('shows task timeline when task is selected', (tester) async {
    final task = TaskRecord.fromJson(const {
      'task_id': 'task-x',
      'device_id': 'dev-1',
      'instruction': 'check system load',
      'status': 'RUNNING',
      'checkpoint_id': null,
      'command': null,
      'reason': null,
      'result': null,
      'error': null,
      'logs': <String>[],
    });

    final controller = await connectController(
      pendingApprovals: [task],
    );

    await pumpWidget(
      tester,
      ConversationViewport(
        controller: controller,
        composerController: TextEditingController(),
        onPrefillInstruction: (_) {},
      ),
    );

    expect(find.byType(TaskTimeline), findsOneWidget);
  });
}
