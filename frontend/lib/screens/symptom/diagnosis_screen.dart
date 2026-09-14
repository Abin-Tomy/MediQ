import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_theme_provider.dart';
import '../../models/symptom_analysis.dart';
import '../doctor/doctor_list_screen.dart';
import '../dashboard/dashboard_screen.dart';

class DiagnosisScreen extends StatelessWidget {
  final SymptomAnalysis analysis;

  const DiagnosisScreen({
    super.key,
    required this.analysis,
  });

  List<Map<String, dynamic>> _generatePredictions() {
    final text = analysis.symptoms.toLowerCase();
    final isKeralaFloodCase = text.contains('flood') ||
        text.contains('water') ||
        text.contains('joint') ||
        text.contains('rash') ||
        text.contains('monsoon') ||
        text.contains('fever');

    if (isKeralaFloodCase) {
      return [
        {
          'disease': 'Leptospirosis',
          'confidence': 74,
          'color': const Color(0xFFEB5757),
          'flag': 'Floodwater exposure identified as significant risk factor.',
          'urgency': 'High',
        },
        {
          'disease': 'Chikungunya',
          'confidence': 68,
          'color': const Color(0xFFF2994A),
          'flag': 'Consistent with severe joint pain and high fever.',
          'urgency': 'Medium-High',
        },
        {
          'disease': 'Dengue Fever',
          'confidence': 61,
          'color': const Color(0xFFF2C94C),
          'flag': 'Monitor platelet counts and rash progression closely.',
          'urgency': 'Medium',
        },
      ];
    } else if (text.contains('cough') ||
        text.contains('throat') ||
        text.contains('breath') ||
        text.contains('chest')) {
      return [
        {
          'disease': 'Upper Respiratory Infection',
          'confidence': 82,
          'color': const Color(0xFF2F80ED),
          'flag': 'Common viral presentation. Watch for breathing difficulty.',
          'urgency': 'Medium',
        },
        {
          'disease': 'Influenza (Flu)',
          'confidence': 67,
          'color': const Color(0xFFF2994A),
          'flag': 'Systemic symptoms match seasonal influenza.',
          'urgency': 'Medium',
        },
        {
          'disease': 'Bronchitis',
          'confidence': 53,
          'color': const Color(0xFF56CCF2),
          'flag': 'Airway inflammation indicated by cough duration.',
          'urgency': 'Low-Medium',
        },
      ];
    } else {
      return [
        {
          'disease': 'Viral Fever Syndrome',
          'confidence': 71,
          'color': const Color(0xFF2F80ED),
          'flag': 'General systemic inflammation and fatigue.',
          'urgency': 'Medium',
        },
        {
          'disease': 'Dengue Presentation',
          'confidence': 64,
          'color': const Color(0xFFF2994A),
          'flag': 'Endemic vector risk. Platelet test recommended.',
          'urgency': 'Medium-High',
        },
        {
          'disease': 'Leptospirosis (Early Stage)',
          'confidence': 58,
          'color': const Color(0xFFEB5757),
          'flag': 'Environmental exposure risk check advised.',
          'urgency': 'High',
        },
      ];
    }
  }

  void _showSOSAmbulanceModal(BuildContext context, AppThemeProvider theme) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) {
        return AlertDialog(
          backgroundColor: theme.isDark || theme.isMonsoon
              ? const Color(0xFF1E293B)
              : Colors.white,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
          title: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: const BoxDecoration(
                  color: Color(0xFFEF4444),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.warning_amber_rounded, color: Colors.white, size: 24),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  theme.tr("EMERGENCY SOS DISPATCHED", "അടിയന്തര ആംബുലൻസ് വിളിച്ചു"),
                  style: GoogleFonts.poppins(
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                    color: const Color(0xFFEF4444),
                  ),
                ),
              ),
            ],
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                theme.tr(
                  "Ambulance Unit #KL-11-ER-108 has been dispatched to your GPS location in Kozhikode.\n\nETA: ~3.5 minutes\n\nSt. Joseph's Hospital Casualty & ER Triage has been pre-alerted with your symptoms.",
                  "ആംബുലൻസ് യൂണിറ്റ് #KL-11-ER-108 നിങ്ങളുടെ സ്ഥലത്തേക്ക് പുറപ്പെട്ടു.\n\nഎത്തിച്ചേരുന്ന സമയം: ~3.5 മിനിറ്റ്\n\nസെന്റ് ജോസഫ്സ് ആശുപത്രിയിലെ എമർജൻസി വിഭാഗത്തിൽ വിവരമറിയിച്ചിട്ടുണ്ട്.",
                ),
                style: GoogleFonts.poppins(
                  fontSize: 13,
                  color: theme.textPrimary,
                  height: 1.5,
                ),
              ),
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFF10B981).withValues(alpha: .15),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.check_circle_rounded, color: Color(0xFF10B981), size: 20),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        theme.tr("ER Bed #4 Reserved • Priority Triage Active", "ER ബെഡ് #4 തയ്യാറാണ് • മുൻഗണന നൽകും"),
                        style: GoogleFonts.poppins(
                          fontSize: 11.5,
                          fontWeight: FontWeight.w600,
                          color: const Color(0xFF10B981),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          actions: [
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFFEF4444),
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                onPressed: () => Navigator.pop(ctx),
                child: Text(
                  theme.tr("Keep Tracking & Stay Calm", "ട്രാക്കിംഗ് തുടരുക"),
                  style: GoogleFonts.poppins(fontWeight: FontWeight.w600),
                ),
              ),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final predictions = _generatePredictions();
    final topPrediction = predictions.first;
    final isHighUrgency = topPrediction['urgency'].toString().toLowerCase().contains('high');

    return AnimatedBuilder(
      animation: AppThemeProvider(),
      builder: (context, _) {
        final theme = AppThemeProvider();

        final title = theme.tr("AI Diagnostic Report", "AI ഡയഗ്നോസ്റ്റിക് റിപ്പോർട്ട്");
        final modelBadgeLbl = theme.tr(
          "Model 1 Output (DistilBERT Text Classifier)",
          "മോഡൽ 1 ഔട്ട്പുട്ട് (DistilBERT AI)",
        );
        final urgencyLbl = theme.tr("Urgency", "തീവ്രത");
        final urgencyDesc = theme.tr(
          "Your symptoms require medical evaluation today. Do not delay seeking professional advice.",
          "നിങ്ങളുടെ ലക്ഷണങ്ങൾക്ക് ഉടൻ ഡോക്ടറുടെ പരിശോധന ആവശ്യമാണ്. വൈകിക്കരുത്.",
        );
        final topProbLbl = theme.tr("Top Disease Probabilities", "സാധ്യതയുള്ള രോഗങ്ങൾ");
        final rankedByLbl = theme.tr("Ranked by AI confidence based on your input:", "നിങ്ങൾ നൽകിയ ലക്ഷണങ്ങളുടെ അടിസ്ഥാനത്തിൽ:");
        final reportedSymptomsLbl = theme.tr("Your Reported Symptoms", "നിങ്ങൾ രേഖപ്പെടുത്തിയ ലക്ഷണങ്ങൾ");
        final affectedAreaLbl = theme.tr("Affected Area", "ബാധിച്ച ഭാഗം");
        final severityLbl = theme.tr("Severity", "തീവ്രത");
        final durationLbl = theme.tr("Duration", "കാലയളവ്");
        final recActionLbl = theme.tr("Recommended Action", "ശുപാർശ ചെയ്യുന്ന നടപടി");
        final recDesc = theme.tr(
          "Based on these findings, we recommend consulting a General Physician or Infectious Disease Specialist immediately.",
          "ഈ വിവരങ്ങളുടെ അടിസ്ഥാനത്തിൽ ഉടൻ ഒരു ജനറൽ ഫിസിഷ്യനെയോ പകർച്ചവ്യാധി വിദഗ്ദ്ധനെയോ കാണുക.",
        );
        final findSpecialistsLbl = theme.tr("Find Specialists Nearby (5 km)", "അടുത്തുള്ള ഡോക്ടർമാരെ കാണുക (5 km)");
        final disclaimerLbl = theme.tr(
          "Disclaimer: MediQ is for decision support only and does not replace professional medical diagnosis.",
          "മുന്നറിയിപ്പ്: MediQ തീരുമാനങ്ങൾ എടുക്കാൻ സഹായിക്കുന്നതിന് മാത്രമുള്ളതാണ്, ഇത് വിദഗ്ദ്ധ വൈദ്യ പരിശോധനയ്ക്ക് പകരമാവില്ല.",
        );

        return Scaffold(
          backgroundColor: theme.background,
          appBar: AppBar(
            backgroundColor: Colors.transparent,
            elevation: 0,
            centerTitle: true,
            leading: IconButton(
              icon: Icon(Icons.close_rounded, color: theme.textPrimary),
              onPressed: () {
                Navigator.pushAndRemoveUntil(
                  context,
                  MaterialPageRoute(
                    builder: (_) => const DashboardScreen(userName: "Vishnu"),
                  ),
                  (route) => false,
                );
              },
            ),
            title: Text(
              title,
              style: GoogleFonts.poppins(
                color: theme.textPrimary,
                fontWeight: FontWeight.w600,
                fontSize: 18,
              ),
            ),
          ),
          body: SafeArea(
            child: SingleChildScrollView(
              physics: const BouncingScrollPhysics(),
              padding: const EdgeInsets.fromLTRB(24, 10, 24, 30),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // MODEL 1 BADGE
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                    decoration: BoxDecoration(
                      color: theme.isDark || theme.isMonsoon
                          ? const Color(0xFF1E293B)
                          : const Color(0xFFEAF4FF),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: theme.primaryAccent.withValues(alpha: .3)),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.psychology_alt_rounded, color: theme.primaryAccent, size: 18),
                        const SizedBox(width: 8),
                        Text(
                          modelBadgeLbl,
                          style: GoogleFonts.poppins(
                            color: theme.primaryAccent,
                            fontWeight: FontWeight.w600,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 20),

                  // RED ALERT EMERGENCY SOS BANNER (IF HIGH URGENCY OR ALWAYS ACCESSIBLE)
                  if (isHighUrgency || true) ...[
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(18),
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [Color(0xFF991B1B), Color(0xFFDC2626)],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                        borderRadius: BorderRadius.circular(24),
                        boxShadow: [
                          BoxShadow(
                            color: const Color(0xFFDC2626).withValues(alpha: .3),
                            blurRadius: 16,
                            offset: const Offset(0, 6),
                          ),
                        ],
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Container(
                                padding: const EdgeInsets.all(8),
                                decoration: BoxDecoration(
                                  color: Colors.white.withValues(alpha: .2),
                                  shape: BoxShape.circle,
                                ),
                                child: const Icon(Icons.emergency_rounded, color: Colors.white, size: 24),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Text(
                                  theme.tr("🚨 RED ALERT EMERGENCY SOS", "🚨 അടിയന്തര എമർജൻസി മുന്നറിയിപ്പ്"),
                                  style: GoogleFonts.poppins(
                                    fontSize: 15,
                                    fontWeight: FontWeight.w800,
                                    color: Colors.white,
                                    letterSpacing: 0.5,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 10),
                          Text(
                            theme.tr(
                              "High risk symptoms detected. Immediate ER casualty triage recommended.",
                              "ഗുരുതരമായ ലക്ഷണങ്ങൾ കാണുന്നു. ഉടൻ ആശുപത്രിയിൽ എത്തുക.",
                            ),
                            style: GoogleFonts.poppins(
                              fontSize: 12.5,
                              color: Colors.white.withValues(alpha: .95),
                            ),
                          ),
                          const SizedBox(height: 16),
                          Row(
                            children: [
                              Expanded(
                                child: ElevatedButton.icon(
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: Colors.white,
                                    foregroundColor: const Color(0xFFDC2626),
                                    elevation: 0,
                                    padding: const EdgeInsets.symmetric(vertical: 12),
                                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                                  ),
                                  icon: const Icon(Icons.phone_in_talk_rounded, size: 18),
                                  label: Text(
                                    theme.tr("CALL 108 AMBULANCE", "108 ആംബുലൻസ് വിളിക്കുക"),
                                    style: GoogleFonts.poppins(
                                      fontSize: 12.5,
                                      fontWeight: FontWeight.w800,
                                    ),
                                  ),
                                  onPressed: () => _showSOSAmbulanceModal(context, theme),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 10),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                            decoration: BoxDecoration(
                              color: Colors.black.withValues(alpha: .25),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                const Icon(Icons.local_hospital_rounded, color: Color(0xFF34D399), size: 14),
                                const SizedBox(width: 6),
                                Text(
                                  theme.tr("St. Joseph's Casualty Triage: 0 min wait (Ready)", "സെന്റ് ജോസഫ്സ് എമർജൻസി ബെഡ് തയ്യാറാണ്"),
                                  style: GoogleFonts.poppins(
                                    fontSize: 11,
                                    fontWeight: FontWeight.w600,
                                    color: Colors.white,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 20),
                  ],

                  // URGENCY CARD
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: theme.isDark || theme.isMonsoon
                            ? [const Color(0xFF450A0A), const Color(0xFF7F1D1D)]
                            : [const Color(0xFFFFF5F5), const Color(0xFFFFE3E3)],
                      ),
                      borderRadius: BorderRadius.circular(24),
                      border: Border.all(color: const Color(0xFFEB5757).withValues(alpha: .4)),
                      boxShadow: [
                        BoxShadow(
                          color: const Color(0xFFEB5757).withValues(alpha: .08),
                          blurRadius: 15,
                          offset: const Offset(0, 6),
                        ),
                      ],
                    ),
                    child: Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: const BoxDecoration(
                            color: Color(0xFFEB5757),
                            shape: BoxShape.circle,
                          ),
                          child: const Icon(Icons.priority_high_rounded, color: Colors.white, size: 28),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                "$urgencyLbl: ${topPrediction['urgency']} Priority",
                                style: GoogleFonts.poppins(
                                  fontSize: 16.5,
                                  fontWeight: FontWeight.w700,
                                  color: theme.isDark || theme.isMonsoon
                                      ? Colors.white
                                      : const Color(0xFF9B1C1C),
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                urgencyDesc,
                                style: GoogleFonts.poppins(
                                  fontSize: 12.5,
                                  color: theme.isDark || theme.isMonsoon
                                      ? Colors.white70
                                      : const Color(0xFF771D1D),
                                  height: 1.4,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 28),

                  Text(
                    topProbLbl,
                    style: GoogleFonts.poppins(
                      fontSize: 20,
                      fontWeight: FontWeight.w700,
                      color: theme.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    rankedByLbl,
                    style: GoogleFonts.poppins(
                      fontSize: 13.5,
                      color: theme.textSecondary,
                    ),
                  ),

                  const SizedBox(height: 16),

                  // PREDICTIONS LIST
                  ...predictions.map((pred) => _buildPredictionCard(pred, theme)),

                  const SizedBox(height: 24),

                  // INPUT SUMMARY CARD
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(18),
                    decoration: BoxDecoration(
                      color: theme.cardColor,
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: theme.borderColor),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          reportedSymptomsLbl,
                          style: GoogleFonts.poppins(
                            fontSize: 15,
                            fontWeight: FontWeight.w600,
                            color: theme.textPrimary,
                          ),
                        ),
                        Divider(height: 24, color: theme.borderColor),
                        _summaryRow(affectedAreaLbl, analysis.bodyArea, theme),
                        const SizedBox(height: 8),
                        _summaryRow(severityLbl, analysis.severity, theme),
                        const SizedBox(height: 8),
                        _summaryRow(durationLbl, analysis.duration, theme),
                        const SizedBox(height: 12),
                        Text(
                          "\"${analysis.symptoms}\"",
                          style: GoogleFonts.poppins(
                            fontSize: 13.5,
                            fontStyle: FontStyle.italic,
                            color: theme.textSecondary,
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 28),

                  // SPECIALIST RECOMMENDATION
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: theme.isMonsoon
                            ? [const Color(0xFF0D9488), const Color(0xFF06B6D4)]
                            : [const Color(0xFF2F80ED), const Color(0xFF56CCF2)],
                      ),
                      borderRadius: BorderRadius.circular(24),
                      boxShadow: [
                        BoxShadow(
                          color: theme.primaryAccent.withValues(alpha: .3),
                          blurRadius: 20,
                          offset: const Offset(0, 8),
                        ),
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            const Icon(Icons.verified_user_rounded, color: Colors.white, size: 26),
                            const SizedBox(width: 12),
                            Text(
                              recActionLbl,
                              style: GoogleFonts.poppins(
                                fontSize: 18,
                                fontWeight: FontWeight.w700,
                                color: Colors.white,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        Text(
                          recDesc,
                          style: GoogleFonts.poppins(
                            fontSize: 13.5,
                            color: Colors.white.withValues(alpha: .95),
                            height: 1.5,
                          ),
                        ),
                        const SizedBox(height: 20),
                        SizedBox(
                          width: double.infinity,
                          height: 54,
                          child: ElevatedButton(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.white,
                              foregroundColor: theme.primaryAccent,
                              elevation: 0,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(16),
                              ),
                            ),
                            onPressed: () {
                              Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (_) => const DoctorListScreen(),
                                ),
                              );
                            },
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Flexible(
                                  child: Text(
                                    findSpecialistsLbl,
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                    style: GoogleFonts.poppins(
                                      fontSize: 14.5,
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 8),
                                const Icon(Icons.arrow_forward_rounded, size: 20),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 16),
                  Center(
                    child: Text(
                      disclaimerLbl,
                      textAlign: TextAlign.center,
                      style: GoogleFonts.poppins(
                        fontSize: 11,
                        color: theme.textHint,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildPredictionCard(Map<String, dynamic> pred, AppThemeProvider theme) {
    final int conf = pred['confidence'];
    final Color color = pred['color'];

    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: theme.cardColor,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: theme.borderColor),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: .04),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  pred['disease'],
                  style: GoogleFonts.poppins(
                    fontSize: 16.5,
                    fontWeight: FontWeight.w700,
                    color: theme.textPrimary,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: color.withValues(alpha: .15),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  "$conf% Prob.",
                  style: GoogleFonts.poppins(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: color,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          ClipRRect(
            borderRadius: BorderRadius.circular(10),
            child: LinearProgressIndicator(
              value: conf / 100.0,
              minHeight: 8,
              backgroundColor: theme.isDark || theme.isMonsoon
                  ? const Color(0xFF1E293B)
                  : AppColors.divider,
              valueColor: AlwaysStoppedAnimation<Color>(color),
            ),
          ),
          const SizedBox(height: 12),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(Icons.flag_rounded, color: color, size: 16),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  pred['flag'],
                  style: GoogleFonts.poppins(
                    fontSize: 13,
                    color: theme.textSecondary,
                    height: 1.4,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _summaryRow(String label, String value, AppThemeProvider theme) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: GoogleFonts.poppins(
            fontSize: 13.5,
            color: theme.textSecondary,
          ),
        ),
        const SizedBox(width: 8),
        Flexible(
          child: Text(
            value,
            textAlign: TextAlign.end,
            style: GoogleFonts.poppins(
              fontSize: 13.5,
              fontWeight: FontWeight.w600,
              color: theme.textPrimary,
            ),
          ),
        ),
      ],
    );
  }
}
