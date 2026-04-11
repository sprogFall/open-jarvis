import 'package:app/src/state/task_controller.dart';
import 'package:app/src/ui/app_theme.dart';
import 'package:flutter/material.dart';

class WelcomeView extends StatefulWidget {
  const WelcomeView({
    required this.controller,
    required this.onQuickPrompt,
    super.key,
  });

  final TaskController controller;
  final ValueChanged<String> onQuickPrompt;

  @override
  State<WelcomeView> createState() => _WelcomeViewState();
}

class _WelcomeViewState extends State<WelcomeView>
    with SingleTickerProviderStateMixin {
  late final AnimationController _breathController;

  @override
  void initState() {
    super.initState();
    _breathController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2000),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _breathController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final tokens = JarvisThemeTokens.of(context);
    final shapes = JarvisShapeTokens.of(context);
    final pendingCount = widget.controller.pendingTasks.length;

    return LayoutBuilder(
      builder: (context, constraints) {
        return SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 40),
          child: ConstrainedBox(
            constraints: BoxConstraints(minHeight: constraints.maxHeight - 80),
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 560),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    ScaleTransition(
                      scale: Tween(begin: 0.97, end: 1.03).animate(
                        CurvedAnimation(
                          parent: _breathController,
                          curve: Curves.easeInOut,
                        ),
                      ),
                      child: Container(
                        width: 56,
                        height: 56,
                        decoration: BoxDecoration(
                          color: tokens.accentSoft,
                          borderRadius: shapes.md,
                        ),
                        child: Icon(
                          Icons.chat_bubble_outline_rounded,
                          color: tokens.accent,
                        ),
                      ),
                    ),
                    const SizedBox(height: 24),
                    Text(
                      '开始一个任务',
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.displaySmall,
                    ),
                    const SizedBox(height: 12),
                    Text(
                      widget.controller.status == ConnectionStatus.connected
                          ? '选择设备后即可开始任务，审批与结果会显示在当前会话。'
                          : '先连接网关，再开始任务。',
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.bodyLarge,
                    ),
                    if (pendingCount > 0) ...[
                      const SizedBox(height: 14),
                      Text(
                        '当前还有 $pendingCount 个挂起任务可恢复。',
                        textAlign: TextAlign.center,
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}
