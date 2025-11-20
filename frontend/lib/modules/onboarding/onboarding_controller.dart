import 'package:flutter/widgets.dart';
import 'package:get/get.dart';
import '../../core/storage/shared_local_storage.dart';
import '../../core/routes/app_routes.dart';

class OnboardingController extends GetxController {
  final ILocalStorage storage;
  final pageIndex = 0.obs;
  late final PageController pageController;

  OnboardingController(this.storage);

  @override
  void onInit() {
    super.onInit();
    pageController = PageController();
  }

  void next() {
    final nextIdx = pageIndex.value + 1;
    if (nextIdx >= 3) {
      complete();
    } else {
      pageController.nextPage(duration: const Duration(milliseconds: 300), curve: Curves.easeInOut);
    }
  }

  void jumpToLast() => pageController.jumpToPage(2);

  void updateIndex(int i) => pageIndex.value = i;

  Future<void> complete() async {
    await storage.saveBool('seenOnboarding', true);
    Get.offAllNamed(AppRoutes.home);
  }

  @override
  void onClose() {
    pageController.dispose();
    super.onClose();
  }
}
