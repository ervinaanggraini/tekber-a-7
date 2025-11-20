/// Simple local storage abstraction. Replace with SharedPreferences, Hive, etc.
class LocalStorage {
  final Map<String, String> _store = {};

  Future<void> save(String key, String value) async {
    _store[key] = value;
  }

  Future<String?> read(String key) async {
    return _store[key];
  }
}
