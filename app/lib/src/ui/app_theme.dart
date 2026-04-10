import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

@immutable
class JarvisThemeTokens extends ThemeExtension<JarvisThemeTokens> {
  const JarvisThemeTokens({
    required this.pageTop,
    required this.pageBottom,
    required this.shell,
    required this.shellRaised,
    required this.surface,
    required this.surfaceMuted,
    required this.border,
    required this.borderStrong,
    required this.textPrimary,
    required this.textMuted,
    required this.accent,
    required this.accentSoft,
    required this.accentSecondary,
    required this.accentSecondarySoft,
    required this.warning,
    required this.warningSoft,
    required this.danger,
    required this.dangerSoft,
    required this.success,
    required this.successSoft,
    required this.userBubble,
    required this.assistantBubble,
    required this.terminal,
    required this.terminalBorder,
    required this.input,
    required this.shadow,
  });

  final Color pageTop;
  final Color pageBottom;
  final Color shell;
  final Color shellRaised;
  final Color surface;
  final Color surfaceMuted;
  final Color border;
  final Color borderStrong;
  final Color textPrimary;
  final Color textMuted;
  final Color accent;
  final Color accentSoft;
  final Color accentSecondary;
  final Color accentSecondarySoft;
  final Color warning;
  final Color warningSoft;
  final Color danger;
  final Color dangerSoft;
  final Color success;
  final Color successSoft;
  final Color userBubble;
  final Color assistantBubble;
  final Color terminal;
  final Color terminalBorder;
  final Color input;
  final Color shadow;

  static JarvisThemeTokens of(BuildContext context) {
    return Theme.of(context).extension<JarvisThemeTokens>()!;
  }

  static const light = JarvisThemeTokens(
    pageTop: Color(0xFFF3F6FA),
    pageBottom: Color(0xFFE9EEF6),
    shell: Color(0xFFFFFFFF),
    shellRaised: Color(0xFFF8FAFD),
    surface: Color(0xFFF2F5FA),
    surfaceMuted: Color(0xFFEAF0F7),
    border: Color(0xFFD7DFEA),
    borderStrong: Color(0xFFC4CEDA),
    textPrimary: Color(0xFF0F172A),
    textMuted: Color(0xFF5B6880),
    accent: Color(0xFF0F9D74),
    accentSoft: Color(0xFFE6F7F0),
    accentSecondary: Color(0xFF2563EB),
    accentSecondarySoft: Color(0xFFE9F0FF),
    warning: Color(0xFFB7791F),
    warningSoft: Color(0xFFFFF4DC),
    danger: Color(0xFFE11D48),
    dangerSoft: Color(0xFFFFE8EF),
    success: Color(0xFF059669),
    successSoft: Color(0xFFE8FAF4),
    userBubble: Color(0xFFEAF9F3),
    assistantBubble: Color(0xFFFFFFFF),
    terminal: Color(0xFF0F172A),
    terminalBorder: Color(0xFF24344E),
    input: Color(0xFFF8FAFC),
    shadow: Color(0x140B1120),
  );

  static const dark = JarvisThemeTokens(
    pageTop: Color(0xFF07111F),
    pageBottom: Color(0xFF0C1628),
    shell: Color(0xFF0F172A),
    shellRaised: Color(0xFF111C31),
    surface: Color(0xFF132035),
    surfaceMuted: Color(0xFF17263D),
    border: Color(0xFF22324A),
    borderStrong: Color(0xFF31435F),
    textPrimary: Color(0xFFF8FAFC),
    textMuted: Color(0xFF93A4BD),
    accent: Color(0xFF36D399),
    accentSoft: Color(0xFF113227),
    accentSecondary: Color(0xFF60A5FA),
    accentSecondarySoft: Color(0xFF12263B),
    warning: Color(0xFFF5C451),
    warningSoft: Color(0xFF3A2B12),
    danger: Color(0xFFFB7185),
    dangerSoft: Color(0xFF3D1820),
    success: Color(0xFF34D399),
    successSoft: Color(0xFF0F2F26),
    userBubble: Color(0xFF113227),
    assistantBubble: Color(0xFF111C31),
    terminal: Color(0xFF08101E),
    terminalBorder: Color(0xFF24344E),
    input: Color(0xFF0B1324),
    shadow: Color(0x40020510),
  );

  @override
  JarvisThemeTokens copyWith({
    Color? pageTop,
    Color? pageBottom,
    Color? shell,
    Color? shellRaised,
    Color? surface,
    Color? surfaceMuted,
    Color? border,
    Color? borderStrong,
    Color? textPrimary,
    Color? textMuted,
    Color? accent,
    Color? accentSoft,
    Color? accentSecondary,
    Color? accentSecondarySoft,
    Color? warning,
    Color? warningSoft,
    Color? danger,
    Color? dangerSoft,
    Color? success,
    Color? successSoft,
    Color? userBubble,
    Color? assistantBubble,
    Color? terminal,
    Color? terminalBorder,
    Color? input,
    Color? shadow,
  }) {
    return JarvisThemeTokens(
      pageTop: pageTop ?? this.pageTop,
      pageBottom: pageBottom ?? this.pageBottom,
      shell: shell ?? this.shell,
      shellRaised: shellRaised ?? this.shellRaised,
      surface: surface ?? this.surface,
      surfaceMuted: surfaceMuted ?? this.surfaceMuted,
      border: border ?? this.border,
      borderStrong: borderStrong ?? this.borderStrong,
      textPrimary: textPrimary ?? this.textPrimary,
      textMuted: textMuted ?? this.textMuted,
      accent: accent ?? this.accent,
      accentSoft: accentSoft ?? this.accentSoft,
      accentSecondary: accentSecondary ?? this.accentSecondary,
      accentSecondarySoft: accentSecondarySoft ?? this.accentSecondarySoft,
      warning: warning ?? this.warning,
      warningSoft: warningSoft ?? this.warningSoft,
      danger: danger ?? this.danger,
      dangerSoft: dangerSoft ?? this.dangerSoft,
      success: success ?? this.success,
      successSoft: successSoft ?? this.successSoft,
      userBubble: userBubble ?? this.userBubble,
      assistantBubble: assistantBubble ?? this.assistantBubble,
      terminal: terminal ?? this.terminal,
      terminalBorder: terminalBorder ?? this.terminalBorder,
      input: input ?? this.input,
      shadow: shadow ?? this.shadow,
    );
  }

  @override
  JarvisThemeTokens lerp(ThemeExtension<JarvisThemeTokens>? other, double t) {
    if (other is! JarvisThemeTokens) {
      return this;
    }
    return JarvisThemeTokens(
      pageTop: Color.lerp(pageTop, other.pageTop, t)!,
      pageBottom: Color.lerp(pageBottom, other.pageBottom, t)!,
      shell: Color.lerp(shell, other.shell, t)!,
      shellRaised: Color.lerp(shellRaised, other.shellRaised, t)!,
      surface: Color.lerp(surface, other.surface, t)!,
      surfaceMuted: Color.lerp(surfaceMuted, other.surfaceMuted, t)!,
      border: Color.lerp(border, other.border, t)!,
      borderStrong: Color.lerp(borderStrong, other.borderStrong, t)!,
      textPrimary: Color.lerp(textPrimary, other.textPrimary, t)!,
      textMuted: Color.lerp(textMuted, other.textMuted, t)!,
      accent: Color.lerp(accent, other.accent, t)!,
      accentSoft: Color.lerp(accentSoft, other.accentSoft, t)!,
      accentSecondary: Color.lerp(accentSecondary, other.accentSecondary, t)!,
      accentSecondarySoft: Color.lerp(
        accentSecondarySoft,
        other.accentSecondarySoft,
        t,
      )!,
      warning: Color.lerp(warning, other.warning, t)!,
      warningSoft: Color.lerp(warningSoft, other.warningSoft, t)!,
      danger: Color.lerp(danger, other.danger, t)!,
      dangerSoft: Color.lerp(dangerSoft, other.dangerSoft, t)!,
      success: Color.lerp(success, other.success, t)!,
      successSoft: Color.lerp(successSoft, other.successSoft, t)!,
      userBubble: Color.lerp(userBubble, other.userBubble, t)!,
      assistantBubble: Color.lerp(assistantBubble, other.assistantBubble, t)!,
      terminal: Color.lerp(terminal, other.terminal, t)!,
      terminalBorder: Color.lerp(terminalBorder, other.terminalBorder, t)!,
      input: Color.lerp(input, other.input, t)!,
      shadow: Color.lerp(shadow, other.shadow, t)!,
    );
  }
}

class JarvisAppTheme {
  static ThemeData light() => _buildTheme(
    brightness: Brightness.light,
    tokens: JarvisThemeTokens.light,
  );

  static ThemeData dark() =>
      _buildTheme(brightness: Brightness.dark, tokens: JarvisThemeTokens.dark);

  static ThemeData _buildTheme({
    required Brightness brightness,
    required JarvisThemeTokens tokens,
  }) {
    final base = ThemeData(
      useMaterial3: true,
      brightness: brightness,
      colorScheme: ColorScheme(
        brightness: brightness,
        primary: tokens.accent,
        onPrimary: Colors.white,
        secondary: tokens.accentSecondary,
        onSecondary: Colors.white,
        error: tokens.danger,
        onError: Colors.white,
        surface: tokens.shell,
        onSurface: tokens.textPrimary,
      ),
    );
    final inter = GoogleFonts.interTextTheme(base.textTheme);
    final textTheme = inter.copyWith(
      displaySmall: GoogleFonts.spaceGrotesk(
        fontSize: 28,
        fontWeight: FontWeight.w700,
        height: 1.1,
        color: tokens.textPrimary,
      ),
      headlineSmall: GoogleFonts.spaceGrotesk(
        fontSize: 24,
        fontWeight: FontWeight.w700,
        height: 1.15,
        color: tokens.textPrimary,
      ),
      titleLarge: GoogleFonts.spaceGrotesk(
        fontSize: 20,
        fontWeight: FontWeight.w700,
        color: tokens.textPrimary,
      ),
      titleMedium: inter.titleMedium?.copyWith(
        fontSize: 16,
        fontWeight: FontWeight.w600,
        color: tokens.textPrimary,
      ),
      bodyLarge: inter.bodyLarge?.copyWith(
        fontSize: 16,
        height: 1.5,
        color: tokens.textPrimary,
      ),
      bodyMedium: inter.bodyMedium?.copyWith(
        fontSize: 14,
        height: 1.45,
        color: tokens.textPrimary,
      ),
      bodySmall: inter.bodySmall?.copyWith(
        fontSize: 12,
        height: 1.4,
        color: tokens.textMuted,
      ),
      labelLarge: inter.labelLarge?.copyWith(
        fontSize: 13,
        fontWeight: FontWeight.w600,
        color: tokens.textPrimary,
      ),
      labelMedium: inter.labelMedium?.copyWith(
        fontSize: 12,
        fontWeight: FontWeight.w500,
        color: tokens.textMuted,
      ),
    );

    return base.copyWith(
      extensions: [tokens],
      scaffoldBackgroundColor: tokens.pageBottom,
      canvasColor: tokens.shellRaised,
      cardColor: tokens.shell,
      shadowColor: tokens.shadow,
      dividerColor: tokens.border,
      textTheme: textTheme,
      iconTheme: IconThemeData(color: tokens.textPrimary),
      appBarTheme: AppBarTheme(
        backgroundColor: tokens.shell.withValues(alpha: 0.92),
        foregroundColor: tokens.textPrimary,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        centerTitle: false,
        titleSpacing: 0,
        toolbarHeight: 72,
      ),
      drawerTheme: DrawerThemeData(
        backgroundColor: tokens.shell.withValues(alpha: 0.98),
        surfaceTintColor: Colors.transparent,
        shape: const RoundedRectangleBorder(),
      ),
      bottomSheetTheme: BottomSheetThemeData(
        backgroundColor: tokens.shellRaised,
        surfaceTintColor: Colors.transparent,
        modalBackgroundColor: tokens.shellRaised,
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(32)),
        ),
      ),
      dividerTheme: DividerThemeData(color: tokens.border, space: 1),
      chipTheme: base.chipTheme.copyWith(
        backgroundColor: tokens.surface,
        selectedColor: tokens.accentSoft,
        side: BorderSide(color: tokens.border),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
        labelStyle: textTheme.labelLarge,
        secondaryLabelStyle: textTheme.labelLarge,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: tokens.input,
        hintStyle: textTheme.bodyMedium?.copyWith(color: tokens.textMuted),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 20,
          vertical: 18,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(24),
          borderSide: BorderSide(color: tokens.border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(24),
          borderSide: BorderSide(color: tokens.border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(24),
          borderSide: BorderSide(color: tokens.accent, width: 1.4),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: tokens.accent,
          foregroundColor: Colors.white,
          disabledBackgroundColor: tokens.surfaceMuted,
          disabledForegroundColor: tokens.textMuted,
          elevation: 0,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 18),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(24),
          ),
          textStyle: textTheme.labelLarge,
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: tokens.textPrimary,
          side: BorderSide(color: tokens.borderStrong),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 18),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(24),
          ),
          textStyle: textTheme.labelLarge,
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: tokens.accentSecondary,
          textStyle: textTheme.labelLarge,
        ),
      ),
    );
  }
}
