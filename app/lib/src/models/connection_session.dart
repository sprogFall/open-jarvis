class ConnectionSession {
  const ConnectionSession({
    required this.baseUrl,
    required this.username,
    this.token,
    this.preferredDeviceId,
  });

  final String baseUrl;
  final String username;
  final String? token;
  final String? preferredDeviceId;

  ConnectionSession copyWith({
    String? baseUrl,
    String? username,
    String? token,
    bool clearToken = false,
    String? preferredDeviceId,
    bool clearPreferredDeviceId = false,
  }) {
    return ConnectionSession(
      baseUrl: baseUrl ?? this.baseUrl,
      username: username ?? this.username,
      token: clearToken ? null : (token ?? this.token),
      preferredDeviceId: clearPreferredDeviceId
          ? null
          : (preferredDeviceId ?? this.preferredDeviceId),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'base_url': baseUrl,
      'username': username,
      'token': token,
      'preferred_device_id': preferredDeviceId,
    };
  }

  factory ConnectionSession.fromJson(Map<String, dynamic> json) {
    return ConnectionSession(
      baseUrl: json['base_url'] as String,
      username: json['username'] as String,
      token: json['token'] as String?,
      preferredDeviceId: json['preferred_device_id'] as String?,
    );
  }
}
