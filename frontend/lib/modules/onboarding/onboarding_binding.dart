import 'package:get/get.dart';
import '../../core/storage/shared_local_storage.dart';
import 'onboarding_controller.dart';

class OnboardingBinding extends Bindings {
  @override
  void dependencies() {
    Get.lazyPut<OnboardingController>(() => OnboardingController(Get.find<ILocalStorage>()));
  }
}
