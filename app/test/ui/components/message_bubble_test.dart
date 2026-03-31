import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/components/message_bubble.dart';
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
  group('MessageBubble', () {
    testWidgets('renders user bubble right-aligned with green tint',
        (tester) async {
      await pumpWidget(
        tester,
        const MessageBubble(
          alignment: Alignment.centerRight,
          tone: BubbleTone.user,
          role: 'You',
          title: 'Restart the service',
          body: 'Please restart api-service now.',
        ),
      );

      expect(find.text('You'), findsOneWidget);
      expect(find.text('Restart the service'), findsOneWidget);
      expect(find.text('Please restart api-service now.'), findsOneWidget);

      // Verify right alignment via Align widget
      final align = tester.widget<Align>(find.byType(Align));
      expect(align.alignment, Alignment.centerRight);
    });

    testWidgets('renders assistant bubble left-aligned', (tester) async {
      await pumpWidget(
        tester,
        const MessageBubble(
          alignment: Alignment.centerLeft,
          tone: BubbleTone.assistant,
          role: 'Jarvis',
          title: 'Task completed',
          body: 'The service has been restarted.',
        ),
      );

      expect(find.text('Jarvis'), findsOneWidget);
      expect(find.text('Task completed'), findsOneWidget);
      expect(find.text('The service has been restarted.'), findsOneWidget);

      final align = tester.widget<Align>(find.byType(Align));
      expect(align.alignment, Alignment.centerLeft);
    });

    testWidgets('renders role label, title, and body text', (tester) async {
      await pumpWidget(
        tester,
        const MessageBubble(
          alignment: Alignment.centerLeft,
          tone: BubbleTone.assistant,
          role: 'Assistant',
          title: 'Summary',
          body: 'All systems nominal.',
        ),
      );

      expect(find.text('Assistant'), findsOneWidget);
      expect(find.text('Summary'), findsOneWidget);
      expect(find.text('All systems nominal.'), findsOneWidget);
    });

    testWidgets('renders optional footer when provided', (tester) async {
      await pumpWidget(
        tester,
        const MessageBubble(
          alignment: Alignment.centerLeft,
          tone: BubbleTone.assistant,
          role: 'Jarvis',
          title: 'Done',
          body: 'Task finished.',
          footer: 'Executed in 2.3s',
        ),
      );

      expect(find.text('Executed in 2.3s'), findsOneWidget);
    });

    testWidgets('does not render footer when null', (tester) async {
      await pumpWidget(
        tester,
        const MessageBubble(
          alignment: Alignment.centerLeft,
          tone: BubbleTone.assistant,
          role: 'Jarvis',
          title: 'Done',
          body: 'Task finished.',
        ),
      );

      // There should be exactly 3 Text widgets: role, title, body
      final textWidgets = find.descendant(
        of: find.byType(MessageBubble),
        matching: find.byType(Text),
      );
      expect(textWidgets, findsNWidgets(3));
    });

    testWidgets('renders timestamp when provided', (tester) async {
      await pumpWidget(
        tester,
        MessageBubble(
          alignment: Alignment.centerLeft,
          tone: BubbleTone.assistant,
          role: 'Jarvis',
          title: 'Done',
          body: 'Task finished.',
          timestamp: DateTime(2025, 3, 15, 14, 30),
        ),
      );

      expect(find.text('14:30'), findsOneWidget);
    });

    testWidgets('does not render timestamp when null', (tester) async {
      await pumpWidget(
        tester,
        const MessageBubble(
          alignment: Alignment.centerLeft,
          tone: BubbleTone.assistant,
          role: 'Jarvis',
          title: 'Done',
          body: 'Task finished.',
        ),
      );

      // No timestamp text should appear
      expect(find.text('14:30'), findsNothing);
    });
  });
}
