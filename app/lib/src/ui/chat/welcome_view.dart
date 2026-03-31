import 'package:app/src/state/task_controller.dart';
import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/components/hint_grid.dart';
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
    final quickPrompts = <(String, String)>[
      ('巡检容器', '检查 docker 容器状态并汇总异常'),
      ('恢复挂起任务', '检查当前所有挂起任务并给出恢复建议'),
      ('查看网关日志', '查看网关最近 100 行日志并标出异常'),
    ];

    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [tokens.shellRaised, tokens.surface],
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              ScaleTransition(
                scale: Tween(begin: 0.95, end: 1.05).animate(
                  CurvedAnimation(
                    parent: _breathController,
                    curve: Curves.easeInOut,
                  ),
                ),
                child: Container(
                  width: 54,
                  height: 54,
                  decoration: BoxDecoration(
                    color: tokens.accentSoft,
                    borderRadius: BorderRadius.circular(18),
                  ),
                  child: Icon(
                    Icons.chat_bubble_outline_rounded,
                    color: tokens.accent,
                  ),
                ),
              ),
              const SizedBox(height: 20),
              Text(
                '给 Jarvis 一个目标',
                style: Theme.of(context).textTheme.displaySmall,
              ),
              const SizedBox(height: 10),
              Text(
                widget.controller.status == ConnectionStatus.connected
                    ? '直接输入任务，系统会把审批、恢复和执行日志全部回收到这条对话。'
                    : '先完成网关连接，之后这里会变成统一的聊天工作区。',
                style: Theme.of(context).textTheme.bodyLarge,
              ),
              const SizedBox(height: 20),
              Wrap(
                spacing: 10,
                runSpacing: 10,
                children: quickPrompts
                    .map(
                      (prompt) => ActionChip(
                        onPressed: () => widget.onQuickPrompt(prompt.$2),
                        avatar: const Icon(Icons.north_east_rounded, size: 16),
                        label: Text(prompt.$1),
                      ),
                    )
                    .toList(growable: false),
              ),
            ],
          ),
        ),
        const SizedBox(height: 18),
        HintGrid(
          cards: const [
            HintData(
              icon: Icons.send_rounded,
              title: '任务下发',
              body: '像聊天一样下发任务，但底层仍然走网关与客户端协议。',
            ),
            HintData(
              icon: Icons.shield_outlined,
              title: '会话内审批',
              body: '敏感操作以审批卡形式插入消息流，不再跳到独立页面。',
            ),
            HintData(
              icon: Icons.terminal_rounded,
              title: '实时日志',
              body: 'stdout、恢复状态和执行结果在同一线程内连续展示。',
            ),
          ],
        ),
      ],
    );
  }
}
