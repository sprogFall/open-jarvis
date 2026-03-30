enum TaskStatus {
  pendingDispatch,
  running,
  awaitingApproval,
  approved,
  rejected,
  resuming,
  completed,
  failed,
  unknown;

  factory TaskStatus.fromWire(String value) {
    switch (value) {
      case 'PENDING_DISPATCH':
        return TaskStatus.pendingDispatch;
      case 'RUNNING':
        return TaskStatus.running;
      case 'AWAITING_APPROVAL':
        return TaskStatus.awaitingApproval;
      case 'APPROVED':
        return TaskStatus.approved;
      case 'REJECTED':
        return TaskStatus.rejected;
      case 'RESUMING':
        return TaskStatus.resuming;
      case 'COMPLETED':
        return TaskStatus.completed;
      case 'FAILED':
        return TaskStatus.failed;
      default:
        return TaskStatus.unknown;
    }
  }

  String get label {
    switch (this) {
      case TaskStatus.pendingDispatch:
        return '待派发';
      case TaskStatus.running:
        return '执行中';
      case TaskStatus.awaitingApproval:
        return '待审批';
      case TaskStatus.approved:
        return '已批准';
      case TaskStatus.rejected:
        return '已拒绝';
      case TaskStatus.resuming:
        return '恢复中';
      case TaskStatus.completed:
        return '已完成';
      case TaskStatus.failed:
        return '失败';
      case TaskStatus.unknown:
        return '未知';
    }
  }
}

class TaskRecord {
  const TaskRecord({
    required this.taskId,
    required this.deviceId,
    required this.instruction,
    required this.status,
    required this.logs,
    this.checkpointId,
    this.command,
    this.reason,
    this.result,
    this.error,
  });

  final String taskId;
  final String deviceId;
  final String instruction;
  final TaskStatus status;
  final String? checkpointId;
  final String? command;
  final String? reason;
  final String? result;
  final String? error;
  final List<String> logs;

  bool get isAwaitingApproval => status == TaskStatus.awaitingApproval;

  factory TaskRecord.fromJson(Map<String, dynamic> json) {
    return TaskRecord(
      taskId: json['task_id'] as String,
      deviceId: json['device_id'] as String,
      instruction: json['instruction'] as String,
      status: TaskStatus.fromWire(json['status'] as String? ?? 'UNKNOWN'),
      checkpointId: json['checkpoint_id'] as String?,
      command: json['command'] as String?,
      reason: json['reason'] as String?,
      result: json['result'] as String?,
      error: json['error'] as String?,
      logs: ((json['logs'] as List<dynamic>?) ?? const <dynamic>[])
          .map((item) => item.toString())
          .toList(growable: false),
    );
  }

  TaskRecord copyWith({
    String? taskId,
    String? deviceId,
    String? instruction,
    TaskStatus? status,
    String? checkpointId,
    String? command,
    String? reason,
    String? result,
    String? error,
    List<String>? logs,
  }) {
    return TaskRecord(
      taskId: taskId ?? this.taskId,
      deviceId: deviceId ?? this.deviceId,
      instruction: instruction ?? this.instruction,
      status: status ?? this.status,
      checkpointId: checkpointId ?? this.checkpointId,
      command: command ?? this.command,
      reason: reason ?? this.reason,
      result: result ?? this.result,
      error: error ?? this.error,
      logs: logs ?? this.logs,
    );
  }
}
