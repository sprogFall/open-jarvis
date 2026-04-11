import 'package:app/src/models/task_record.dart';
import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/chat/status_hero.dart';
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
  testWidgets('renders task status headline and label', (tester) async {
    final task = TaskRecord.fromJson(const {
      'task_id': 'task-1',
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

    await pumpWidget(tester, StatusHero(task: task));

    expect(find.text('任务正在执行'), findsOneWidget);
    expect(find.textContaining('task-1'), findsOneWidget);
    expect(find.textContaining('执行中'), findsOneWidget);
  });

  testWidgets('shows result when present', (tester) async {
    final task = TaskRecord.fromJson(const {
      'task_id': 'task-2',
      'device_id': 'dev-1',
      'instruction': 'check system load',
      'status': 'COMPLETED',
      'checkpoint_id': null,
      'command': null,
      'reason': null,
      'result': 'All services healthy',
      'error': null,
      'logs': <String>[],
    });

    await pumpWidget(tester, StatusHero(task: task));

    expect(find.text('All services healthy'), findsOneWidget);
  });

  testWidgets('shows log preview when logs exist', (tester) async {
    final task = TaskRecord.fromJson(const {
      'task_id': 'task-3',
      'device_id': 'dev-1',
      'instruction': 'check system load',
      'status': 'RUNNING',
      'checkpoint_id': null,
      'command': null,
      'reason': null,
      'result': null,
      'error': null,
      'logs': ['log line 1', 'log line 2', 'log line 3'],
    });

    await pumpWidget(tester, StatusHero(task: task));

    expect(find.text('执行日志'), findsOneWidget);
    // StatusHero shows only the first 2 log lines.
    expect(find.text('log line 1'), findsOneWidget);
    expect(find.text('log line 2'), findsOneWidget);
  });
}
