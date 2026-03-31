import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/chat/inline_notice_card.dart';
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
  testWidgets('renders title and body text', (tester) async {
    await pumpWidget(
      tester,
      const InlineNoticeCard(
        icon: Icons.info_outline_rounded,
        title: '测试标题',
        body: '测试正文内容',
        accent: Colors.blue,
      ),
    );
    expect(find.text('测试标题'), findsOneWidget);
    expect(find.text('测试正文内容'), findsOneWidget);
  });

  testWidgets('renders icon with accent color', (tester) async {
    await pumpWidget(
      tester,
      const InlineNoticeCard(
        icon: Icons.check_circle_outline_rounded,
        title: '标题',
        body: '正文',
        accent: Colors.green,
      ),
    );
    expect(find.byIcon(Icons.check_circle_outline_rounded), findsOneWidget);
  });
}
