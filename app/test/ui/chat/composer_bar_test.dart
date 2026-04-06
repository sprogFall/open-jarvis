import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/chat/composer_bar.dart';
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
  testWidgets('shows text field and circular send icon button', (tester) async {
    final controller = await connectController();
    await pumpWidget(
      tester,
      ComposerBar(
        controller: controller,
        selectedDeviceId: 'device-alpha',
        composerController: TextEditingController(),
        onComposerChanged: () {},
        onSend: () async {},
      ),
    );

    expect(find.byKey(const Key('chatComposerField')), findsOneWidget);
    expect(find.byKey(const Key('chatSendButton')), findsOneWidget);
    // Verify the arrow-up icon is rendered inside the send button
    expect(
      find.descendant(
        of: find.byKey(const Key('chatSendButton')),
        matching: find.byIcon(Icons.arrow_upward_rounded),
      ),
      findsOneWidget,
    );
  });

  testWidgets('shows device chip when device is selected', (tester) async {
    final controller = await connectController();
    await pumpWidget(
      tester,
      ComposerBar(
        controller: controller,
        selectedDeviceId: 'device-alpha',
        composerController: TextEditingController(),
        onComposerChanged: () {},
        onSend: () async {},
      ),
    );

    expect(find.textContaining('device-alpha'), findsWidgets);
  });

  testWidgets('shows unavailable message when no device selected',
      (tester) async {
    final controller = await connectController();
    await pumpWidget(
      tester,
      ComposerBar(
        controller: controller,
        selectedDeviceId: null,
        composerController: TextEditingController(),
        onComposerChanged: () {},
        onSend: () async {},
      ),
    );

    expect(find.textContaining('请先在顶部展开会话设置并选择设备'), findsOneWidget);
  });

  testWidgets('send button is 44x44 minimum touch target', (tester) async {
    final controller = await connectController();
    await pumpWidget(
      tester,
      ComposerBar(
        controller: controller,
        selectedDeviceId: 'device-alpha',
        composerController: TextEditingController(),
        onComposerChanged: () {},
        onSend: () async {},
      ),
    );

    final sendButton = tester.renderObject(
      find.byKey(const Key('chatSendButton')),
    );
    final size = sendButton.paintBounds;
    expect(size.width, greaterThanOrEqualTo(44));
    expect(size.height, greaterThanOrEqualTo(44));
  });
}
