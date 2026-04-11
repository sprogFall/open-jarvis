import 'dart:io';

import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/components/jarvis_dropdown_field.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

Future<void> pumpDropdown(
  WidgetTester tester, {
  required ThemeData theme,
}) async {
  await tester.pumpWidget(
    MaterialApp(
      theme: theme,
      home: Scaffold(
        body: JarvisDropdownField<String>(
          initialValue: 'device-alpha',
          hintText: '选择设备',
          items: const [
            DropdownMenuItem<String>(
              value: 'device-alpha',
              child: Text('device-alpha · 在线'),
            ),
            DropdownMenuItem<String>(
              value: 'device-beta',
              child: Text('device-beta · 离线'),
            ),
          ],
          onChanged: (_) {},
        ),
      ),
    ),
  );
  await tester.pump();
}

void main() {
  testWidgets('uses readable light-theme dropdown popup colors', (
    tester,
  ) async {
    await pumpDropdown(tester, theme: JarvisAppTheme.light());

    final field = tester.widget<DropdownButton<String>>(
      find.byType(DropdownButton<String>),
    );

    expect(field.dropdownColor, JarvisThemeTokens.light.shellRaised);
    expect(field.style?.color, JarvisThemeTokens.light.textPrimary);
    expect(field.iconEnabledColor, JarvisThemeTokens.light.textMuted);
    expect(field.borderRadius, BorderRadius.circular(28));
    expect(field.menuMaxHeight, 320);
  });

  testWidgets('uses readable dark-theme dropdown popup colors', (tester) async {
    await pumpDropdown(tester, theme: JarvisAppTheme.dark());

    final field = tester.widget<DropdownButton<String>>(
      find.byType(DropdownButton<String>),
    );

    expect(field.dropdownColor, JarvisThemeTokens.dark.shellRaised);
    expect(field.style?.color, JarvisThemeTokens.dark.textPrimary);
    expect(field.iconEnabledColor, JarvisThemeTokens.dark.textMuted);
    expect(field.borderRadius, BorderRadius.circular(28));
    expect(field.menuMaxHeight, 320);
  });

  test('dropdown entrypoints use the shared field', () {
    final threadRail = File(
      'lib/src/ui/sidebar/thread_rail.dart',
    ).readAsStringSync();
    final setupTray = File('lib/src/ui/setup_tray.dart').readAsStringSync();

    expect(threadRail.contains('JarvisDropdownField<String>'), isTrue);
    expect(setupTray.contains('JarvisDropdownField<String>'), isTrue);
    expect(threadRail.contains('DropdownButtonFormField<String>'), isFalse);
    expect(setupTray.contains('DropdownButtonFormField<String>'), isFalse);
  });
}
