import 'package:flutter/material.dart';

/// Central color palette for the AI Medical Assistant app.
/// Use these colors throughout the project instead of hardcoding values.
class AppColors {
  AppColors._();

  // Brand
  static const Color primary = Color(0xFF2F80ED);
  static const Color secondary = Color(0xFF56CCF2);
  static const Color accent = Color(0xFF27AE60);

  // Status
  static const Color success = Color(0xFF27AE60);
  static const Color warning = Color(0xFFF2C94C);
  static const Color error = Color(0xFFEB5757);

  // Backgrounds
  static const Color background = Color(0xFFF8FAFC);
  static const Color surface = Colors.white;
  static const Color card = Colors.white;

  // Text
  static const Color textPrimary = Color(0xFF1F2937);
  static const Color textSecondary = Color(0xFF6B7280);
  static const Color textHint = Color(0xFF9CA3AF);

  // Borders & Dividers
  static const Color border = Color(0xFFE5E7EB);
  static const Color divider = Color(0xFFEDF2F7);

  // Misc
  static const Color shadow = Color(0x14000000);
  static const Color icon = Color(0xFF4B5563);

  // Dashboard
  static const Color healthBlue = Color(0xFF2F80ED);
  static const Color healthGreen = Color(0xFF27AE60);
  static const Color healthOrange = Color(0xFFF2994A);
  static const Color healthRed = Color(0xFFEB5757);
}
