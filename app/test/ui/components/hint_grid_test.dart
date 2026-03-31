import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/components/hint_grid.dart';
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
  group('HintGrid', () {
    final cards = [
      const HintData(
        icon: Icons.psychology,
        title: 'Analyze Logs',
        body: 'Scan error logs for anomalies.',
      ),
      const HintData(
        icon: Icons.restart_alt,
        title: 'Restart Service',
        body: 'Gracefully restart the target service.',
      ),
      const HintData(
        icon: Icons.monitor_heart,
        title: 'Health Check',
        body: 'Verify system health metrics.',
      ),
    ];

    testWidgets('renders all card titles and bodies', (tester) async {
      await pumpWidget(
        tester,
        SizedBox(
          width: 800,
          child: HintGrid(cards: cards),
        ),
      );

      // Verify all titles are rendered
      expect(find.text('Analyze Logs'), findsOneWidget);
      expect(find.text('Restart Service'), findsOneWidget);
      expect(find.text('Health Check'), findsOneWidget);

      // Verify all bodies are rendered
      expect(find.text('Scan error logs for anomalies.'), findsOneWidget);
      expect(
        find.text('Gracefully restart the target service.'),
        findsOneWidget,
      );
      expect(find.text('Verify system health metrics.'), findsOneWidget);
    });

    testWidgets('renders icons', (tester) async {
      await pumpWidget(
        tester,
        SizedBox(
          width: 400,
          child: HintGrid(cards: cards),
        ),
      );

      expect(find.byIcon(Icons.psychology), findsOneWidget);
      expect(find.byIcon(Icons.restart_alt), findsOneWidget);
      expect(find.byIcon(Icons.monitor_heart), findsOneWidget);
    });
  });
}
