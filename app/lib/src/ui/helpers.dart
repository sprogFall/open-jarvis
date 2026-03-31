import 'package:app/src/models/task_record.dart';
import 'package:app/src/state/task_controller.dart';
import 'package:app/src/ui/app_theme.dart';
import 'package:flutter/material.dart';

Duration motionDuration(BuildContext context) {
  final disableAnimations =
      MediaQuery.maybeOf(context)?.disableAnimations ?? false;
  return disableAnimations ? Duration.zero : const Duration(milliseconds: 220);
}

String connectionStatusLabel(ConnectionStatus status) {
  return switch (status) {
    ConnectionStatus.connected => '已连接',
    ConnectionStatus.connecting => '连接中',
    ConnectionStatus.failed => '异常',
    ConnectionStatus.idle => '未连接',
  };
}

Color connectionStatusColor(
  ConnectionStatus status,
  JarvisThemeTokens tokens,
) {
  return switch (status) {
    ConnectionStatus.connected => tokens.success,
    ConnectionStatus.connecting => tokens.warning,
    ConnectionStatus.failed => tokens.danger,
    ConnectionStatus.idle => tokens.textMuted,
  };
}

String taskHeadline(TaskStatus status) {
  return switch (status) {
    TaskStatus.pendingDispatch => '任务已进入派发队列',
    TaskStatus.running => '任务正在执行',
    TaskStatus.awaitingApproval => '等待你的批准',
    TaskStatus.approved => '审批已通过',
    TaskStatus.rejected => '审批已拒绝',
    TaskStatus.resuming => '任务正在恢复',
    TaskStatus.completed => '执行已完成',
    TaskStatus.failed => '任务执行失败',
    TaskStatus.unknown => '任务状态未知',
  };
}

Color taskStatusColor(TaskStatus status, JarvisThemeTokens tokens) {
  return switch (status) {
    TaskStatus.pendingDispatch => tokens.textMuted,
    TaskStatus.running => tokens.accentSecondary,
    TaskStatus.awaitingApproval => tokens.warning,
    TaskStatus.approved => tokens.success,
    TaskStatus.rejected => tokens.danger,
    TaskStatus.resuming => tokens.accentSecondary,
    TaskStatus.completed => tokens.success,
    TaskStatus.failed => tokens.danger,
    TaskStatus.unknown => tokens.textMuted,
  };
}

IconData taskIcon(TaskStatus status) {
  return switch (status) {
    TaskStatus.pendingDispatch => Icons.schedule_send_rounded,
    TaskStatus.running => Icons.motion_photos_on_rounded,
    TaskStatus.awaitingApproval => Icons.shield_outlined,
    TaskStatus.approved => Icons.check_circle_outline_rounded,
    TaskStatus.rejected => Icons.cancel_outlined,
    TaskStatus.resuming => Icons.restore_rounded,
    TaskStatus.completed => Icons.done_all_rounded,
    TaskStatus.failed => Icons.error_outline_rounded,
    TaskStatus.unknown => Icons.help_outline_rounded,
  };
}

String taskNarrative(TaskRecord task) {
  return switch (task.status) {
    TaskStatus.pendingDispatch => '网关已经接收任务，正在等待客户端拉取并开始执行。',
    TaskStatus.running => '执行链路已经启动，新的日志会实时回到当前会话。',
    TaskStatus.awaitingApproval => 'AI 命中了敏感操作，已经在执行前自动挂起。',
    TaskStatus.approved => '敏感操作已经放行，客户端会从恢复点继续执行。',
    TaskStatus.rejected => '这次敏感操作被拒绝，线程会保留上下文等待新的指令。',
    TaskStatus.resuming => '客户端正在从检查点恢复，后续过程会继续写回当前线程。',
    TaskStatus.completed => '任务已经完成，最终结果和日志都保留在这里。',
    TaskStatus.failed => '任务执行出现错误，建议结合日志继续排查。',
    TaskStatus.unknown => '网关返回了未知状态，建议同步任务或检查事件流。',
  };
}
