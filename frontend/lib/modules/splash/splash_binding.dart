import 'package:get/get.dart';
import '../../core/storage/shared_local_storage.dart';
import 'splash_controller.dart';

class SplashBinding extends Bindings {
  @override
  void dependencies() {
    // expect ILocalStorage already registered globally in main
    Get.lazyPut<SplashController>(() => SplashController(Get.find<ILocalStorage>()));
  }
}
