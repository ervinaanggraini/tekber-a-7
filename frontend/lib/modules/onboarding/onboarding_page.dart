import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../core/constants/app_text_styles.dart';
import '../../modules/onboarding/onboarding_controller.dart';

class OnboardingPage extends StatelessWidget {
  const OnboardingPage({super.key});

  @override
  Widget build(BuildContext context) {
  final controller = Get.find<OnboardingController>();
    final pages = [
      _buildPage('Welcome', 'Discover features of TekberApp'),
      _buildPage('Fast', 'Fast and responsive'),
      _buildPage('Secure', 'Your data is safe with us'),
    ];

    return Scaffold(
      appBar: AppBar(title: const Text('Onboarding')),
      body: Column(
        children: [
          Expanded(
            child: PageView(controller: controller.pageController, onPageChanged: controller.updateIndex, children: pages),
          ),
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                TextButton(
                  onPressed: controller.jumpToLast,
                  child: const Text('Skip'),
                ),
                Obx(() => ElevatedButton(
                      onPressed: controller.pageIndex.value == pages.length - 1 ? controller.complete : controller.next,
                      child: Text(controller.pageIndex.value == pages.length - 1 ? 'Get Started' : 'Next'),
                    )),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPage(String title, String subtitle) => Center(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24.0),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              FlutterLogo(size: 96),
              const SizedBox(height: 16),
              Text(title, style: AppTextStyles.heading),
              const SizedBox(height: 8),
              Text(subtitle, style: AppTextStyles.subtitle, textAlign: TextAlign.center),
            ],
          ),
        ),
      );
}
