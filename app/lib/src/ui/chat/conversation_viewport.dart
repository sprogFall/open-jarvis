import 'package:app/src/state/task_controller.dart';
import 'package:app/src/ui/chat/task_timeline.dart';
import 'package:app/src/ui/chat/welcome_view.dart';
import 'package:app/src/ui/components/glass_card.dart';
import 'package:app/src/ui/helpers.dart';
import 'package:flutter/material.dart';

class ConversationViewport extends StatelessWidget {
  const ConversationViewport({
    required this.controller,
    required this.composerController,
    required this.onPrefillInstruction,
    super.key,
  });

  final TaskController controller;
  final TextEditingController composerController;
  final ValueChanged<String> onPrefillInstruction;

  @override
  Widget build(BuildContext context) {
    final child = controller.selectedTask == null
        ? WelcomeView(
            controller: controller,
            onQuickPrompt: onPrefillInstruction,
          )
        : TaskTimeline(controller: controller, task: controller.selectedTask!);

    return GlassCard(
      padding: EdgeInsets.zero,
      clipBehavior: Clip.antiAlias,
      child: AnimatedSwitcher(
        duration: motionDuration(context),
        switchInCurve: Curves.easeOutCubic,
        switchOutCurve: Curves.easeOutCubic,
        child: KeyedSubtree(
          key: ValueKey<String?>(controller.selectedTask?.taskId),
          child: child,
        ),
      ),
    );
  }
}
