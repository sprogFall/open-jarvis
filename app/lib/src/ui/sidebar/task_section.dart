import 'package:app/src/models/task_record.dart';
import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/components/glass_card.dart';
import 'package:app/src/ui/sidebar/thread_tile.dart';
import 'package:flutter/material.dart';

class TaskSection extends StatelessWidget {
  const TaskSection({
    required this.title,
    required this.body,
    required this.tasks,
    required this.selectedTaskId,
    required this.onSelectTask,
    super.key,
  });

  final String title;
  final String body;
  final List<TaskRecord> tasks;
  final String? selectedTaskId;
  final ValueChanged<String> onSelectTask;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      padding: const EdgeInsets.all(16),
      backgroundColor: JarvisThemeTokens.of(context).surface,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 6),
          Text(body, style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(height: 14),
          ...tasks.map(
            (task) => Padding(
              padding: EdgeInsets.only(bottom: task == tasks.last ? 0 : 10),
              child: ThreadTile(
                task: task,
                selected: selectedTaskId == task.taskId,
                onTap: () => onSelectTask(task.taskId),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
