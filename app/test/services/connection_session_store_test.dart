import 'package:app/src/models/connection_session.dart';
import 'package:app/src/services/connection_session_store.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  test(
    'shared preferences store persists saved gateway session fields',
    () async {
      const store = SharedPreferencesConnectionSessionStore();
      const session = ConnectionSession(
        baseUrl: 'http://10.0.0.8:8000',
        username: 'root',
        password: 'secret',
        token: 'jwt-token',
        preferredDeviceId: 'device-beta',
      );

      await store.save(session);
      final restored = await store.load();

      expect(restored, isNotNull);
      expect(restored?.baseUrl, 'http://10.0.0.8:8000');
      expect(restored?.username, 'root');
      expect(restored?.password, 'secret');
      expect(restored?.token, 'jwt-token');
      expect(restored?.preferredDeviceId, 'device-beta');
    },
  );
}
