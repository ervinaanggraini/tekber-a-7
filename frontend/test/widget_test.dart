// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/main.dart';
import 'package:frontend/core/storage/shared_local_storage.dart';

class _FakeLocalStorage implements ILocalStorage {
  final Map<String, Object> _m = {};

  @override
  Future<void> save(String key, String value) async => _m[key] = value;

  @override
  Future<String?> read(String key) async => _m[key] as String?;

  @override
  Future<bool?> readBool(String key) async => _m[key] as bool?;

  @override
  Future<void> saveBool(String key, bool value) async => _m[key] = value;
}

void main() {
  testWidgets('Counter increments smoke test', (WidgetTester tester) async {
    // Build our app and trigger a frame.
  await tester.pumpWidget(MyApp(storage: _FakeLocalStorage()));

    // Verify that our counter starts at 0.
    expect(find.text('0'), findsOneWidget);
    expect(find.text('1'), findsNothing);

    // Tap the '+' icon and trigger a frame.
    await tester.tap(find.byIcon(Icons.add));
    await tester.pump();

    // Verify that our counter has incremented.
    expect(find.text('0'), findsNothing);
    expect(find.text('1'), findsOneWidget);
  });
}
