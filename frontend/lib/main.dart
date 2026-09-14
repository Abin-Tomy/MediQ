import 'package:flutter/material.dart';
import 'core/theme/app_theme_provider.dart';
import 'core/routing/app_router.dart';
import 'screens/auth/login_screen.dart';

void main() {
  runApp(const MedicalAIApp());
}

class MedicalAIApp extends StatelessWidget {
  const MedicalAIApp({super.key});

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: AppThemeProvider(),
      builder: (context, _) {
        final theme = AppThemeProvider();
        return MaterialApp(
          title: 'MediQ',
          debugShowCheckedModeBanner: false,
          theme: theme.themeData,
          onGenerateRoute: AppRouter.generateRoute,
          home: const LoginScreen(),
        );
      },
    );
  }
}
