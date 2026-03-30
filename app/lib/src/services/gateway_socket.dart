import 'dart:async';
import 'dart:convert';

import 'package:web_socket_channel/web_socket_channel.dart';

abstract class GatewaySocket {
  Future<void> connect({
    required String baseUrl,
    required String token,
    required void Function(Map<String, dynamic> event) onEvent,
  });

  Future<void> disconnect();
}

class ChannelGatewaySocket implements GatewaySocket {
  WebSocketChannel? _channel;
  StreamSubscription<dynamic>? _subscription;

  @override
  Future<void> connect({
    required String baseUrl,
    required String token,
    required void Function(Map<String, dynamic> event) onEvent,
  }) async {
    await disconnect();
    final wsBaseUrl = baseUrl.startsWith('https://')
        ? baseUrl.replaceFirst('https://', 'wss://')
        : baseUrl.replaceFirst('http://', 'ws://');
    final uri = Uri.parse(
      '$wsBaseUrl/ws/app',
    ).replace(queryParameters: {'token': token});
    final channel = WebSocketChannel.connect(uri);
    _channel = channel;
    _subscription = channel.stream.listen((payload) {
      final decoded = jsonDecode(payload as String) as Map<String, dynamic>;
      onEvent(decoded);
    });
  }

  @override
  Future<void> disconnect() async {
    await _subscription?.cancel();
    await _channel?.sink.close();
    _subscription = null;
    _channel = null;
  }
}
