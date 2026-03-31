import 'package:app/src/ui/components/glass_card.dart';
import 'package:app/src/ui/app_theme.dart';
import 'package:flutter/material.dart';

enum BubbleTone { user, assistant }

class MessageBubble extends StatelessWidget {
  const MessageBubble({
    required this.alignment,
    required this.tone,
    required this.role,
    required this.title,
    required this.body,
    this.footer,
    this.timestamp,
    super.key,
  });

  final Alignment alignment;
  final BubbleTone tone;
  final String role;
  final String title;
  final String body;
  final String? footer;
  final DateTime? timestamp;

  static String _formatTime(DateTime dt) {
    final hour = dt.hour.toString().padLeft(2, '0');
    final minute = dt.minute.toString().padLeft(2, '0');
    return '$hour:$minute';
  }

  @override
  Widget build(BuildContext context) {
    final tokens = JarvisThemeTokens.of(context);
    final background = switch (tone) {
      BubbleTone.user => tokens.userBubble,
      BubbleTone.assistant => tokens.assistantBubble,
    };
    final border = switch (tone) {
      BubbleTone.user => tokens.accent.withValues(alpha: 0.22),
      BubbleTone.assistant => tokens.border,
    };
    final labelColor = switch (tone) {
      BubbleTone.user => tokens.accent,
      BubbleTone.assistant => tokens.accentSecondary,
    };

    return Align(
      alignment: alignment,
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 640),
        child: GlassCard(
          padding: const EdgeInsets.all(18),
          backgroundColor: background,
          borderColor: border,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                role,
                style: Theme.of(
                  context,
                ).textTheme.labelLarge?.copyWith(color: labelColor),
              ),
              const SizedBox(height: 8),
              Text(title, style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              Text(body, style: Theme.of(context).textTheme.bodyLarge),
              if (timestamp case final ts?) ...[
                const SizedBox(height: 8),
                Text(
                  _formatTime(ts),
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: JarvisThemeTokens.of(context).textMuted,
                  ),
                ),
              ],
              if (footer case final footerText?) ...[
                const SizedBox(height: 10),
                Text(footerText, style: Theme.of(context).textTheme.bodySmall),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
