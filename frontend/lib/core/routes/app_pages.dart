import 'package:get/get.dart';

import '../routes/app_routes.dart';
import '../../modules/splash/splash_page.dart';
import '../../modules/splash/splash_binding.dart';
import '../../modules/onboarding/onboarding_page.dart';
import '../../modules/onboarding/onboarding_binding.dart';
import '../../modules/home/pages/home_page.dart';
import '../../modules/auth/login_screen.dart';
import '../../modules/auth/login_binding.dart';
import '../../shared/not_found_screen.dart';

class AppPages {
  static final List<GetPage> routes = [
    // Common
    GetPage(
      name: AppRoutes.initial,
      page: () => const SplashPage(),
      binding: SplashBinding()
    ),
    GetPage(
      name: AppRoutes.splash,
      page: () => const SplashPage(),
      binding: SplashBinding()
    ),
    GetPage(
      name: AppRoutes.onboarding,
      page: () => const OnboardingPage(),
      binding: OnboardingBinding()
    ),

    // Authentication
    GetPage(
      name: AppRoutes.login,
      page: () => const LoginScreen(),
      binding: LoginBinding()
    ),

    // Home
    GetPage(
      name: AppRoutes.home,
      page: () => const HomePage()
    ),

    // Error
    GetPage(
      name: AppRoutes.notFound,
      page: () => const NotFoundScreen()
    ),
  ];
}
