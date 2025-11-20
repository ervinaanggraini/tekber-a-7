import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'core/storage/shared_local_storage.dart';
import 'core/constants/app_colors.dart';
// routes/pages are provided via AppPages
import 'core/routes/app_pages.dart';
import 'core/routes/app_routes.dart';
import 'shared/not_found_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final prefs = await SharedPreferences.getInstance();
  final storage = SharedLocalStorage(prefs);
  // register storage globally so bindings/controllers can find it
  Get.put<ILocalStorage>(storage);
  runApp(MyApp(storage: storage));
}

class MyApp extends StatelessWidget {
  final ILocalStorage storage;
  const MyApp({super.key, required this.storage});

  @override
  Widget build(BuildContext context) {
    return GetMaterialApp(
      title: 'TekberApp',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: AppColors.primary),
        scaffoldBackgroundColor: AppColors.background,
        appBarTheme: const AppBarTheme(backgroundColor: AppColors.primary, foregroundColor: AppColors.surface),
      ),
      initialRoute: AppRoutes.splash,
      getPages: AppPages.routes,
      unknownRoute: GetPage(name: AppRoutes.notFound, page: () => const NotFoundScreen()),
    );
  }
}
