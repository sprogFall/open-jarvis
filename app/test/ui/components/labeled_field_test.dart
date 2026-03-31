import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/components/labeled_field.dart';
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
  group('LabeledField', () {
    testWidgets('renders label text', (tester) async {
      await pumpWidget(
        tester,
        const LabeledField(
          label: 'Device Name',
          child: Text('Jarvis-Alpha'),
        ),
      );

      expect(find.text('Device Name'), findsOneWidget);
    });

    testWidgets('renders child widget below label', (tester) async {
      await pumpWidget(
        tester,
        const LabeledField(
          label: 'Status',
          child: Text('Connected'),
        ),
      );

      // Both the label and child should be present
      expect(find.text('Status'), findsOneWidget);
      expect(find.text('Connected'), findsOneWidget);

      // Verify layout: label should appear before child in the column
      final column = tester.widget<Column>(find.byType(Column));
      final children = column.children;

      // First child is the label Text
      expect(children[0], isA<Text>());
      expect((children[0] as Text).data, 'Status');

      // Second child is a SizedBox spacer
      expect(children[1], isA<SizedBox>());

      // Third child is the user-provided child
      expect(children[2], isA<Text>());
      expect((children[2] as Text).data, 'Connected');
    });
  });
}
