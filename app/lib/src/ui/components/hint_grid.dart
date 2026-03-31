import 'package:app/src/ui/components/glass_card.dart';
import 'package:app/src/ui/app_theme.dart';
import 'package:flutter/material.dart';

class HintData {
  const HintData({
    required this.icon,
    required this.title,
    required this.body,
  });

  final IconData icon;
  final String title;
  final String body;
}

class HintGrid extends StatelessWidget {
  const HintGrid({required this.cards, super.key});

  final List<HintData> cards;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final wide = constraints.maxWidth >= 720;
        final itemWidth = wide
            ? (constraints.maxWidth - 20) / 2
            : constraints.maxWidth;
        return Wrap(
          spacing: 12,
          runSpacing: 12,
          children: cards
              .map(
                (card) => SizedBox(
                  width: itemWidth,
                  child: GlassCard(
                    padding: const EdgeInsets.all(18),
                    backgroundColor: JarvisThemeTokens.of(context).surface,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(card.icon),
                        const SizedBox(height: 12),
                        Text(
                          card.title,
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        const SizedBox(height: 8),
                        Text(
                          card.body,
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                    ),
                  ),
                ),
              )
              .toList(growable: false),
        );
      },
    );
  }
}
