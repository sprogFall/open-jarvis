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

    expect(find.text('开始一个任务'), findsOneWidget);
  });

  testWidgets('keeps quick prompts out of the empty conversation canvas', (tester) async {
    final controller = await connectController();
    await pumpWidget(
      tester,
      WelcomeView(controller: controller, onQuickPrompt: (_) {}),
    );

    expect(find.text('巡检容器'), findsNothing);
    expect(find.text('恢复挂起任务'), findsNothing);
    expect(find.text('查看网关日志'), findsNothing);
  });

  testWidgets('shows connected message', (tester) async {
    final controller = await connectController();
    await pumpWidget(
      tester,
      WelcomeView(controller: controller, onQuickPrompt: (_) {}),
    );

    expect(
      find.textContaining('选择设备后即可开始任务'),
      findsOneWidget,
    );
  });
}
