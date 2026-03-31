import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/chat/streaming_indicator.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

Future<void> pumpWidget(WidgetTester tester, Widget child) async {
  await tester.pumpWidget(MaterialApp(
    theme: JarvisAppTheme.light(),
    home: Scaffold(body: child),
  ));
  // Use pump instead of pumpAndSettle because StreamingIndicator has a
  // repeating animation that never settles.
  await tester.pump();
}

void main() {
  testWidgets('renders thinking text', (tester) async {
    await pumpWidget(tester, const StreamingIndicator());

    expect(find.text('思考中...'), findsOneWidget);
  });

  testWidgets('renders three animated dots', (tester) async {
    await pumpWidget(tester, const StreamingIndicator());

    // The three dots are Containers with BoxShape.circle inside Opacity widgets
    final opacityWidgets = find.descendant(
      of: find.byType(StreamingIndicator),
      matching: find.byType(Opacity),
    );
    expect(opacityWidgets, findsNWidgets(3));
  });

  testWidgets('is a StatefulWidget with animation', (tester) async {
    await pumpWidget(tester, const StreamingIndicator());

    final state = tester.state(find.byType(StreamingIndicator));
    expect(state, isA<State>());
  });
}
