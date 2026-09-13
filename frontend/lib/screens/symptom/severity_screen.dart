import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/theme/app_theme_provider.dart';
import '../../models/symptom_analysis.dart';
import 'duration_screen.dart';

class SeverityScreen extends StatefulWidget {
  final SymptomAnalysis analysis;

  const SeverityScreen({
    super.key,
    required this.analysis,
  });

  @override
  State<SeverityScreen> createState() => _SeverityScreenState();
}

class _SeverityScreenState extends State<SeverityScreen> {
  String? selectedSeverity;

  final List<Map<String, String>> severityLevels = [
    {
      "emoji": "😊",
      "title": "Mild",
      "subtitle": "Slight discomfort",
      "title_ml": "ലഘുവായത്",
      "subtitle_ml": "ചെറിയ ബുദ്ധിമുട്ട്",
    },
    {
      "emoji": "😐",
      "title": "Moderate",
      "subtitle": "Pain is noticeable",
      "title_ml": "മിതമായത്",
      "subtitle_ml": "ശ്രദ്ധിക്കപ്പെടുന്ന വേദന",
    },
    {
      "emoji": "😖",
      "title": "Severe",
      "subtitle": "Difficult to perform daily activities",
      "title_ml": "കഠിനമായത്",
      "subtitle_ml": "ദൈനംദിന കാര്യങ്ങൾ ചെയ്യാൻ ബുദ്ധിമുട്ട്",
    },
    {
      "emoji": "🚨",
      "title": "Emergency",
      "subtitle": "Needs immediate medical attention",
      "title_ml": "അടിയന്തര സാഹചര്യം",
      "subtitle_ml": "ഉടൻ വൈദ്യസഹായം ആവശ്യമാണ്",
    },
  ];

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: AppThemeProvider(),
      builder: (context, _) {
        final theme = AppThemeProvider();

        final title = theme.tr("Severity", "തീവ്രത");
        final heading = theme.tr("How severe is it?", "എത്രത്തോളം കഠിനമാണ്?");
        final subHeading = theme.tr(
          "Choose the option that best describes your discomfort.",
          "നിങ്ങളുടെ ബുദ്ധിമുട്ടിന് ഏറ്റവും അനുയോജ്യമായ ഓപ്ഷൻ തിരഞ്ഞെടുക്കുക.",
        );
        final continueLbl = theme.tr("Continue", "തുടരുക");

        return Scaffold(
          backgroundColor: theme.background,
          appBar: AppBar(
            backgroundColor: Colors.transparent,
            elevation: 0,
            centerTitle: true,
            iconTheme: IconThemeData(color: theme.textPrimary),
            title: Text(
              title,
              style: GoogleFonts.poppins(
                fontWeight: FontWeight.w600,
                color: theme.textPrimary,
              ),
            ),
          ),
          body: SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  ClipRRect(
                    borderRadius: BorderRadius.circular(20),
                    child: LinearProgressIndicator(
                      value: 0.66,
                      minHeight: 7,
                      backgroundColor: theme.isDark || theme.isMonsoon
                          ? const Color(0xFF1E293B)
                          : const Color(0xFFE2E8F0),
                      valueColor: AlwaysStoppedAnimation<Color>(theme.primaryAccent),
                    ),
                  ),

                  const SizedBox(height: 24),

                  Text(
                    heading,
                    style: GoogleFonts.poppins(
                      fontSize: 26,
                      fontWeight: FontWeight.w700,
                      color: theme.textPrimary,
                    ),
                  ),

                  const SizedBox(height: 8),

                  Text(
                    subHeading,
                    style: GoogleFonts.poppins(
                      color: theme.textSecondary,
                      height: 1.4,
                      fontSize: 13.5,
                    ),
                  ),

                  const SizedBox(height: 28),

                  Expanded(
                    child: ListView.builder(
                      itemCount: severityLevels.length,
                      physics: const BouncingScrollPhysics(),
                      itemBuilder: (context, index) {
                        final item = severityLevels[index];
                        final selected = selectedSeverity == item["title"];

                        final itemTitle = theme.tr(item["title"]!, item["title_ml"]!);
                        final itemSubtitle = theme.tr(item["subtitle"]!, item["subtitle_ml"]!);

                        return Padding(
                          padding: const EdgeInsets.only(bottom: 16),
                          child: InkWell(
                            borderRadius: BorderRadius.circular(22),
                            onTap: () {
                              setState(() {
                                selectedSeverity = item["title"];
                              });
                            },
                            child: AnimatedContainer(
                              duration: const Duration(milliseconds: 250),
                              padding: const EdgeInsets.all(18),
                              decoration: BoxDecoration(
                                color: selected
                                    ? theme.primaryAccent.withValues(alpha: .15)
                                    : theme.cardColor,
                                borderRadius: BorderRadius.circular(22),
                                border: Border.all(
                                  color: selected
                                      ? theme.primaryAccent
                                      : theme.borderColor,
                                  width: selected ? 2 : 1,
                                ),
                                boxShadow: [
                                  BoxShadow(
                                    color: Colors.black.withValues(alpha: .04),
                                    blurRadius: 10,
                                    offset: const Offset(0, 4),
                                  ),
                                ],
                              ),
                              child: Row(
                                children: [
                                  Text(
                                    item["emoji"]!,
                                    style: const TextStyle(fontSize: 32),
                                  ),
                                  const SizedBox(width: 16),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          itemTitle,
                                          style: GoogleFonts.poppins(
                                            fontWeight: FontWeight.w700,
                                            fontSize: 17,
                                            color: selected
                                                ? theme.primaryAccent
                                                : theme.textPrimary,
                                          ),
                                        ),
                                        const SizedBox(height: 4),
                                        Text(
                                          itemSubtitle,
                                          style: GoogleFonts.poppins(
                                            color: theme.textSecondary,
                                            fontSize: 12.5,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                  if (selected)
                                    Icon(
                                      Icons.check_circle_rounded,
                                      color: theme.primaryAccent,
                                      size: 26,
                                    ),
                                ],
                              ),
                            ),
                          ),
                        );
                      },
                    ),
                  ),

                  const SizedBox(height: 12),

                  SizedBox(
                    width: double.infinity,
                    height: 56,
                    child: ElevatedButton.icon(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: theme.primaryAccent,
                        foregroundColor: Colors.white,
                        disabledBackgroundColor: theme.borderColor,
                        elevation: 0,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(18),
                        ),
                      ),
                      icon: const Icon(Icons.arrow_forward_rounded, size: 20),
                      label: Text(
                        continueLbl,
                        style: GoogleFonts.poppins(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      onPressed: selectedSeverity == null
                          ? null
                          : () {
                              widget.analysis.severity = selectedSeverity!;
                              Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (_) => DurationScreen(
                                    analysis: widget.analysis,
                                  ),
                                ),
                              );
                            },
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
}