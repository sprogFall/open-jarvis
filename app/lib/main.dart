import 'package:app/src/services/gateway_api.dart';
import 'package:app/src/services/gateway_socket.dart';
import 'package:app/src/state/task_controller.dart';
import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/home_screen.dart';
import 'package:flutter/material.dart';

void main() {
  runApp(const OmniAgentApp());
}

class OmniAgentApp extends StatefulWidget {
  const OmniAgentApp({super.key, this.controller});

  final TaskController? controller;

  @override
  State<OmniAgentApp> createState() => _OmniAgentAppState();
}

class _OmniAgentAppState extends State<OmniAgentApp> {
  late final TaskController _controller =
      widget.controller ??
      TaskController(api: HttpGatewayApi(), socket: ChannelGatewaySocket());

  @override
  void dispose() {
    if (widget.controller == null) {
      _controller.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'OpenJarvis',
      theme: JarvisAppTheme.light(),
      darkTheme: JarvisAppTheme.dark(),
      themeMode: ThemeMode.system,
      home: OpenJarvisHome(controller: _controller),
    );
  }
}
