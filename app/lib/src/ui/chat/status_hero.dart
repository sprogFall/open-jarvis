import 'dart:async';

import 'package:app/src/models/task_record.dart';
import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/components/glass_card.dart';
import 'package:app/src/ui/helpers.dart';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class StatusHero extends StatelessWidget {
  const StatusHero({required this.task, this.onDelete, super.key});

  final TaskRecord task;
  final Future<void> Function()? onDelete;

  @override
  Widget build(BuildContext context) {
    final tokens = JarvisThemeTokens.of(context);
    final shapes = JarvisShapeTokens.of(context);
    final accent = taskStatusColor(task.status, tokens);
    return GlassCard(
      padding: const EdgeInsets.all(20),
      backgroundColor: tokens.surface,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: accent.withValues(alpha: 0.16),
              borderRadius: shapes.sm,
            ),
            child: Icon(taskIcon(task.status), color: accent),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  taskHeadline(task.status),
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 6),
                Text(
                  '任务 ${task.taskId} · ${task.status.label}',
                  style: Theme.of(
                    context,
                  ).textTheme.bodySmall?.copyWith(color: accent),
                ),
                if (task.result case final result?) ...[
                  const SizedBox(height: 6),
                  Text(
                    result,
                    style: Theme.of(
                      context,
                    ).textTheme.titleMedium?.copyWith(color: accent),
                  ),
                ],
                const SizedBox(height: 8),
                Text(
                  '所有状态流转都会在这条线程里持续展开。',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
                if (task.logs.isNotEmpty) ...[
                  const SizedBox(height: 14),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: tokens.terminal,
                      borderRadius: shapes.lg,
                      border: Border.all(color: tokens.terminalBorder),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '实时日志',
                          style: Theme.of(context).textTheme.labelLarge
                              ?.copyWith(color: tokens.textPrimary),
                        ),
                        const SizedBox(height: 8),
                        for (final line in task.logs.take(2))
                          Padding(
                            padding: EdgeInsets.only(
                              bottom: line == task.logs.take(2).last ? 0 : 6,
                            ),
                            child: Text(
                              line,
                              style: GoogleFonts.spaceMono(
                                fontSize: 13,
                                height: 1.5,
                                color: tokens.textPrimary,
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),
          if (onDelete != null) ...[
            const SizedBox(width: 12),
            IconButton(
              key: const Key('deleteTaskButton'),
              tooltip: '删除记录',
              onPressed: () => unawaited(onDelete!()),
              icon: Icon(Icons.delete_outline_rounded, color: tokens.danger),
            ),
          ],
        ],
      ),
    );
  }
}
