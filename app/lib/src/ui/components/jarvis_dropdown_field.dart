import 'package:app/src/ui/app_theme.dart';
import 'package:flutter/material.dart';

class JarvisDropdownField<T> extends StatelessWidget {
  const JarvisDropdownField({
    super.key,
    required this.items,
    required this.onChanged,
    required this.hintText,
    this.initialValue,
  });

  final T? initialValue;
  final String hintText;
  final List<DropdownMenuItem<T>> items;
  final ValueChanged<T?>? onChanged;

  @override
  Widget build(BuildContext context) {
    final tokens = JarvisThemeTokens.of(context);
    final textStyle =
        Theme.of(
          context,
        ).textTheme.bodyLarge?.copyWith(color: tokens.textPrimary) ??
        TextStyle(color: tokens.textPrimary, fontSize: 16, height: 1.5);

    return DropdownButtonFormField<T>(
      initialValue: initialValue,
      isExpanded: true,
      decoration: InputDecoration(hintText: hintText),
      style: textStyle,
      dropdownColor: tokens.shellRaised,
      iconEnabledColor: tokens.textMuted,
      iconDisabledColor: tokens.textMuted.withValues(alpha: 0.72),
      borderRadius: BorderRadius.circular(24),
      menuMaxHeight: 320,
      items: items,
      onChanged: onChanged,
    );
  }
}
