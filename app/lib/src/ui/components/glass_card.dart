import 'package:app/src/ui/app_theme.dart';
import 'package:flutter/material.dart';

class GlassCard extends StatelessWidget {
  const GlassCard({
    required this.child,
    this.padding = const EdgeInsets.all(20),
    this.backgroundColor,
    this.borderColor,
    this.clipBehavior = Clip.none,
    super.key,
  });

  final Widget child;
  final EdgeInsetsGeometry padding;
  final Color? backgroundColor;
  final Color? borderColor;
  final Clip clipBehavior;

  @override
  Widget build(BuildContext context) {
    final tokens = JarvisThemeTokens.of(context);
    final shapes = JarvisShapeTokens.of(context);
    return DecoratedBox(
      decoration: BoxDecoration(
        color: backgroundColor ?? tokens.shell.withValues(alpha: 0.9),
        borderRadius: shapes.lg,
        border: Border.all(color: borderColor ?? tokens.border),
        boxShadow: [
          BoxShadow(
            color: tokens.shadow,
            blurRadius: 32,
            offset: const Offset(0, 20),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: shapes.lg,
        clipBehavior: clipBehavior,
        child: Padding(padding: padding, child: child),
      ),
    );
  }
}
