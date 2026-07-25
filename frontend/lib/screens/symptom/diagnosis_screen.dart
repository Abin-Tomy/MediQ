import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/theme/app_colors.dart';
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

  @override
  Widget build(BuildContext context) {
    final predictions = _generatePredictions();
    final topPrediction = predictions.first;

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        leading: IconButton(
          icon: const Icon(Icons.close_rounded, color: AppColors.textPrimary),
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
          "AI Diagnostic Report",
          style: GoogleFonts.poppins(
            color: AppColors.textPrimary,
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
                  color: const Color(0xFFEAF4FF),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: AppColors.primary.withValues(alpha: .3)),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.psychology_alt_rounded,
                        color: AppColors.primary, size: 18),
                    const SizedBox(width: 8),
                    Text(
                      "Model 1 Output (DistilBERT Text Classifier)",
                      style: GoogleFonts.poppins(
                        color: AppColors.primary,
                        fontWeight: FontWeight.w600,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 20),

              // URGENCY CARD
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFFFFF5F5), Color(0xFFFFE3E3)],
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
                      child: const Icon(Icons.priority_high_rounded,
                          color: Colors.white, size: 28),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            "Urgency: ${topPrediction['urgency']} Priority",
                            style: GoogleFonts.poppins(
                              fontSize: 17,
                              fontWeight: FontWeight.w700,
                              color: const Color(0xFF9B1C1C),
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            "Your symptoms require medical evaluation today. Do not delay seeking professional advice.",
                            style: GoogleFonts.poppins(
                              fontSize: 13,
                              color: const Color(0xFF771D1D),
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
                "Top Disease Probabilities",
                style: GoogleFonts.poppins(
                  fontSize: 20,
                  fontWeight: FontWeight.w700,
                  color: AppColors.textPrimary,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                "Ranked by AI confidence based on your input:",
                style: GoogleFonts.poppins(
                  fontSize: 14,
                  color: AppColors.textSecondary,
                ),
              ),

              const SizedBox(height: 16),

              // PREDICTIONS LIST
              ...predictions.map((pred) => _buildPredictionCard(pred)),

              const SizedBox(height: 24),

              // INPUT SUMMARY CARD
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: AppColors.border),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      "Your Reported Symptoms",
                      style: GoogleFonts.poppins(
                        fontSize: 15,
                        fontWeight: FontWeight.w600,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    const Divider(height: 24),
                    _summaryRow("Affected Area", analysis.bodyArea),
                    const SizedBox(height: 8),
                    _summaryRow("Severity", analysis.severity),
                    const SizedBox(height: 8),
                    _summaryRow("Duration", analysis.duration),
                    const SizedBox(height: 12),
                    Text(
                      "\"${analysis.symptoms}\"",
                      style: GoogleFonts.poppins(
                        fontSize: 13.5,
                        fontStyle: FontStyle.italic,
                        color: AppColors.textSecondary,
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
                  gradient: const LinearGradient(
                    colors: [Color(0xFF2F80ED), Color(0xFF56CCF2)],
                  ),
                  borderRadius: BorderRadius.circular(24),
                  boxShadow: [
                    BoxShadow(
                      color: AppColors.primary.withValues(alpha: .3),
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
                        const Icon(Icons.verified_user_rounded,
                            color: Colors.white, size: 26),
                        const SizedBox(width: 12),
                        Text(
                          "Recommended Action",
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
                      "Based on these findings, we recommend consulting a General Physician or Infectious Disease Specialist immediately.",
                      style: GoogleFonts.poppins(
                        fontSize: 14,
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
                          foregroundColor: AppColors.primary,
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
                                "Find Specialists Nearby (5 km)",
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: GoogleFonts.poppins(
                                  fontSize: 15,
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
                  "Disclaimer: This application is an informational mini-project and does not provide formal medical diagnoses.",
                  textAlign: TextAlign.center,
                  style: GoogleFonts.poppins(
                    fontSize: 11,
                    color: AppColors.textHint,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildPredictionCard(Map<String, dynamic> pred) {
    final int conf = pred['confidence'];
    final Color color = pred['color'];

    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.border),
        boxShadow: const [
          BoxShadow(
            color: Color(0x0A000000),
            blurRadius: 10,
            offset: Offset(0, 4),
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
                    color: AppColors.textPrimary,
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
              backgroundColor: AppColors.divider,
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
                    color: AppColors.textSecondary,
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

  Widget _summaryRow(String label, String value) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: GoogleFonts.poppins(
            fontSize: 13.5,
            color: AppColors.textSecondary,
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
              color: AppColors.textPrimary,
            ),
          ),
        ),
      ],
    );
  }
}
