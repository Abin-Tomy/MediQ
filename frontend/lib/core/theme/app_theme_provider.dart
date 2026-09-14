import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

enum ThemeModeType {
  light,
  amoledDark,
  monsoon,
}

enum LanguageType {
  english,
  malayalam,
}

class AppThemeProvider extends ChangeNotifier {
  static final AppThemeProvider _instance = AppThemeProvider._internal();
  factory AppThemeProvider() => _instance;
  AppThemeProvider._internal();

  ThemeModeType _themeMode = ThemeModeType.light;
  LanguageType _language = LanguageType.english;

  ThemeModeType get themeMode => _themeMode;
  LanguageType get language => _language;

  bool get isDark => _themeMode == ThemeModeType.amoledDark;
  bool get isMonsoon => _themeMode == ThemeModeType.monsoon;
  bool get isMalayalam => _language == LanguageType.malayalam;

  void toggleTheme() {
    if (_themeMode == ThemeModeType.light) {
      _themeMode = ThemeModeType.amoledDark;
    } else if (_themeMode == ThemeModeType.amoledDark) {
      _themeMode = ThemeModeType.monsoon;
    } else {
      _themeMode = ThemeModeType.light;
    }
    notifyListeners();
  }

  void setThemeMode(ThemeModeType mode) {
    if (_themeMode != mode) {
      _themeMode = mode;
      notifyListeners();
    }
  }

  void toggleLanguage() {
    _language = (_language == LanguageType.english)
        ? LanguageType.malayalam
        : LanguageType.english;
    notifyListeners();
  }

  // Reactive Color Tokens based on active theme
  Color get background {
    switch (_themeMode) {
      case ThemeModeType.amoledDark:
        return const Color(0xFF090D16); // Ultra Deep AMOLED
      case ThemeModeType.monsoon:
        return const Color(0xFF0E1A24); // Deep Rainy Teal Navy
      case ThemeModeType.light:
        return const Color(0xFFF8FAFC);
    }
  }

  Color get cardColor {
    switch (_themeMode) {
      case ThemeModeType.amoledDark:
        return const Color(0xFF131B2E);
      case ThemeModeType.monsoon:
        return const Color(0xFF162636);
      case ThemeModeType.light:
        return Colors.white;
    }
  }

  Color get textPrimary {
    switch (_themeMode) {
      case ThemeModeType.amoledDark:
      case ThemeModeType.monsoon:
        return const Color(0xFFF9FAFB);
      case ThemeModeType.light:
        return const Color(0xFF1F2937);
    }
  }

  Color get textSecondary {
    switch (_themeMode) {
      case ThemeModeType.amoledDark:
      case ThemeModeType.monsoon:
        return const Color(0xFF9CA3AF);
      case ThemeModeType.light:
        return const Color(0xFF6B7280);
    }
  }

  Color get textHint {
    switch (_themeMode) {
      case ThemeModeType.amoledDark:
      case ThemeModeType.monsoon:
        return const Color(0xFF6B7280);
      case ThemeModeType.light:
        return const Color(0xFF9CA3AF);
    }
  }

  Color get borderColor {
    switch (_themeMode) {
      case ThemeModeType.amoledDark:
        return const Color(0xFF23314F);
      case ThemeModeType.monsoon:
        return const Color(0xFF22384C);
      case ThemeModeType.light:
        return const Color(0xFFE5E7EB);
    }
  }

  Color get primaryAccent {
    switch (_themeMode) {
      case ThemeModeType.amoledDark:
        return const Color(0xFF3892FF); // Neon Blue
      case ThemeModeType.monsoon:
        return const Color(0xFF00D2B4); // Monsoon Aqua
      case ThemeModeType.light:
        return const Color(0xFF2F80ED);
    }
  }

  List<Color> get headerGradient {
    switch (_themeMode) {
      case ThemeModeType.amoledDark:
        return const [Color(0xFF1E3A8A), Color(0xFF3B82F6)];
      case ThemeModeType.monsoon:
        return const [Color(0xFF0D9488), Color(0xFF06B6D4)];
      case ThemeModeType.light:
        return const [Color(0xFF2F80ED), Color(0xFF56CCF2)];
    }
  }

  // Translation helper
  String tr(String eng, String mal) {
    return _language == LanguageType.malayalam ? mal : eng;
  }

  // Dynamic global ThemeData matching active theme tokens
  ThemeData get themeData {
    return ThemeData(
      useMaterial3: true,
      fontFamily: GoogleFonts.poppins().fontFamily,
      scaffoldBackgroundColor: background,
      brightness: isDark ? Brightness.dark : Brightness.light,
      colorScheme: ColorScheme.fromSeed(
        seedColor: primaryAccent,
        brightness: isDark ? Brightness.dark : Brightness.light,
        surface: background,
        primary: primaryAccent,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: false,
        surfaceTintColor: Colors.transparent,
        foregroundColor: textPrimary,
      ),
      cardTheme: CardThemeData(
        color: cardColor,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(24),
        ),
      ),
      dividerColor: borderColor,
    );
  }
}
