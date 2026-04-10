import 'package:app/src/ui/app_theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:google_fonts/google_fonts.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  GoogleFonts.config.allowRuntimeFetching = false;

  test('dark theme uses shared iOS-style color and shape tokens', () {
    final theme = JarvisAppTheme.dark();
    final tokens = theme.extension<JarvisThemeTokens>()!;
    final shapes = theme.extension<JarvisShapeTokens>()!;
    final bottomSheetShape =
        theme.bottomSheetTheme.shape! as RoundedRectangleBorder;
    final inputBorder =
        theme.inputDecorationTheme.border! as OutlineInputBorder;

    expect(tokens.pageTop, const Color(0xFF07111F));
    expect(tokens.pageBottom, const Color(0xFF0C1628));
    expect(tokens.accent, const Color(0xFF36D399));
    expect(tokens.accentSecondary, const Color(0xFF60A5FA));
    expect(tokens.warning, const Color(0xFFF5C451));
    expect(tokens.danger, const Color(0xFFFB7185));
    expect(tokens.success, const Color(0xFF34D399));
    expect(tokens.textMuted, const Color(0xFFA3B4D0));

    expect(shapes.radiusSm, 18);
    expect(shapes.radiusMd, 24);
    expect(shapes.radiusLg, 32);
    expect(shapes.radiusXl, 40);
    expect(shapes.radiusXxl, 48);
    expect(
      bottomSheetShape.borderRadius,
      BorderRadius.vertical(top: Radius.circular(shapes.radiusXl)),
    );
    expect(inputBorder.borderRadius, BorderRadius.circular(shapes.radiusMd));
  });
}
