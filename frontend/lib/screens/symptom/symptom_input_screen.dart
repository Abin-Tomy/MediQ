import 'dart:async';
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/theme/app_theme_provider.dart';
import '../../models/symptom_analysis.dart';
import 'severity_screen.dart';

class SymptomInputScreen extends StatefulWidget {
  final SymptomAnalysis analysis;

  const SymptomInputScreen({
    super.key,
    required this.analysis,
  });

  @override
  State<SymptomInputScreen> createState() => _SymptomInputScreenState();
}

class _SymptomInputScreenState extends State<SymptomInputScreen>
    with SingleTickerProviderStateMixin {
  final TextEditingController _controller = TextEditingController();
  bool _isListening = false;
  late AnimationController _waveController;
  Timer? _listeningTimer;

  @override
  void initState() {
    super.initState();
    _controller.addListener(() {
      setState(() {});
    });

    _waveController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    )..repeat();
  }

  @override
  void dispose() {
    _waveController.dispose();
    _listeningTimer?.cancel();
    _controller.dispose();
    super.dispose();
  }

  bool get canContinue => _controller.text.trim().isNotEmpty;

  void _toggleListening(AppThemeProvider theme) {
    if (_isListening) {
      _stopListening();
    } else {
      setState(() {
        _isListening = true;
      });
      // Simulate speech recognition for 3.5 seconds
      _listeningTimer = Timer(const Duration(milliseconds: 3500), () {
        if (mounted && _isListening) {
          _stopListening(autoPopulate: true, theme: theme);
        }
      });
    }
  }

  void _stopListening({bool autoPopulate = false, AppThemeProvider? theme}) {
    _listeningTimer?.cancel();
    setState(() {
      _isListening = false;
    });

    if (autoPopulate && theme != null) {
      String sampleText;
      final area = widget.analysis.bodyArea.toLowerCase();
      if (theme.isMalayalam) {
        if (area.contains('head') || area.contains('തല')) {
          sampleText = "കഠിനമായ തലവേദനയും ചെറിയ പനിയും അനുഭവപ്പെടുന്നു, കണ്ണുകൾക്ക് വേദനയുണ്ട്.";
        } else if (area.contains('chest') || area.contains('നെഞ്ച്')) {
          sampleText = "നെഞ്ചുവേദനയും ശ്വാസമെടുക്കാൻ ചെറിയ ബുദ്ധിമുട്ടും അനുഭവപ്പെടുന്നു.";
        } else if (area.contains('abdomen') || area.contains('വയർ')) {
          sampleText = "വയറുവേദനയും ഛർദ്ദിയും അനുഭവപ്പെടുന്നു, ഇന്നലെ മുതൽ ചെറിയ പനിയും ഉണ്ട്.";
        } else {
          sampleText = "കഠിനമായ ശരീരവേദനയും പനിയും ക്ഷീണവും അനുഭവപ്പെടുന്നു.";
        }
      } else {
        if (area.contains('head')) {
          sampleText = "Severe throbbing headache, mild fever since yesterday, and dizziness when standing up.";
        } else if (area.contains('chest')) {
          sampleText = "Sharp chest tightness when breathing deeply, accompanied by dry cough and fatigue.";
        } else if (area.contains('abdomen')) {
          sampleText = "Severe abdominal cramping, nausea since yesterday morning, and mild fever.";
        } else {
          sampleText = "Continuous body aches, high fever (38.8 C), extreme tiredness, and joint pain.";
        }
      }

      if (_controller.text.isEmpty) {
        _controller.text = sampleText;
      } else {
        _controller.text = "${_controller.text.trim()} • $sampleText";
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: AppThemeProvider(),
      builder: (context, _) {
        final theme = AppThemeProvider();

        final title = theme.tr("Describe Symptoms", "ലക്ഷണങ്ങൾ വിവരിക്കുക");
        final affectedAreaLbl = theme.tr("Affected Area", "ബാധിച്ച ഭാഗം");
        final heading = theme.tr("What are you experiencing?", "എന്തൊക്കെയാണ് ബുദ്ധിമുട്ടുകൾ?");
        final subHeading = theme.tr(
          "Tell the AI in your own words or use the voice assistant below.\nThe more details you provide, the better the prediction.",
          "നിങ്ങളുടെ സ്വന്തം വാക്കുകളിൽ എഴുതുകയോ താഴെയുള്ള വോയ്സ് അസിസ്റ്റന്റ് ഉപയോഗിക്കുകയോ ചെയ്യുക.",
        );
        final hint = theme.tr(
          "Example:\n\n• Sharp pain while walking\n• Swelling since yesterday\n• Burning sensation\n• Fever with chills",
          "ഉദാഹരണത്തിന്:\n\n• നടക്കുമ്പോൾ കഠിനമായ വേദന\n• ഇന്നലെ മുതൽ നീർക്കെട്ട്\n• പനിയും വിറയലും",
        );
        final looksGoodLbl = theme.tr("✓ Looks good", "✓ മികച്ച വിവരണം");
        final pleaseDescribeLbl = theme.tr("Please describe your symptoms", "ലക്ഷണങ്ങൾ എഴുതുക അല്ലെങ്കിൽ പറയുക");
        final continueLbl = theme.tr("Continue to Severity", "തുടരുക");
        final speakBtnLbl = _isListening
            ? theme.tr("Listening... Tap to stop", "കേൾക്കുന്നു... നിർത്താൻ തൊടുക")
            : theme.tr("🎙️ Speak Your Symptoms (AI Voice)", "🎙️ ലക്ഷണങ്ങൾ പറയുക (വോയ്സ്)");

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
                  // AFFECTED AREA PILL
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    decoration: BoxDecoration(
                      color: theme.isDark || theme.isMonsoon
                          ? const Color(0xFF1E293B)
                          : const Color(0xFFEAF4FF),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: theme.primaryAccent.withValues(alpha: .3)),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.place_rounded, color: theme.primaryAccent),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            "$affectedAreaLbl : ${widget.analysis.bodyArea}",
                            style: GoogleFonts.poppins(
                              color: theme.primaryAccent,
                              fontWeight: FontWeight.w700,
                              fontSize: 15,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 24),

                  Text(
                    heading,
                    style: GoogleFonts.poppins(
                      fontSize: 24,
                      fontWeight: FontWeight.w700,
                      color: theme.textPrimary,
                    ),
                  ),

                  const SizedBox(height: 6),

                  Text(
                    subHeading,
                    style: GoogleFonts.poppins(
                      color: theme.textSecondary,
                      fontSize: 13,
                      height: 1.4,
                    ),
                  ),

                  const SizedBox(height: 18),

                  // VOICE ASSISTANT BAR
                  GestureDetector(
                    onTap: () => _toggleListening(theme),
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 300),
                      width: double.infinity,
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      decoration: BoxDecoration(
                        color: _isListening
                            ? const Color(0xFFEF4444).withValues(alpha: .15)
                            : (theme.isDark || theme.isMonsoon
                                ? const Color(0xFF131B2E)
                                : const Color(0xFFF1F5F9)),
                        borderRadius: BorderRadius.circular(18),
                        border: Border.all(
                          color: _isListening
                              ? const Color(0xFFEF4444)
                              : theme.primaryAccent.withValues(alpha: .4),
                          width: _isListening ? 2 : 1,
                        ),
                      ),
                      child: Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: _isListening ? const Color(0xFFEF4444) : theme.primaryAccent,
                              shape: BoxShape.circle,
                            ),
                            child: Icon(
                              _isListening ? Icons.mic_rounded : Icons.mic_none_rounded,
                              color: Colors.white,
                              size: 20,
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Text(
                              speakBtnLbl,
                              style: GoogleFonts.poppins(
                                fontSize: 13,
                                fontWeight: _isListening ? FontWeight.w700 : FontWeight.w600,
                                color: _isListening
                                    ? const Color(0xFFEF4444)
                                    : theme.textPrimary,
                              ),
                            ),
                          ),
                          if (_isListening)
                            SizedBox(
                              width: 60,
                              height: 24,
                              child: _VoiceWaveform(controller: _waveController),
                            ),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 16),

                  // TEXT FIELD
                  Expanded(
                    child: Container(
                      decoration: BoxDecoration(
                        color: theme.cardColor,
                        borderRadius: BorderRadius.circular(22),
                        border: Border.all(
                          color: canContinue ? theme.primaryAccent : theme.borderColor,
                          width: canContinue ? 1.5 : 1,
                        ),
                      ),
                      child: TextField(
                        controller: _controller,
                        expands: true,
                        maxLines: null,
                        textAlignVertical: TextAlignVertical.top,
                        style: GoogleFonts.poppins(color: theme.textPrimary, fontSize: 14.5),
                        decoration: InputDecoration(
                          border: InputBorder.none,
                          contentPadding: const EdgeInsets.all(20),
                          hintText: hint,
                          hintStyle: GoogleFonts.poppins(color: theme.textHint, fontSize: 13.5),
                        ),
                      ),
                    ),
                  ),

                  const SizedBox(height: 12),

                  // STATUS ROW
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        canContinue ? looksGoodLbl : pleaseDescribeLbl,
                        style: GoogleFonts.poppins(
                          color: canContinue ? const Color(0xFF10B981) : theme.textSecondary,
                          fontWeight: FontWeight.w600,
                          fontSize: 12.5,
                        ),
                      ),
                      Text(
                        "${_controller.text.length}/500",
                        style: GoogleFonts.poppins(color: theme.textSecondary, fontSize: 12),
                      ),
                    ],
                  ),

                  const SizedBox(height: 18),

                  // CONTINUE BUTTON
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
                      onPressed: canContinue
                          ? () {
                              widget.analysis.symptoms = _controller.text.trim();
                              Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (_) => SeverityScreen(
                                    analysis: widget.analysis,
                                  ),
                                ),
                              );
                            }
                          : null,
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

class _VoiceWaveform extends StatelessWidget {
  final AnimationController controller;
  const _VoiceWaveform({required this.controller});

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: controller,
      builder: (context, _) {
        return Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: List.generate(5, (index) {
            final sinValue = math.sin((controller.value * 2 * math.pi) + (index * 0.8));
            final height = 6 + ((sinValue + 1) / 2) * 16;
            return Container(
              width: 3.5,
              height: height,
              decoration: BoxDecoration(
                color: const Color(0xFFEF4444),
                borderRadius: BorderRadius.circular(4),
              ),
            );
          }),
        );
      },
    );
  }
}