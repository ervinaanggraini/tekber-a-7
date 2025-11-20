import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../core/constants/app_text_styles.dart';
import 'splash_controller.dart';

class SplashPage extends StatelessWidget {
  const SplashPage({super.key});

  @override
  Widget build(BuildContext context) {
    // Get the controller to trigger onInit which starts the timer
    final controller = Get.find<SplashController>();
    print('SplashPage: Controller found: ${controller.runtimeType}');
    
    return const Scaffold(
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            FlutterLogo(size: 96),
            SizedBox(height: 16),
            Text('TekberApp', style: AppTextStyles.title),
          ],
        ),
      ),
    );
  }
}
