import 'package:app/src/models/task_record.dart';
import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/sidebar/thread_tile.dart';
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
  testWidgets('renders task instruction text', (tester) async {
    final task = TaskRecord.fromJson(const {
      'task_id': 'task-1',
      'device_id': 'dev-1',
      'instruction': 'restart the api-service container',
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
      ThreadTile(task: task, selected: false, onTap: () {}),
    );

    expect(find.text('restart the api-service container'), findsOneWidget);
  });

  testWidgets('renders status label', (tester) async {
    final task = TaskRecord.fromJson(const {
      'task_id': 'task-2',
      'device_id': 'dev-1',
      'instruction': 'check logs',
      'status': 'RUNNING',
      'checkpoint_id': null,
      'command': null,
      'reason': null,
      'result': null,
      'error': null,
      'logs': <String>[],
    });

    await pumpWidget(
      tester,
      ThreadTile(task: task, selected: false, onTap: () {}),
    );

    expect(find.text('执行中'), findsOneWidget);
  });

  testWidgets('renders selected state styling', (tester) async {
    final task = TaskRecord.fromJson(const {
      'task_id': 'task-3',
      'device_id': 'dev-1',
      'instruction': 'check logs',
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
      ThreadTile(task: task, selected: true, onTap: () {}),
    );

    // The tile should still render the instruction; the selected flag changes
    // the container decoration colour. Verify the tile is present.
    expect(find.text('check logs'), findsOneWidget);
    expect(find.text('已完成'), findsOneWidget);
  });
}
