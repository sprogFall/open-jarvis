import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

String _read(String path) => File(path).readAsStringSync();

void main() {
  test('app copy stays focused on current actions and results', () {
    final files = <String, String>{
      'composer': _read('lib/src/ui/chat/composer_bar.dart'),
      'statusHero': _read('lib/src/ui/chat/status_hero.dart'),
      'welcome': _read('lib/src/ui/chat/welcome_view.dart'),
      'liveLog': _read('lib/src/ui/chat/live_log_card.dart'),
      'emptyThread': _read('lib/src/ui/sidebar/empty_thread_state.dart'),
      'threadRail': _read('lib/src/ui/sidebar/thread_rail.dart'),
      'setupTray': _read('lib/src/ui/setup_tray.dart'),
      'settings': _read('lib/src/ui/settings_sheet.dart'),
      'workspace': _read('lib/src/ui/workspace_summary.dart'),
      'helpers': _read('lib/src/ui/helpers.dart'),
    };

    const forbiddenSnippets = <String>[
      '后续审批与日志会继续写回这里。',
      '所有状态流转都会在这条线程里持续展开。',
      '连接网关后发出第一条任务，这里会自动形成可恢复的聊天线程。',
      '任务会发送到这里选中的执行端。',
      '任务下发、审批、恢复和实时日志都会留在这条对话里。顶部可展开会话设置。',
      '任务下发、审批恢复和实时日志都会继续沿用这条连接。',
      '对话、审批、恢复和实时日志都收敛在同一条消息流里。',
      '当前线程状态：',
      '客户端 stdout 与恢复信息会不断追加到这里。',
      '执行链路已经启动，新的日志会实时回到当前会话。',
      '客户端正在从检查点恢复，后续过程会继续写回当前线程。',
      '网关返回了未知状态，建议同步任务或检查事件流。',
      '移动端 AI 工作台',
    ];

    for (final entry in files.entries) {
      for (final snippet in forbiddenSnippets) {
        expect(
          entry.value.contains(snippet),
          isFalse,
          reason: '${entry.key} should not contain "$snippet"',
        );
      }
    }

    expect(files['composer'], contains('请先选择设备。'));
    expect(files['statusHero'], contains('执行日志'));
    expect(files['welcome'], contains('选择设备后即可开始任务'));
    expect(files['liveLog'], contains('查看执行输出和处理记录。'));
    expect(files['emptyThread'], contains('连接后开始第一条任务。'));
    expect(files['threadRail'], contains('执行目标'));
    expect(files['setupTray'], contains('选择设备并快速填写常用任务。'));
    expect(files['settings'], contains('查看当前连接并同步任务。'));
    expect(files['workspace'], contains('任务总览'));
    expect(files['helpers'], contains('任务执行中，可继续关注日志和审批。'));
  });
}
