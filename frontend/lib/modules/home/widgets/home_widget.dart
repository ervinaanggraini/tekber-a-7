import 'package:flutter/material.dart';
import '../../../core/constants/app_text_styles.dart';

class HomeWidget extends StatelessWidget {
  const HomeWidget({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: const [
        Icon(Icons.home, size: 72),
        SizedBox(height: 12),
        Text('Welcome to the Home Module!', style: AppTextStyles.body),
      ],
    );
  }
}
