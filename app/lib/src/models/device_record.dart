class DeviceRecord {
  const DeviceRecord({required this.deviceId, required this.connected});

  final String deviceId;
  final bool connected;

  factory DeviceRecord.fromJson(Map<String, dynamic> json) {
    return DeviceRecord(
      deviceId: json['device_id'] as String,
      connected: json['connected'] as bool? ?? false,
    );
  }
}
