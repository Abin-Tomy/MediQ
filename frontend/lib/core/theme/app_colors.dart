import 'package:flutter/material.dart';

/// Premium central color palette for the MediQ app based on SRS.
class AppColors {
  AppColors._();

  // Premium Brand Colors
  static const Color primary = Color(0xFF2F80ED); // From SRS
  static const Color primaryDark = Color(0xFF205BB0);
  static const Color primaryLight = Color(0xFFE5EFFF);
  
  static const Color secondary = Color(0xFF56CCF2); // From SRS
  static const Color accent = Color(0xFF27AE60); // From SRS (Accent/Success)

  // AI & Gradients
  static const Color aiGradientStart = Color(0xFF2F80ED); 
  static const Color aiGradientEnd = Color(0xFF56CCF2); 

  // Backgrounds & Surfaces
  static const Color background = Color(0xFFF8FAFC); // From SRS
  static const Color surface = Colors.white;
  static const Color card = Colors.white; // From SRS

  // Text
  static const Color textPrimary = Color(0xFF1F2937); // From SRS
  static const Color textSecondary = Color(0xFF6B7280); 
  static const Color textHint = Color(0xFF9CA3AF);

  // Status
  static const Color success = Color(0xFF27AE60); // From SRS
  static const Color warning = Color(0xFFF2C94C); // From SRS
  static const Color error = Color(0xFFEB5757); // From SRS

  // Borders & Dividers
  static const Color border = Color(0xFFE5E7EB);
  static const Color divider = Color(0xFFF3F4F6);

  // Shadows
  static const Color shadow = Color(0x1A000000);
}
