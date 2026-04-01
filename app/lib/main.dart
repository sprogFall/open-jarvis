import 'package:app/src/services/gateway_api.dart';
import 'package:app/src/services/connection_session_store.dart';
import 'package:app/src/services/gateway_socket.dart';
import 'package:app/src/state/task_controller.dart';
import 'package:app/src/ui/app_theme.dart';
import 'package:app/src/ui/home_screen.dart';
import 'package:flutter/material.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
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
      TaskController(
        api: HttpGatewayApi(),
        socket: ChannelGatewaySocket(),
        sessionStore: const SharedPreferencesConnectionSessionStore(),
      );
  late final Future<void>? _restoreFuture = widget.controller == null
      ? _controller.restoreSavedSession()
      : null;

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
      home: _restoreFuture == null
          ? OpenJarvisHome(controller: _controller)
          : FutureBuilder<void>(
              future: _restoreFuture,
              builder: (context, snapshot) {
                if (snapshot.connectionState != ConnectionState.done) {
                  return const Scaffold(
                    body: Center(child: CircularProgressIndicator.adaptive()),
                  );
                }
                return OpenJarvisHome(controller: _controller);
              },
            ),
    );
  }
}
