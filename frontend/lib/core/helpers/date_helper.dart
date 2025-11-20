/// Small date helper utilities.
class DateHelper {
  /// Safe parse (returns null on failure)
  static DateTime? tryParse(String input) {
    try {
      return DateTime.parse(input);
    } catch (_) {
      return null;
    }
  }

  /// Format a [DateTime] to ISO-like yyyy-MM-dd string.
  static String toSimpleDate(DateTime dt) {
    final y = dt.year.toString().padLeft(4, '0');
    final m = dt.month.toString().padLeft(2, '0');
    final d = dt.day.toString().padLeft(2, '0');
    return '$y-$m-$d';
  }
}
