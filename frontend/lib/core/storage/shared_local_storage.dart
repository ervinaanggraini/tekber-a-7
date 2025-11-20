import 'package:shared_preferences/shared_preferences.dart';

abstract class ILocalStorage {
  Future<void> save(String key, String value);
  Future<String?> read(String key);
  Future<void> saveBool(String key, bool value);
  Future<bool?> readBool(String key);
}

class SharedLocalStorage implements ILocalStorage {
  final SharedPreferences _prefs;

  SharedLocalStorage(this._prefs);

  @override
  Future<String?> read(String key) async => _prefs.getString(key);

  @override
  Future<void> save(String key, String value) async => await _prefs.setString(key, value);

  @override
  Future<bool?> readBool(String key) async {
    if (!_prefs.containsKey(key)) return null;
    return _prefs.getBool(key);
  }

  @override
  Future<void> saveBool(String key, bool value) async => await _prefs.setBool(key, value);
}
