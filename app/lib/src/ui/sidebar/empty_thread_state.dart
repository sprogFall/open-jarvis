import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/components/glass_card.dart';
import 'package:flutter/material.dart';

class EmptyThreadState extends StatelessWidget {
  const EmptyThreadState({super.key});

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      padding: const EdgeInsets.all(16),
      backgroundColor: JarvisThemeTokens.of(context).surface,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('还没有历史线程', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          Text(
            '连接网关后发出第一条任务，这里会自动形成可恢复的聊天线程。',
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
    );
  }
}
