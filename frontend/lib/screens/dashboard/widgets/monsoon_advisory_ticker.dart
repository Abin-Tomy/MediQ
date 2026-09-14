import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/theme/app_theme_provider.dart';

class MonsoonAdvisoryTicker extends StatefulWidget {
  const MonsoonAdvisoryTicker({super.key});

  @override
  State<MonsoonAdvisoryTicker> createState() => _MonsoonAdvisoryTickerState();
}

class _MonsoonAdvisoryTickerState extends State<MonsoonAdvisoryTicker>
    with SingleTickerProviderStateMixin {
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);

    _pulseAnimation = Tween<double>(begin: 0.85, end: 1.0).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: Listenable.merge([AppThemeProvider(), _pulseAnimation]),
      builder: (context, _) {
        final theme = AppThemeProvider();

        final title = theme.tr(
          "Kozhikode Monsoon & Dengue Advisory Active",
          "കോഴിക്കോട് മൺസൂൺ & ഡെങ്കിപ്പനി ജാഗ്രത",
        );
        final subtitle = theme.tr(
          "Boil drinking water • Seek immediate care if platelet drop occurs.",
          "തിളപ്പിച്ചാറ്റിയ വെള്ളം മാത്രം കുടിക്കുക • പനി കണ്ടാൽ ഉടൻ ഡോക്ടറെ കാണുക.",
        );

        return Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: theme.isMonsoon
                  ? [const Color(0xFF0D9488).withValues(alpha: .3), const Color(0xFF06B6D4).withValues(alpha: .3)]
                  : (theme.isDark
                      ? [const Color(0xFF1E293B), const Color(0xFF0F172A)]
                      : [const Color(0xFFE0F2FE), const Color(0xFFBAE6FD)]),
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: theme.isMonsoon
                  ? const Color(0xFF00D2B4).withValues(alpha: .5)
                  : const Color(0xFF0284C7).withValues(alpha: .3),
            ),
            boxShadow: [
              BoxShadow(
                color: theme.isMonsoon
                    ? const Color(0xFF00D2B4).withValues(alpha: .1)
                    : Colors.black.withValues(alpha: .04),
                blurRadius: 10,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Row(
            children: [
              ScaleTransition(
                scale: _pulseAnimation,
                child: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: theme.isMonsoon
                        ? const Color(0xFF00D2B4).withValues(alpha: .2)
                        : const Color(0xFF0284C7).withValues(alpha: .15),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    theme.isMonsoon ? Icons.water_drop_rounded : Icons.warning_amber_rounded,
                    color: theme.isMonsoon ? const Color(0xFF00D2B4) : const Color(0xFF0284C7),
                    size: 22,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: GoogleFonts.poppins(
                        fontSize: 12.5,
                        fontWeight: FontWeight.w700,
                        color: theme.isDark || theme.isMonsoon
                            ? Colors.white
                            : const Color(0xFF0369A1),
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      subtitle,
                      style: GoogleFonts.poppins(
                        fontSize: 11,
                        fontWeight: FontWeight.w400,
                        color: theme.isDark || theme.isMonsoon
                            ? Colors.white70
                            : const Color(0xFF0C4A6E),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Icon(
                Icons.arrow_forward_ios_rounded,
                size: 14,
                color: theme.isDark || theme.isMonsoon ? Colors.white54 : const Color(0xFF0369A1),
              ),
            ],
          ),
        );
      },
    );
  }
}
