import 'package:app/src/models/task_record.dart';
import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/helpers.dart';
import 'package:flutter/material.dart';

class ThreadTile extends StatelessWidget {
  const ThreadTile({
    required this.task,
    required this.selected,
    required this.onTap,
    super.key,
  });

  final TaskRecord task;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final tokens = JarvisThemeTokens.of(context);
    final accent = taskStatusColor(task.status, tokens);
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(18),
        child: AnimatedContainer(
          duration: motionDuration(context),
          curve: Curves.easeOutCubic,
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: selected
                ? accent.withValues(alpha: 0.14)
                : tokens.shellRaised,
            borderRadius: BorderRadius.circular(18),
            border: Border.all(
              color: selected ? accent.withValues(alpha: 0.5) : tokens.border,
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(
                      color: accent,
                      borderRadius: BorderRadius.circular(999),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      task.status.label,
                      style: Theme.of(context)
                          .textTheme
                          .labelLarge
                          ?.copyWith(color: accent),
                    ),
                  ),
                  Text(
                    task.deviceId,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
              const SizedBox(height: 10),
              Text(
                task.instruction,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const SizedBox(height: 8),
              Text(
                task.reason ??
                    task.result ??
                    (task.logs.isNotEmpty ? task.logs.last : '打开查看详情'),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
