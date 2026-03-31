import 'package:app/src/ui/app_theme.dart';
import 'package:flutter/material.dart';

class Backdrop extends StatelessWidget {
  const Backdrop({required this.child, super.key});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    final tokens = JarvisThemeTokens.of(context);
    return DecoratedBox(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [tokens.pageTop, tokens.pageBottom],
        ),
      ),
      child: Stack(
        children: [
          Positioned(
            top: -120,
            right: -80,
            child: IgnorePointer(
              child: _GlowOrb(
                size: 320,
                colors: [
                  tokens.accent.withValues(alpha: 0.18),
                  Colors.transparent,
                ],
              ),
            ),
          ),
          Positioned(
            left: -80,
            bottom: -140,
            child: IgnorePointer(
              child: _GlowOrb(
                size: 300,
                colors: [
                  tokens.accentSecondary.withValues(alpha: 0.16),
                  Colors.transparent,
                ],
              ),
            ),
          ),
          child,
        ],
      ),
    );
  }
}

class _GlowOrb extends StatelessWidget {
  const _GlowOrb({required this.size, required this.colors});

  final double size;
  final List<Color> colors;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: RadialGradient(colors: colors),
      ),
    );
  }
}
