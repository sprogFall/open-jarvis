import 'dart:math' as math;

import 'package:flutter/material.dart';

class StreamingIndicator extends StatefulWidget {
  const StreamingIndicator({super.key});

  @override
  State<StreamingIndicator> createState() => _StreamingIndicatorState();
}

class _StreamingIndicatorState extends State<StreamingIndicator>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        for (var i = 0; i < 3; i++)
          Padding(
            padding: EdgeInsets.only(right: i < 2 ? 4 : 8),
            child: AnimatedBuilder(
              animation: _controller,
              builder: (context, child) {
                // Stagger each dot by shifting the phase (100ms = 1/6 of the
                // 600ms cycle). The controller value goes 0 -> 1 linearly.
                final phase = (_controller.value * 3 - i) % 1.0;
                final wave = 0.5 + 0.5 * math.sin(phase * 2 * math.pi);
                final opacity = (0.3 + 0.7 * wave).clamp(0.3, 1.0);
                return Opacity(
                  opacity: opacity,
                  child: child,
                );
              },
              child: Container(
                width: 6,
                height: 6,
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.primary,
                  shape: BoxShape.circle,
                ),
              ),
            ),
          ),
        Text(
          '思考中...',
          style: Theme.of(context).textTheme.bodySmall,
        ),
      ],
    );
  }
}
