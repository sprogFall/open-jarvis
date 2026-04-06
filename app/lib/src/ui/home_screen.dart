import 'package:app/src/state/task_controller.dart';
import 'package:app/src/ui/jarvis_app_shell.dart';
import 'package:flutter/material.dart';

class OpenJarvisHome extends StatelessWidget {
  const OpenJarvisHome({super.key, required this.controller});

  final TaskController controller;

  @override
  Widget build(BuildContext context) {
    return JarvisAppShell(controller: controller);
  }
}
