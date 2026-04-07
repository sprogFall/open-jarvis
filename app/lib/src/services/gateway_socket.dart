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
  static const _heartbeatInterval = Duration(seconds: 15);

  WebSocketChannel? _channel;
  StreamSubscription<dynamic>? _subscription;
  Timer? _heartbeatTimer;
  Timer? _reconnectTimer;
  String? _baseUrl;
  String? _token;
  void Function(Map<String, dynamic> event)? _onEvent;
  bool _shouldReconnect = false;
  int _reconnectAttempt = 0;

  @override
  Future<void> connect({
    required String baseUrl,
    required String token,
    required void Function(Map<String, dynamic> event) onEvent,
  }) async {
    await disconnect();
    _baseUrl = baseUrl;
    _token = token;
    _onEvent = onEvent;
    _shouldReconnect = true;
    await _openChannel(initialAttempt: true);
  }

  @override
  Future<void> disconnect() async {
    _shouldReconnect = false;
    _heartbeatTimer?.cancel();
    _heartbeatTimer = null;
    _reconnectTimer?.cancel();
    _reconnectTimer = null;
    await _subscription?.cancel();
    await _channel?.sink.close();
    _subscription = null;
    _channel = null;
    _baseUrl = null;
    _token = null;
    _onEvent = null;
    _reconnectAttempt = 0;
  }

  Future<void> _openChannel({bool initialAttempt = false}) async {
    final baseUrl = _baseUrl;
    final token = _token;
    final onEvent = _onEvent;
    if (!_shouldReconnect || baseUrl == null || token == null || onEvent == null) {
      return;
    }
    final wsBaseUrl = baseUrl.startsWith('https://')
        ? baseUrl.replaceFirst('https://', 'wss://')
        : baseUrl.replaceFirst('http://', 'ws://');
    final uri = Uri.parse(
      '$wsBaseUrl/ws/app',
    ).replace(queryParameters: {'token': token});
    final channel = WebSocketChannel.connect(uri);
    _channel = channel;
    _subscription = channel.stream.listen(
      (payload) {
        final decoded = jsonDecode(payload as String) as Map<String, dynamic>;
        onEvent(decoded);
      },
      onDone: _handleDisconnect,
      onError: (_, __) => _handleDisconnect(),
      cancelOnError: true,
    );
    try {
      await channel.ready;
      _reconnectAttempt = 0;
      _startHeartbeat();
    } catch (error) {
      await _subscription?.cancel();
      _subscription = null;
      _channel = null;
      if (initialAttempt) {
        rethrow;
      }
      _scheduleReconnect();
    }
  }

  void _startHeartbeat() {
    _heartbeatTimer?.cancel();
    _heartbeatTimer = Timer.periodic(_heartbeatInterval, (_) {
      try {
        _channel?.sink.add('ping');
      } catch (_) {
        _handleDisconnect();
      }
    });
  }

  void _handleDisconnect() {
    final subscription = _subscription;
    final channel = _channel;
    _heartbeatTimer?.cancel();
    _heartbeatTimer = null;
    _subscription = null;
    _channel = null;
    if (subscription != null) {
      unawaited(subscription.cancel());
    }
    if (channel != null) {
      unawaited(channel.sink.close());
    }
    _scheduleReconnect();
  }

  void _scheduleReconnect() {
    if (!_shouldReconnect || _reconnectTimer != null) {
      return;
    }
    final delaySeconds = _reconnectAttempt >= 2 ? 3 : _reconnectAttempt + 1;
    _reconnectAttempt += 1;
    _reconnectTimer = Timer(Duration(seconds: delaySeconds), () {
      _reconnectTimer = null;
      unawaited(_openChannel());
    });
  }
}
