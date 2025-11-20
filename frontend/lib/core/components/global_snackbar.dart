import 'package:flutter/material.dart';
import '../constants/app_text_styles.dart';

/// Utility to show a simple global snackbar/message.
void showGlobalSnackBar(BuildContext context, String message,
    {Duration duration = const Duration(seconds: 3)}) {
  final messenger = ScaffoldMessenger.of(context);
  messenger.hideCurrentSnackBar();
  messenger.showSnackBar(
    SnackBar(
      content: Text(message, style: AppTextStyles.body),
      duration: duration,
    ),
  );
}
