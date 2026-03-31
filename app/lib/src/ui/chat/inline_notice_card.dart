import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/components/glass_card.dart';
import 'package:flutter/material.dart';

class InlineNoticeCard extends StatelessWidget {
  const InlineNoticeCard({
    required this.icon,
    required this.title,
    required this.body,
    required this.accent,
    super.key,
  });

  final IconData icon;
  final String title;
  final String body;
  final Color accent;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      padding: const EdgeInsets.all(18),
      backgroundColor: JarvisThemeTokens.of(context).surface,
      borderColor: accent.withValues(alpha: 0.24),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: accent.withValues(alpha: 0.16),
              borderRadius: BorderRadius.circular(14),
            ),
            child: Icon(icon, color: accent),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 6),
                Text(body, style: Theme.of(context).textTheme.bodyMedium),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
