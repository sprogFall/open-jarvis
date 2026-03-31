import 'package:app/src/models/task_record.dart';
import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/sidebar/task_section.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

Future<void> pumpWidget(WidgetTester tester, Widget child) async {
  await tester.pumpWidget(MaterialApp(
    theme: JarvisAppTheme.light(),
    home: Scaffold(body: child),
  ));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('renders section title and body text', (tester) async {
    await pumpWidget(
      tester,
      TaskSection(
        title: '测试分组',
        body: '这是分组的描述文字',
        tasks: const [],
        selectedTaskId: null,
        onSelectTask: (_) {},
      ),
    );

    expect(find.text('测试分组'), findsOneWidget);
    expect(find.text('这是分组的描述文字'), findsOneWidget);
  });

  testWidgets('renders task tiles', (tester) async {
    final tasks = [
      TaskRecord.fromJson(const {
        'task_id': 'task-1',
        'device_id': 'dev-1',
        'instruction': 'first task instruction',
        'status': 'RUNNING',
        'checkpoint_id': null,
        'command': null,
        'reason': null,
        'result': null,
        'error': null,
        'logs': <String>[],
      }),
      TaskRecord.fromJson(const {
        'task_id': 'task-2',
        'device_id': 'dev-1',
        'instruction': 'second task instruction',
        'status': 'COMPLETED',
        'checkpoint_id': null,
        'command': null,
        'reason': null,
        'result': null,
        'error': null,
        'logs': <String>[],
      }),
    ];

    await pumpWidget(
      tester,
      TaskSection(
        title: '分组',
        body: '描述',
        tasks: tasks,
        selectedTaskId: null,
        onSelectTask: (_) {},
      ),
    );

    expect(find.text('first task instruction'), findsOneWidget);
    expect(find.text('second task instruction'), findsOneWidget);
  });
}
