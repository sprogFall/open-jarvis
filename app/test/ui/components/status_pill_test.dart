import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/components/status_pill.dart';
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
  group('StatusPill', () {
    testWidgets('renders label text', (tester) async {
      await pumpWidget(
        tester,
        const StatusPill(label: 'Active', color: Colors.green),
      );

      expect(find.text('Active'), findsOneWidget);
    });

    testWidgets('applies color to background, border, and text', (tester) async {
      const pillColor = Colors.orange;

      await pumpWidget(
        tester,
        const StatusPill(label: 'Pending', color: pillColor),
      );

      // Verify the Container decoration
      final container = tester.widget<Container>(
        find.descendant(
          of: find.byType(StatusPill),
          matching: find.byType(Container),
        ),
      );
      final decoration = container.decoration as BoxDecoration;

      // Background uses color with alpha 0.16
      expect(
        decoration.color,
        pillColor.withValues(alpha: 0.16),
      );

      // Border uses color with alpha 0.28
      final border = decoration.border as BoxBorder;
      expect(border.top.color, pillColor.withValues(alpha: 0.28));

      // Text uses the pill color
      final text = tester.widget<Text>(find.text('Pending'));
      expect(text.style?.color, pillColor);
    });
  });
}
