import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/components/backdrop.dart';
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
  group('Backdrop', () {
    testWidgets('renders child within a gradient background', (tester) async {
      await pumpWidget(
        tester,
        const Backdrop(child: Text('Content')),
      );

      expect(find.text('Content'), findsOneWidget);

      // Verify the outer DecoratedBox has a gradient by checking the Backdrop's
      // first descendant DecoratedBox (which is the gradient container).
      final decoratedBoxes = find.descendant(
        of: find.byType(Backdrop),
        matching: find.byType(DecoratedBox),
      );
      // At least the outer gradient DecoratedBox plus _GlowOrb containers
      expect(decoratedBoxes, findsAtLeast(1));

      // Find the outer one by checking for gradient
      var foundGradient = false;
      for (var i = 0; i < decoratedBoxes.found.length; i++) {
        final box = tester.widget<DecoratedBox>(decoratedBoxes.at(i));
        final decoration = box.decoration as BoxDecoration;
        if (decoration.gradient != null) {
          foundGradient = true;
          expect(decoration.gradient, isA<LinearGradient>());
          break;
        }
      }
      expect(foundGradient, isTrue);
    });

    testWidgets('has a Stack with glow orbs', (tester) async {
      await pumpWidget(
        tester,
        const Backdrop(child: SizedBox.shrink()),
      );

      // Backdrop uses a Stack to layer glow orbs behind the child
      expect(
        find.descendant(
          of: find.byType(Backdrop),
          matching: find.byType(Stack),
        ),
        findsOneWidget,
      );

      // There should be Positioned widgets for glow orbs
      expect(
        find.descendant(
          of: find.byType(Backdrop),
          matching: find.byType(Positioned),
        ),
        findsNWidgets(2),
      );

      // There should be IgnorePointer wrapping each glow orb
      expect(
        find.descendant(
          of: find.byType(Backdrop),
          matching: find.byType(IgnorePointer),
        ),
        findsNWidgets(2),
      );
    });
  });
}
