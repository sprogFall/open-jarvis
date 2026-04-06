import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('home screen delegates to the shared app shell and removes private UI forks', () {
    final homeScreen = File('lib/src/ui/home_screen.dart').readAsStringSync();
    final shell = File('lib/src/ui/jarvis_app_shell.dart').readAsStringSync();
    final setupTray = File('lib/src/ui/setup_tray.dart');

    expect(setupTray.existsSync(), isTrue);
    expect(homeScreen.contains('JarvisAppShell'), isTrue);
    expect(homeScreen.contains('class _JarvisAppBar'), isFalse);
    expect(homeScreen.contains('class _SetupTray'), isFalse);
    expect(homeScreen.contains('class _ThreadRail'), isFalse);
    expect(homeScreen.contains('class _GlassCard'), isFalse);
    expect(homeScreen.split('\n').length, lessThan(80));
    expect(shell.contains('SetupTray'), isTrue);
  });
}
