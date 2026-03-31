import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('android release manifest declares internet permission', () async {
    final manifest = File('android/app/src/main/AndroidManifest.xml');

    expect(await manifest.exists(), isTrue);
    expect(
      await manifest.readAsString(),
      contains('android.permission.INTERNET'),
    );
  });
}
