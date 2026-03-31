import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/chat/welcome_view.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import '../../helpers/test_fakes.dart';

Future<void> pumpWidget(WidgetTester tester, Widget child) async {
  await tester.pumpWidget(MaterialApp(
    theme: JarvisAppTheme.light(),
    home: Scaffold(body: child),
  ));
  // Use pump instead of pumpAndSettle because WelcomeView has a repeating
  // breathing animation that never settles.
  await tester.pump();
}

void main() {
  testWidgets('shows headline', (tester) async {
    final controller = await connectController();
    await pumpWidget(
      tester,
      WelcomeView(controller: controller, onQuickPrompt: (_) {}),
    );

    expect(find.text('给 Jarvis 一个目标'), findsOneWidget);
  });

  testWidgets('shows quick prompt chips', (tester) async {
    final controller = await connectController();
    await pumpWidget(
      tester,
      WelcomeView(controller: controller, onQuickPrompt: (_) {}),
    );

    expect(find.text('巡检容器'), findsOneWidget);
    expect(find.text('恢复挂起任务'), findsOneWidget);
    expect(find.text('查看网关日志'), findsOneWidget);
  });

  testWidgets('shows connected message', (tester) async {
    final controller = await connectController();
    await pumpWidget(
      tester,
      WelcomeView(controller: controller, onQuickPrompt: (_) {}),
    );

    expect(
      find.textContaining('直接输入任务'),
      findsOneWidget,
    );
  });
}
