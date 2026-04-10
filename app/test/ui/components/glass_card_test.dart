import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/components/glass_card.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

Future<void> pumpWidget(WidgetTester tester, Widget child) async {
  await tester.pumpWidget(
    MaterialApp(
      theme: JarvisAppTheme.light(),
      home: Scaffold(body: child),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  group('GlassCard', () {
    testWidgets('renders child text', (tester) async {
      await pumpWidget(tester, const GlassCard(child: Text('Hello Card')));

      expect(find.text('Hello Card'), findsOneWidget);
    });

    testWidgets('accepts custom backgroundColor', (tester) async {
      const customColor = Colors.red;

      await pumpWidget(
        tester,
        const GlassCard(backgroundColor: customColor, child: Text('Colored')),
      );

      final decoratedBox = tester.widget<DecoratedBox>(
        find.descendant(
          of: find.byType(GlassCard),
          matching: find.byType(DecoratedBox),
        ),
      );
      final decoration = decoratedBox.decoration as BoxDecoration;
      expect(decoration.color, customColor);
    });

    testWidgets('accepts custom borderColor', (tester) async {
      const customBorder = Colors.blue;

      await pumpWidget(
        tester,
        const GlassCard(borderColor: customBorder, child: Text('Bordered')),
      );

      final decoratedBox = tester.widget<DecoratedBox>(
        find.descendant(
          of: find.byType(GlassCard),
          matching: find.byType(DecoratedBox),
        ),
      );
      final decoration = decoratedBox.decoration as BoxDecoration;
      expect(decoration.border, isA<Border>());
      final border = decoration.border as Border;
      expect(border.top.color, customBorder);
    });

    testWidgets('has rounded corners with 32px radius', (tester) async {
      await pumpWidget(tester, const GlassCard(child: SizedBox.shrink()));

      final decoratedBox = tester.widget<DecoratedBox>(
        find.descendant(
          of: find.byType(GlassCard),
          matching: find.byType(DecoratedBox),
        ),
      );
      final decoration = decoratedBox.decoration as BoxDecoration;
      expect(decoration.borderRadius, BorderRadius.circular(32));
    });
  });
}
