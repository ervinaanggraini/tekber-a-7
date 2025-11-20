// file: lib/screens/login_screen.dart (sesuaikan dengan path Anda)

import 'package:get/get.dart';
import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:moneyvesto/core/constants/color.dart';
import 'package:moneyvesto/core/global_components/base_widget_container.dart';
import 'package:moneyvesto/core/global_components/global_button.dart';
import 'package:moneyvesto/core/global_components/global_text.dart';
import 'package:moneyvesto/core/global_components/global_text_fields.dart';
import 'package:moneyvesto/core/global_components/legal_bottom_sheets.dart';
import 'package:moneyvesto/core/utils/route_utils.dart';
import 'package:moneyvesto/features/login/controller/login_controller.dart';

class LoginScreen extends StatelessWidget {
  const LoginScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final controller = Get.put(LoginController());

    TextStyle defaultTextStyle = TextStyle(
      fontSize: 11.sp,
      color: AppColors.textLight.withOpacity(0.7),
      fontFamily: Theme.of(context).textTheme.bodyMedium?.fontFamily,
    );
    TextStyle linkTextStyle = TextStyle(
      fontSize: 11.sp,
      color: AppColors.primaryAccent,
      decoration: TextDecoration.underline,
      decorationColor: AppColors.primaryAccent,
      fontFamily: Theme.of(context).textTheme.bodyMedium?.fontFamily,
    );

    return BaseWidgetContainer(
      backgroundColor: AppColors.background,
      body: SingleChildScrollView(
        child: SafeArea(
          child: Padding(
            padding: EdgeInsets.symmetric(horizontal: 24.w),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SizedBox(height: 40.h),
                GlobalText.semiBold(
                  'Welcome Back!',
                  fontSize: 24.sp,
                  color: AppColors.textLight,
                ),
                SizedBox(height: 8.h),
                GlobalText.regular(
                  'Sign in to your account to continue',
                  fontSize: 14.sp,
                  color: AppColors.textLight,
                ),
                SizedBox(height: 30.h),
                GlobalTextField(
                  controller: controller.usernameController,
                  hintText: 'Username',
                  keyboardType: TextInputType.name,
                ),
                SizedBox(height: 18.h),
                GlobalTextField(
                  controller: controller.passwordController,
                  hintText: 'Password',
                  isPassword: true,
                ),
                SizedBox(height: 10.h),
                Align(
                  alignment: Alignment.centerRight,
                  child: TextButton(
                    style: TextButton.styleFrom(
                      padding: EdgeInsets.zero,
                      minimumSize: Size.zero,
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                    onPressed: () {
                      Get.toNamed(NavigationRoutes.forgotPassword);
                    },
                    child: GlobalText.regular(
                      'Forgot Password?',
                      fontSize: 12.sp,
                      color: AppColors.textLight,
                    ),
                  ),
                ),
                SizedBox(height: 25.h),

                Obx(
                  () => GlobalButton(
                    isLoading: controller.isLoading.value,
                    text: 'Sign In',
                    backgroundColor: AppColors.primaryAccent,
                    textColor: AppColors.textLight,
                    onPressed: () {
                      controller.login();
                    },
                    width: 1.sw,
                    fontSize: 14.sp,
                    height: 48.h,
                  ),
                ),

                SizedBox(height: 20.h),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    GlobalText.regular(
                      "Don't have an account?",
                      fontSize: 12.sp,
                      color: AppColors.textLight,
                    ),
                    TextButton(
                      style: TextButton.styleFrom(
                        padding: EdgeInsets.only(left: 4.w),
                        minimumSize: Size.zero,
                        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      ),
                      onPressed: () {
                        Get.toNamed(NavigationRoutes.signUp);
                      },
                      child: GlobalText.semiBold(
                        'Sign Up',
                        fontSize: 12.sp,
                        color: AppColors.primaryAccent,
                      ),
                    ),
                  ],
                ),
                SizedBox(height: 20.h),
                Padding(
                  padding: EdgeInsets.symmetric(horizontal: 8.w),
                  child: Center(
                    child: RichText(
                      textAlign: TextAlign.center,
                      text: TextSpan(
                        style: defaultTextStyle,
                        children: <TextSpan>[
                          const TextSpan(
                            text: 'By signing in, you agree to our\n',
                          ),
                          TextSpan(
                            text: 'Terms of Service',
                            style: linkTextStyle,
                            recognizer:
                                TapGestureRecognizer()
                                  ..onTap = () {
                                    showTermsOfServiceBottomSheet();
                                  },
                          ),
                          const TextSpan(text: ' and '),
                          TextSpan(
                            text: 'Privacy Policy',
                            style: linkTextStyle,
                            recognizer:
                                TapGestureRecognizer()
                                  ..onTap = () {
                                    showPrivacyPolicyBottomSheet();
                                  },
                          ),
                          const TextSpan(text: '.'),
                        ],
                      ),
                    ),
                  ),
                ),
                SizedBox(height: 20.h),
              ],
            ),
          ),
        ),
      ),
    );
  }
}