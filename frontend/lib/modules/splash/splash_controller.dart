import 'dart:async';

import 'package:get/get.dart';
import '../../core/storage/shared_local_storage.dart';
import '../../core/routes/app_routes.dart';

class SplashController extends GetxController {
  final ILocalStorage storage;

  SplashController(this.storage);

  @override
  void onInit() {
    super.onInit();
    print('SplashController: onInit called');
    Timer(const Duration(seconds: 2), _decideNext);
  }

  Future<void> _decideNext() async {
    print('SplashController: _decideNext called');
    final seen = await storage.readBool('seenOnboarding') ?? false;
    print('SplashController: seenOnboarding = $seen');
    if (seen) {
      print('SplashController: Navigating to home');
      Get.offAllNamed(AppRoutes.home);
    } else {
      print('SplashController: Navigating to onboarding');
      Get.offAllNamed(AppRoutes.onboarding);
    }
  }
}
