import 'package:flutter/material.dart';
import 'app_colors.dart';

/// Reusable gradients for the AI Medical Assistant app.
class AppGradients {
  AppGradients._();

  static const LinearGradient primary = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [
      AppColors.primary,
      AppColors.secondary,
    ],
  );

  static const LinearGradient aiAssistant = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [
      Color(0xFF2F80ED),
      Color(0xFF4DA8F7),
      Color(0xFF56CCF2),
    ],
  );

  static const LinearGradient success = LinearGradient(
    colors: [
      Color(0xFF27AE60),
      Color(0xFF6FCF97),
    ],
  );

  static const LinearGradient warning = LinearGradient(
    colors: [
      Color(0xFFF2994A),
      Color(0xFFF2C94C),
    ],
  );

  static const LinearGradient danger = LinearGradient(
    colors: [
      Color(0xFFEB5757),
      Color(0xFFFF8A80),
    ],
  );

  static const LinearGradient pageBackground = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [
      Color(0xFFF8FAFC),
      Color(0xFFEFF7FF),
    ],
  );

  static const LinearGradient glassOverlay = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [
      Color.fromARGB(180, 255, 255, 255),
      Color.fromARGB(110, 255, 255, 255),
    ],
  );
}
