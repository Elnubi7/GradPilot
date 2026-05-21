import 'package:flutter/material.dart';

import '../screens/login_screen.dart';
import '../screens/main_nav_screen.dart';
import '../screens/generate_ideas_screen.dart';
import '../screens/register_screen.dart';
import '../screens/splash_screen.dart';

class AppRoutes {
  const AppRoutes._();

  static const splash = '/';
  static const login = '/login';
  static const register = '/register';
  static const main = '/main';
  static const generateIdeas = '/generate-ideas';

  static Map<String, WidgetBuilder> get routes => {
        splash: (_) => const SplashScreen(),
        login: (_) => const LoginScreen(),
        register: (_) => const RegisterScreen(),
        main: (_) => const MainNavScreen(),
        generateIdeas: (_) => const GenerateIdeasScreen(),
      };
}
