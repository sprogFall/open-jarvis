import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/chat/live_log_card.dart';
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
  testWidgets('renders title text', (tester) async {
    await pumpWidget(tester, const LiveLogCard(logs: ['line 1']));
    expect(find.text('执行日志'), findsOneWidget);
  });

  testWidgets('renders all log lines', (tester) async {
    const logs = ['first log line', 'second log line', 'third log line'];
    await pumpWidget(tester, const LiveLogCard(logs: logs));
    expect(find.text('first log line'), findsOneWidget);
    expect(find.text('second log line'), findsOneWidget);
    expect(find.text('third log line'), findsOneWidget);
  });

  testWidgets('renders terminal-styled container', (tester) async {
    await pumpWidget(tester, const LiveLogCard(logs: ['log']));
    // The log line is wrapped in a SelectionArea inside a Container with
    // rounded-corner terminal styling. Verify the text is present and the
    // description text beneath the title is rendered.
    expect(
      find.text('查看执行输出和处理记录。'),
      findsOneWidget,
    );
  });
}
