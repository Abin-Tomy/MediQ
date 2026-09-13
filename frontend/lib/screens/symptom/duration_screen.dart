import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/theme/app_theme_provider.dart';
import '../../models/symptom_analysis.dart';
import 'ai_processing_screen.dart';

class DurationScreen extends StatefulWidget {
  final SymptomAnalysis analysis;

  const DurationScreen({
    super.key,
    required this.analysis,
  });

  @override
  State<DurationScreen> createState() => _DurationScreenState();
}

class _DurationScreenState extends State<DurationScreen> {
  String? selectedDuration;

  final List<Map<String, dynamic>> durations = [
    {
      "icon": Icons.today_rounded,
      "title": "Today",
      "subtitle": "Symptoms started today",
      "title_ml": "ഇന്ന്",
      "subtitle_ml": "ലക്ഷണങ്ങൾ ഇന്ന് തുടങ്ങി",
    },
    {
      "icon": Icons.nightlight_round,
      "title": "Yesterday",
      "subtitle": "Started yesterday",
      "title_ml": "ഇന്നലെ",
      "subtitle_ml": "ഇന്നലെ തുടങ്ങി",
    },
    {
      "icon": Icons.calendar_today_rounded,
      "title": "2–3 Days",
      "subtitle": "Present for a few days",
      "title_ml": "2–3 ദിവസം",
      "subtitle_ml": "കുറച്ചു ദിവസങ്ങളായി ഉണ്ട്",
    },
    {
      "icon": Icons.date_range_rounded,
      "title": "1 Week",
      "subtitle": "Around one week",
      "title_ml": "1 ആഴ്ച",
      "subtitle_ml": "ഏകദേശം ഒരാഴ്ചയായി",
    },
    {
      "icon": Icons.event_note_rounded,
      "title": "2 Weeks",
      "subtitle": "Persistent for two weeks",
      "title_ml": "2 ആഴ്ച",
      "subtitle_ml": "രണ്ടാഴ്ചയായി തുടരുന്നു",
    },
    {
      "icon": Icons.schedule_rounded,
      "title": "More than 1 Month",
      "subtitle": "Long-term symptoms",
      "title_ml": "1 മാസത്തിൽ കൂടുതൽ",
      "subtitle_ml": "ദീർഘകാലമായി തുടരുന്ന ലക്ഷണങ്ങൾ",
    },
  ];

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: AppThemeProvider(),
      builder: (context, _) {
        final theme = AppThemeProvider();

        final title = theme.tr("Duration", "കാലയളവ്");
        final heading = theme.tr("How long have you had these symptoms?", "എത്ര നാളായി ഈ ലക്ഷണങ്ങൾ ഉണ്ട്?");
        final subHeading = theme.tr(
          "Choose the option that best matches your condition.",
          "നിങ്ങളുടെ അവസ്ഥയ്ക്ക് ഏറ്റവും അനുയോജ്യമായത് തിരഞ്ഞെടുക്കുക.",
        );
        final analyzeLbl = theme.tr("Analyze Symptoms", "ലക്ഷണങ്ങൾ പരിശോധിക്കുക");

        return Scaffold(
          backgroundColor: theme.background,
          appBar: AppBar(
            elevation: 0,
            centerTitle: true,
            backgroundColor: Colors.transparent,
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
                      value: .80,
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

                  const SizedBox(height: 26),

                  Expanded(
                    child: ListView.builder(
                      itemCount: durations.length,
                      physics: const BouncingScrollPhysics(),
                      itemBuilder: (context, index) {
                        final item = durations[index];
                        final selected = selectedDuration == item["title"];

                        final itemTitle = theme.tr(item["title"], item["title_ml"]);
                        final itemSubtitle = theme.tr(item["subtitle"], item["subtitle_ml"]);

                        return Padding(
                          padding: const EdgeInsets.only(bottom: 16),
                          child: InkWell(
                            borderRadius: BorderRadius.circular(24),
                            onTap: () {
                              setState(() {
                                selectedDuration = item["title"];
                              });
                            },
                            child: AnimatedContainer(
                              duration: const Duration(milliseconds: 220),
                              padding: const EdgeInsets.all(18),
                              decoration: BoxDecoration(
                                color: selected
                                    ? theme.primaryAccent.withValues(alpha: .15)
                                    : theme.cardColor,
                                borderRadius: BorderRadius.circular(24),
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
                                  Icon(
                                    item["icon"],
                                    size: 30,
                                    color: selected
                                        ? theme.primaryAccent
                                        : theme.textPrimary,
                                  ),
                                  const SizedBox(width: 16),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          itemTitle,
                                          style: GoogleFonts.poppins(
                                            fontSize: 17,
                                            fontWeight: FontWeight.w700,
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
                      icon: const Icon(Icons.auto_awesome_rounded, size: 20),
                      label: Text(
                        analyzeLbl,
                        style: GoogleFonts.poppins(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      onPressed: selectedDuration == null
                          ? null
                          : () {
                              widget.analysis.duration = selectedDuration!;
                              Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (_) => AIProcessingScreen(
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