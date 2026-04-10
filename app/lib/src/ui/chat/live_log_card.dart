import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/components/glass_card.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';

class LiveLogCard extends StatefulWidget {
  const LiveLogCard({required this.logs, super.key});

  final List<String> logs;

  @override
  State<LiveLogCard> createState() => _LiveLogCardState();
}

class _LiveLogCardState extends State<LiveLogCard> {
  final _scrollController = ScrollController();

  @override
  void didUpdateWidget(LiveLogCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.logs.length != oldWidget.logs.length) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (_scrollController.hasClients) {
          _scrollController.animateTo(
            _scrollController.position.maxScrollExtent,
            duration: const Duration(milliseconds: 200),
            curve: Curves.easeOut,
          );
        }
      });
    }
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _copyAll() {
    Clipboard.setData(ClipboardData(text: widget.logs.join('\n')));
  }

  @override
  Widget build(BuildContext context) {
    final tokens = JarvisThemeTokens.of(context);
    return GlassCard(
      padding: const EdgeInsets.all(20),
      backgroundColor: tokens.shellRaised,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text('日志流', style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: tokens.surfaceMuted,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Text(
                  '${widget.logs.length} 行',
                  style: Theme.of(context).textTheme.labelMedium,
                ),
              ),
              const Spacer(),
              IconButton(
                onPressed: _copyAll,
                icon: Icon(
                  Icons.copy_rounded,
                  size: 20,
                  color: tokens.textMuted,
                ),
                tooltip: '复制全部日志',
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            '客户端 stdout 与恢复信息会不断追加到这里。',
            style: Theme.of(context).textTheme.bodySmall,
          ),
          const SizedBox(height: 16),
          Container(
            width: double.infinity,
            constraints: const BoxConstraints(maxHeight: 300),
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              color: tokens.terminal,
              borderRadius: BorderRadius.circular(24),
              border: Border.all(color: tokens.terminalBorder),
            ),
            child: SingleChildScrollView(
              controller: _scrollController,
              child: SelectionArea(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    for (var index = 0; index < widget.logs.length; index++)
                      Padding(
                        padding: EdgeInsets.only(
                          bottom: index == widget.logs.length - 1 ? 0 : 8,
                        ),
                        child: Text(
                          widget.logs[index],
                          style: GoogleFonts.spaceMono(
                            fontSize: 13,
                            height: 1.5,
                            color: const Color(0xFFF8FAFC),
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
