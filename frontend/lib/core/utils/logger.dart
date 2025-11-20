/// Very small logger utility. Replace or extend with `logging` package when needed.
class Logger {
  static void d(String message) {
    // Only print debug messages when not in production build.
    const inProduction = bool.fromEnvironment('dart.vm.product');
    if (!inProduction) {
      // ignore: avoid_print
      print('[DEBUG] $message');
    }
  }
}
