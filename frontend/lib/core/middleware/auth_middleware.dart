/// Placeholder auth middleware utilities.
class AuthMiddleware {
  /// Simulate an authentication check. Replace with real logic.
  Future<bool> isAuthenticated() async {

    return Future.value(true);
  }

  /// Guard helper: run [action] only if authenticated.
  Future<T> requireAuth<T>(Future<T> Function() action) async {
    final ok = await isAuthenticated();
    if (!ok) throw Exception('User not authenticated');
    return await action();
  }
}
