import 'dart:convert';

import 'package:app/src/models/connection_session.dart';
import 'package:shared_preferences/shared_preferences.dart';

abstract class ConnectionSessionStore {
  Future<ConnectionSession?> load();

  Future<void> save(ConnectionSession nextSession);
}

class NoopConnectionSessionStore implements ConnectionSessionStore {
  const NoopConnectionSessionStore();

  @override
  Future<ConnectionSession?> load() async => null;

  @override
  Future<void> save(ConnectionSession nextSession) async {}
}

class SharedPreferencesConnectionSessionStore
    implements ConnectionSessionStore {
  const SharedPreferencesConnectionSessionStore();

  static const _sessionKey = 'connection_session';

  @override
  Future<ConnectionSession?> load() async {
    final preferences = await SharedPreferences.getInstance();
    final rawSession = preferences.getString(_sessionKey);
    if (rawSession == null || rawSession.isEmpty) {
      return null;
    }
    try {
      final decoded = jsonDecode(rawSession);
      if (decoded is! Map<String, dynamic>) {
        return null;
      }
      return ConnectionSession.fromJson(decoded);
    } on FormatException {
      return null;
    }
  }

  @override
  Future<void> save(ConnectionSession nextSession) async {
    final preferences = await SharedPreferences.getInstance();
    await preferences.setString(_sessionKey, jsonEncode(nextSession.toJson()));
  }
}
