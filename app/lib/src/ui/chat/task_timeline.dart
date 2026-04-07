import 'package:app/src/models/task_record.dart';
import 'package:app/src/state/task_controller.dart';
import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/chat/approval_card.dart';
import 'package:app/src/ui/chat/inline_notice_card.dart';
import 'package:app/src/ui/chat/live_log_card.dart';
import 'package:app/src/ui/chat/status_hero.dart';
import 'package:app/src/ui/chat/streaming_indicator.dart';
import 'package:app/src/ui/components/message_bubble.dart';
import 'package:app/src/ui/helpers.dart';
import 'package:flutter/material.dart';

class TaskTimeline extends StatelessWidget {
  const TaskTimeline({
    required this.controller,
    required this.task,
    super.key,
  });

  final TaskController controller;
  final TaskRecord task;

  @override
  Widget build(BuildContext context) {
    final timeline = <Widget>[
      StatusHero(
        task: task,
        onDelete: task.canDeleteHistory
            ? () => controller.deleteTask(task.taskId)
            : null,
      ),
    ];

    if (task.status == TaskStatus.running) {
      timeline.add(const SizedBox(height: 12));
      timeline.add(const StreamingIndicator());
    }

    if (task.command != null ||
        task.reason != null ||
        task.isAwaitingApproval) {
      timeline.add(const SizedBox(height: 16));
      timeline.add(ApprovalCard(controller: controller, task: task));
    }

    if (task.logs.length > 2) {
      timeline.add(const SizedBox(height: 16));
      timeline.add(LiveLogCard(logs: task.logs));
    }

    if (task.result case final result?
        when result.length > 24 || result.contains('\n')) {
      timeline.add(const SizedBox(height: 16));
      timeline.add(
        InlineNoticeCard(
          icon: Icons.check_circle_outline_rounded,
          title: '执行结果',
          body: result,
          accent: JarvisThemeTokens.of(context).success,
        ),
      );
    }

    if (task.error case final error?) {
      timeline.add(const SizedBox(height: 16));
      timeline.add(
        InlineNoticeCard(
          icon: Icons.error_outline_rounded,
          title: '执行错误',
          body: error,
          accent: JarvisThemeTokens.of(context).danger,
        ),
      );
    }

    timeline.addAll([
      const SizedBox(height: 16),
      MessageBubble(
        alignment: Alignment.centerRight,
        tone: BubbleTone.user,
        role: '你',
        title: '任务已发送',
        body: task.instruction,
        footer: '目标设备 ${task.deviceId}',
      ),
      const SizedBox(height: 16),
      MessageBubble(
        alignment: Alignment.centerLeft,
        tone: BubbleTone.assistant,
        role: 'Jarvis',
        title: '任务分析',
        body: taskNarrative(task),
      ),
    ]);

    return Scrollbar(
      child: ListView(padding: const EdgeInsets.all(24), children: timeline),
    );
  }
}
