import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/sidebar/empty_thread_state.dart';
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
  testWidgets('shows title text', (tester) async {
    await pumpWidget(tester, const EmptyThreadState());
    expect(find.text('还没有历史线程'), findsOneWidget);
  });

  testWidgets('shows description text', (tester) async {
    await pumpWidget(tester, const EmptyThreadState());
    expect(
      find.text('连接后开始第一条任务。'),
      findsOneWidget,
    );
  });
}
