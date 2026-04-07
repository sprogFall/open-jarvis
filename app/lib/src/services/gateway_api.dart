import 'dart:convert';

import 'package:app/src/models/device_record.dart';
import 'package:app/src/models/task_record.dart';
import 'package:http/http.dart' as http;

abstract class GatewayApi {
  Future<String> login({
    required String baseUrl,
    required String username,
    required String password,
  });

  Future<List<TaskRecord>> fetchPendingApprovals({
    required String baseUrl,
    required String token,
  });

  Future<List<TaskRecord>> fetchTasks({
    required String baseUrl,
    required String token,
  });

  Future<List<DeviceRecord>> fetchDevices({
    required String baseUrl,
    required String token,
  });

  Future<TaskRecord> createTask({
    required String baseUrl,
    required String token,
    required String deviceId,
    required String instruction,
  });

  Future<TaskRecord> submitDecision({
    required String baseUrl,
    required String token,
    required String taskId,
    required bool approved,
  });

  Future<void> deleteTask({
    required String baseUrl,
    required String token,
    required String taskId,
  });
}

class HttpGatewayApi implements GatewayApi {
  HttpGatewayApi({http.Client? client}) : _client = client ?? http.Client();

  final http.Client _client;

  @override
  Future<String> login({
    required String baseUrl,
    required String username,
    required String password,
  }) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'username': username, 'password': password}),
    );
    _ensureSuccess(response);
    return (jsonDecode(response.body) as Map<String, dynamic>)['access_token']
        as String;
  }

  @override
  Future<List<TaskRecord>> fetchPendingApprovals({
    required String baseUrl,
    required String token,
  }) async {
    final response = await _client.get(
      Uri.parse('$baseUrl/tasks/pending_approvals'),
      headers: _authHeaders(token),
    );
    _ensureSuccess(response);
    final body = jsonDecode(response.body) as List<dynamic>;
    return body
        .map((item) => TaskRecord.fromJson(item as Map<String, dynamic>))
        .toList(growable: false);
  }

  @override
  Future<List<TaskRecord>> fetchTasks({
    required String baseUrl,
    required String token,
  }) async {
    final response = await _client.get(
      Uri.parse('$baseUrl/tasks'),
      headers: _authHeaders(token),
    );
    _ensureSuccess(response);
    final body = jsonDecode(response.body) as List<dynamic>;
    return body
        .map((item) => TaskRecord.fromJson(item as Map<String, dynamic>))
        .toList(growable: false);
  }

  @override
  Future<List<DeviceRecord>> fetchDevices({
    required String baseUrl,
    required String token,
  }) async {
    final response = await _client.get(
      Uri.parse('$baseUrl/devices'),
      headers: _authHeaders(token),
    );
    _ensureSuccess(response);
    final body = jsonDecode(response.body) as List<dynamic>;
    return body
        .map((item) => DeviceRecord.fromJson(item as Map<String, dynamic>))
        .toList(growable: false);
  }

  @override
  Future<TaskRecord> createTask({
    required String baseUrl,
    required String token,
    required String deviceId,
    required String instruction,
  }) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/tasks'),
      headers: {..._authHeaders(token), 'Content-Type': 'application/json'},
      body: jsonEncode({'device_id': deviceId, 'instruction': instruction}),
    );
    _ensureSuccess(response);
    return TaskRecord.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }

  @override
  Future<TaskRecord> submitDecision({
    required String baseUrl,
    required String token,
    required String taskId,
    required bool approved,
  }) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/tasks/$taskId/decision'),
      headers: {..._authHeaders(token), 'Content-Type': 'application/json'},
      body: jsonEncode({'approved': approved}),
    );
    _ensureSuccess(response);
    return TaskRecord.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }

  @override
  Future<void> deleteTask({
    required String baseUrl,
    required String token,
    required String taskId,
  }) async {
    final response = await _client.delete(
      Uri.parse('$baseUrl/tasks/$taskId'),
      headers: _authHeaders(token),
    );
    _ensureSuccess(response);
  }

  Map<String, String> _authHeaders(String token) {
    return {'Authorization': 'Bearer $token'};
  }

  void _ensureSuccess(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return;
    }
    throw StateError(
      'Gateway request failed: ${response.statusCode} ${response.body}',
    );
  }
}
