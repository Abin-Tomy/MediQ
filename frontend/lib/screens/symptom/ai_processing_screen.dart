import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/theme/app_theme_provider.dart';
import '../../models/symptom_analysis.dart';
import 'diagnosis_screen.dart';

class AIProcessingScreen extends StatefulWidget {
  final SymptomAnalysis analysis;

  const AIProcessingScreen({
    super.key,
    required this.analysis,
  });

  @override
  State<AIProcessingScreen> createState() =>
      _AIProcessingScreenState();
}

class _AIProcessingScreenState
    extends State<AIProcessingScreen>
    with TickerProviderStateMixin {

  late AnimationController pulseController;
  int currentStep = 0;
  int confidence = 0;

  final List<Map<String, String>> steps = [
    {
      "en": "Understanding your symptoms",
      "ml": "ലക്ഷണങ്ങൾ മനസ്സിലാക്കുന്നു",
    },
    {
      "en": "Reviewing medical knowledge",
      "ml": "വൈദ്യശാസ്ത്ര വിവരങ്ങൾ പരിശോധിക്കുന്നു",
    },
    {
      "en": "Comparing similar medical cases",
      "ml": "സമാനമായ രോഗവിവരങ്ങൾ താരതമ്യം ചെയ്യുന്നു",
    },
    {
      "en": "Finding possible conditions",
      "ml": "സാധ്യതയുള്ള രോഗങ്ങൾ കണ്ടെത്തുന്നു",
    },
    {
      "en": "Selecting the right specialist",
      "ml": "അനുയോജ്യമായ ഡോക്ടറെ നിർദ്ദേശിക്കുന്നു",
    },
    {
      "en": "Generating health report",
      "ml": "ആരോഗ്യ റിപ്പോർട്ട് തയ്യാറാക്കുന്നു",
    },
  ];

  @override
  void initState() {
    super.initState();
    pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1400),
    )..repeat(reverse: true);

    startAnalysis();
  }

  Future<void> startAnalysis() async {
    for (int i = 0; i < steps.length; i++) {
      await Future.delayed(
        const Duration(milliseconds: 900),
      );
      if (!mounted) return;
      setState(() {
        currentStep = i + 1;
        confidence =
            ((i + 1) / steps.length * 94).round();
      });
    }

    await Future.delayed(
      const Duration(milliseconds: 1200),
    );

    if (!mounted) return;

    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (_) => DiagnosisScreen(
          analysis: widget.analysis,
        ),
      ),
    );
  }

  @override
  void dispose() {
    pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: AppThemeProvider(),
      builder: (context, _) {
        final theme = AppThemeProvider();

        final title = theme.tr("MediQ AI", "MediQ AI");
        final subtitle = theme.tr("Analyzing your symptoms...", "ലക്ഷണങ്ങൾ പരിശോധിക്കുന്നു...");
        final confLbl = theme.tr("AI Confidence", "AI കൃത്യത");
        final waitLbl = theme.tr(
          "Please wait while MediQ prepares your report.",
          "റിപ്പോർട്ട് തയ്യാറാക്കുന്നത് വരെ ദയവായി കാത്തിരിക്കുക.",
        );

        return Scaffold(
          backgroundColor: theme.background,
          body: SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                children: [
                  const Spacer(),
                  AnimatedBuilder(
                    animation: pulseController,
                    builder: (_, child) {
                      final scale = 1 + pulseController.value * .08;
                      return Transform.scale(
                        scale: scale,
                        child: child,
                      );
                    },
                    child: Container(
                      width: 130,
                      height: 130,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: LinearGradient(
                          colors: theme.isMonsoon
                              ? [const Color(0xFF0D9488), const Color(0xFF06B6D4)]
                              : [const Color(0xFF2F80ED), const Color(0xFF56CCF2)],
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: theme.primaryAccent.withValues(alpha: .25),
                            blurRadius: 30,
                            spreadRadius: 10,
                          ),
                        ],
                      ),
                      child: const Icon(
                        Icons.psychology_alt_rounded,
                        color: Colors.white,
                        size: 70,
                      ),
                    ),
                  ),

                  const SizedBox(height: 28),

                  Text(
                    title,
                    style: GoogleFonts.poppins(
                      fontSize: 34,
                      fontWeight: FontWeight.bold,
                      color: theme.textPrimary,
                    ),
                  ),

                  const SizedBox(height: 10),

                  Text(
                    subtitle,
                    style: GoogleFonts.poppins(
                      color: theme.textSecondary,
                      fontSize: 16,
                    ),
                  ),

                  const SizedBox(height: 35),

                  TweenAnimationBuilder<double>(
                    tween: Tween(
                      begin: 0,
                      end: currentStep / steps.length,
                    ),
                    duration: const Duration(milliseconds: 700),
                    builder: (context, value, child) {
                      return ClipRRect(
                        borderRadius: BorderRadius.circular(20),
                        child: LinearProgressIndicator(
                          value: value,
                          minHeight: 8,
                          backgroundColor: theme.isDark || theme.isMonsoon
                              ? const Color(0xFF1E293B)
                              : const Color(0xFFE2E8F0),
                          valueColor: AlwaysStoppedAnimation<Color>(theme.primaryAccent),
                        ),
                      );
                    },
                  ),

                  const SizedBox(height: 15),

                  Text(
                    "$confLbl  $confidence%",
                    style: GoogleFonts.poppins(
                      fontWeight: FontWeight.bold,
                      color: theme.primaryAccent,
                    ),
                  ),

                  const SizedBox(height: 35),

                  Expanded(
                    child: ListView.builder(
                      physics: const NeverScrollableScrollPhysics(),
                      itemCount: steps.length,
                      itemBuilder: (_, index) {
                        final completed = currentStep > index;
                        final active = currentStep == index;

                        final stepText = theme.tr(
                          steps[index]["en"]!,
                          steps[index]["ml"]!,
                        );

                        return AnimatedOpacity(
                          duration: const Duration(milliseconds: 500),
                          opacity: completed || active ? 1 : .35,
                          child: Container(
                            margin: const EdgeInsets.only(bottom: 16),
                            padding: const EdgeInsets.all(18),
                            decoration: BoxDecoration(
                              color: theme.cardColor,
                              borderRadius: BorderRadius.circular(20),
                              border: Border.all(color: theme.borderColor),
                              boxShadow: [
                                BoxShadow(
                                  color: Colors.black.withValues(alpha: .04),
                                  blurRadius: 12,
                                ),
                              ],
                            ),
                            child: Row(
                              children: [
                                if (completed)
                                  const Icon(
                                    Icons.check_circle_rounded,
                                    color: Color(0xFF10B981),
                                  )
                                else if (active)
                                  SizedBox(
                                    width: 22,
                                    height: 22,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2.5,
                                      valueColor: AlwaysStoppedAnimation<Color>(theme.primaryAccent),
                                    ),
                                  )
                                else
                                  Icon(
                                    Icons.radio_button_unchecked,
                                    color: theme.textHint,
                                  ),
                                const SizedBox(width: 15),
                                Expanded(
                                  child: Text(
                                    stepText,
                                    style: GoogleFonts.poppins(
                                      fontSize: 15.5,
                                      fontWeight: completed || active
                                          ? FontWeight.w600
                                          : FontWeight.w500,
                                      color: theme.textPrimary,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
                  ),

                  Text(
                    waitLbl,
                    textAlign: TextAlign.center,
                    style: GoogleFonts.poppins(
                      color: theme.textSecondary,
                      fontSize: 12.5,
                    ),
                  ),

                  const SizedBox(height: 15),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}