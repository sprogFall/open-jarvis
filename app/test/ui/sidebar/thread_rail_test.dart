import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/sidebar/thread_rail.dart';
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
  testWidgets('shows title', (tester) async {
    final controller = await connectController();
    await pumpWidget(
      tester,
      SizedBox(
        width: 320,
        height: 800,
        child: ThreadRail(
          controller: controller,
          selectedDeviceId: 'device-alpha',
          onDeviceChanged: (_) {},
          onNewChat: () {},
          onSelectTask: (_) {},
        ),
      ),
    );

    expect(find.text('任务线程'), findsOneWidget);
  });

  testWidgets('shows new chat button', (tester) async {
    final controller = await connectController();
    await pumpWidget(
      tester,
      SizedBox(
        width: 320,
        height: 800,
        child: ThreadRail(
          controller: controller,
          selectedDeviceId: 'device-alpha',
          onDeviceChanged: (_) {},
          onNewChat: () {},
          onSelectTask: (_) {},
        ),
      ),
    );

    expect(find.byKey(const Key('drawerNewChatButton')), findsOneWidget);
    expect(find.text('新对话'), findsOneWidget);
  });

  testWidgets('shows device dropdown', (tester) async {
    final controller = await connectController();
    await pumpWidget(
      tester,
      SizedBox(
        width: 320,
        height: 800,
        child: ThreadRail(
          controller: controller,
          selectedDeviceId: 'device-alpha',
          onDeviceChanged: (_) {},
          onNewChat: () {},
          onSelectTask: (_) {},
        ),
      ),
    );

    expect(find.text('当前路由'), findsOneWidget);
    expect(find.byType(DropdownButtonFormField<String>), findsOneWidget);
  });
}
