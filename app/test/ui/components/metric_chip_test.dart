import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/components/metric_chip.dart';
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
  group('MetricChip', () {
    testWidgets('renders icon and label text', (tester) async {
      await pumpWidget(
        tester,
        const MetricChip(icon: Icons.memory, label: 'CPU 42%'),
      );

      expect(find.byIcon(Icons.memory), findsOneWidget);
      expect(find.text('CPU 42%'), findsOneWidget);
    });

    testWidgets('uses theme colors from tokens', (tester) async {
      await pumpWidget(
        tester,
        const MetricChip(icon: Icons.speed, label: 'Speed'),
      );

      final tokens = JarvisThemeTokens.light;

      // Verify the icon uses textMuted color
      final icon = tester.widget<Icon>(find.byIcon(Icons.speed));
      expect(icon.color, tokens.textMuted);
      expect(icon.size, 16);

      // Verify the container decoration uses theme colors
      final container = tester.widget<Container>(
        find.descendant(
          of: find.byType(MetricChip),
          matching: find.byType(Container),
        ),
      );
      final decoration = container.decoration as BoxDecoration;
      expect(decoration.color, tokens.shellRaised);

      final border = decoration.border as BoxBorder;
      expect(border.top.color, tokens.border);
    });
  });
}
