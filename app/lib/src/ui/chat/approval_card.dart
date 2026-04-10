import 'package:app/src/models/task_record.dart';
import 'package:app/src/state/task_controller.dart';
import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/components/glass_card.dart';
import 'package:app/src/ui/components/status_pill.dart';
import 'package:app/src/ui/helpers.dart';
import 'package:flutter/material.dart';
import 'package:flutter_highlight/flutter_highlight.dart';
import 'package:flutter_highlight/themes/atom-one-dark.dart';
import 'package:google_fonts/google_fonts.dart';

class ApprovalCard extends StatefulWidget {
  const ApprovalCard({required this.controller, required this.task, super.key});

  final TaskController controller;
  final TaskRecord task;

  @override
  State<ApprovalCard> createState() => _ApprovalCardState();
}

class _ApprovalCardState extends State<ApprovalCard> {
  bool _confirmedApproval = false;

  @override
  Widget build(BuildContext context) {
    final tokens = JarvisThemeTokens.of(context);
    final shapes = JarvisShapeTokens.of(context);
    return GlassCard(
      padding: const EdgeInsets.all(20),
      backgroundColor: tokens.warningSoft,
      borderColor: tokens.warning.withValues(alpha: 0.28),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: tokens.warning.withValues(alpha: 0.16),
                  borderRadius: shapes.sm,
                ),
                child: Icon(Icons.lock_outline_rounded, color: tokens.warning),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '需要审批后继续',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      widget.task.reason ?? '敏感操作已被挂起，等待你的确认。',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
            ],
          ),
          if (widget.task.command case final command?) ...[
            const SizedBox(height: 16),
            SelectableText(
              command,
              style: GoogleFonts.spaceMono(
                fontSize: 13,
                height: 1.5,
                color: tokens.textPrimary,
              ),
            ),
            const SizedBox(height: 12),
            Container(
              decoration: BoxDecoration(
                color: tokens.terminal,
                borderRadius: shapes.lg,
                border: Border.all(color: tokens.terminalBorder),
              ),
              child: ClipRRect(
                borderRadius: shapes.lg,
                child: HighlightView(
                  command,
                  language: 'bash',
                  theme: atomOneDarkTheme,
                  padding: const EdgeInsets.all(18),
                  textStyle: GoogleFonts.spaceMono(fontSize: 13, height: 1.5),
                ),
              ),
            ),
          ],
          if (widget.task.checkpointId case final checkpointId?) ...[
            const SizedBox(height: 12),
            Text(
              '恢复检查点 $checkpointId',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
          if (widget.task.isAwaitingApproval) ...[
            const SizedBox(height: 18),
            Wrap(
              spacing: 12,
              runSpacing: 12,
              children: [
                FilledButton(
                  style: _confirmedApproval
                      ? FilledButton.styleFrom(
                          backgroundColor: tokens.danger,
                          foregroundColor: Colors.white,
                        )
                      : null,
                  onPressed: () {
                    if (_confirmedApproval) {
                      widget.controller.submitDecision(true);
                    } else {
                      setState(() => _confirmedApproval = true);
                    }
                  },
                  child: Text(_confirmedApproval ? '确认批准?' : '批准继续'),
                ),
                OutlinedButton(
                  onPressed: () => widget.controller.submitDecision(false),
                  child: const Text('拒绝执行'),
                ),
              ],
            ),
          ] else ...[
            const SizedBox(height: 18),
            StatusPill(
              label: widget.task.status.label,
              color: taskStatusColor(widget.task.status, tokens),
            ),
          ],
        ],
      ),
    );
  }
}
