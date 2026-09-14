import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/theme/app_theme_provider.dart';
import '../../../core/theme/app_colors.dart';

class ClinicTokenTracker extends StatelessWidget {
  const ClinicTokenTracker({super.key});

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: AppThemeProvider(),
      builder: (context, _) {
        final theme = AppThemeProvider();

        final title = theme.tr(
          "Live Clinic Token Queue",
          "തത്സമയ ക്ലിനിക്ക് ടോക്കൺ",
        );
        final doctorName = theme.tr(
          "Dr. Thomas Kurian • St. Joseph's Kozhikode",
          "ഡോ. തോമസ് കുര്യൻ • സെന്റ് ജോസഫ്സ് കോഴിക്കോട്",
        );
        final currentTokenLbl = theme.tr("Current Token", "ഇപ്പോഴത്തെ ടോക്കൺ");
        final yourTokenLbl = theme.tr("Your Token", "നിങ്ങളുടെ ടോക്കൺ");
        final estWaitLbl = theme.tr("Est. Wait Time", "പ്രതീക്ഷിക്കുന്ന സമയം");

        return Container(
          width: double.infinity,
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            color: theme.cardColor,
            borderRadius: BorderRadius.circular(22),
            border: Border.all(
              color: theme.isMonsoon
                  ? const Color(0xFF00D2B4).withValues(alpha: .4)
                  : (theme.isDark ? const Color(0xFF3892FF).withValues(alpha: .3) : AppColors.border),
              width: 1.2,
            ),
            boxShadow: [
              BoxShadow(
                color: theme.isDark ? Colors.black38 : AppColors.shadow,
                blurRadius: 16,
                offset: const Offset(0, 6),
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // HEADER ROW
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: const Color(0xFF10B981).withValues(alpha: .15),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: const Icon(
                          Icons.confirmation_num_rounded,
                          color: Color(0xFF10B981),
                          size: 18,
                        ),
                      ),
                      const SizedBox(width: 10),
                      Text(
                        title,
                        style: GoogleFonts.poppins(
                          fontSize: 14.5,
                          fontWeight: FontWeight.w700,
                          color: theme.textPrimary,
                        ),
                      ),
                    ],
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                    decoration: BoxDecoration(
                      color: const Color(0xFF10B981).withValues(alpha: .15),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Container(
                          width: 6,
                          height: 6,
                          decoration: const BoxDecoration(
                            color: Color(0xFF10B981),
                            shape: BoxShape.circle,
                          ),
                        ),
                        const SizedBox(width: 6),
                        Text(
                          theme.tr("LIVE", "തത്സമയം"),
                          style: GoogleFonts.poppins(
                            fontSize: 10.5,
                            fontWeight: FontWeight.w700,
                            color: const Color(0xFF10B981),
                            letterSpacing: 0.5,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 6),

              Text(
                doctorName,
                style: GoogleFonts.poppins(
                  fontSize: 12,
                  fontWeight: FontWeight.w500,
                  color: theme.textSecondary,
                ),
              ),

              const SizedBox(height: 16),

              // TOKEN STATS ROW
              Row(
                children: [
                  Expanded(
                    child: _buildTokenBox(
                      label: currentTokenLbl,
                      value: "14",
                      valueColor: const Color(0xFF10B981),
                      theme: theme,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _buildTokenBox(
                      label: yourTokenLbl,
                      value: "18",
                      valueColor: theme.primaryAccent,
                      theme: theme,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _buildTokenBox(
                      label: estWaitLbl,
                      value: "~20 min",
                      valueColor: const Color(0xFFF59E0B),
                      theme: theme,
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 16),

              // PROGRESS BAR
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        theme.tr("Queue Progress (4 patients ahead)", "ക്യൂ പുരോഗതി (4 പേർ മുമ്പിലുണ്ട്)"),
                        style: GoogleFonts.poppins(
                          fontSize: 11,
                          fontWeight: FontWeight.w500,
                          color: theme.textSecondary,
                        ),
                      ),
                      Text(
                        "78%",
                        style: GoogleFonts.poppins(
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          color: theme.primaryAccent,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(8),
                    child: LinearProgressIndicator(
                      value: 14 / 18,
                      minHeight: 8,
                      backgroundColor: theme.isDark || theme.isMonsoon
                          ? const Color(0xFF1E293B)
                          : const Color(0xFFE2E8F0),
                      valueColor: AlwaysStoppedAnimation<Color>(theme.primaryAccent),
                    ),
                  ),
                ],
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildTokenBox({
    required String label,
    required String value,
    required Color valueColor,
    required AppThemeProvider theme,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
      decoration: BoxDecoration(
        color: theme.isDark || theme.isMonsoon
            ? const Color(0xFF1E293B).withValues(alpha: .5)
            : const Color(0xFFF1F5F9),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Column(
        children: [
          Text(
            label,
            textAlign: TextAlign.center,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: GoogleFonts.poppins(
              fontSize: 10.5,
              fontWeight: FontWeight.w500,
              color: theme.textSecondary,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            value,
            style: GoogleFonts.poppins(
              fontSize: 16,
              fontWeight: FontWeight.w700,
              color: valueColor,
            ),
          ),
        ],
      ),
    );
  }
}
