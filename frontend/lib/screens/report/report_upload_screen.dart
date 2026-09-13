import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/theme/app_theme_provider.dart';
import '../doctor/doctor_list_screen.dart';
import 'widgets/vital_trend_chart.dart';

class ReportUploadScreen extends StatefulWidget {
  const ReportUploadScreen({super.key});

  @override
  State<ReportUploadScreen> createState() => _ReportUploadScreenState();
}

class _ReportUploadScreenState extends State<ReportUploadScreen>
    with TickerProviderStateMixin {
  bool _isProcessing = false;
  bool _hasSummary = false;
  String _selectedReport = "Blood Test (Kozhikode Diagnostic Lab).pdf";
  int _processStep = 0;

  late AnimationController _shimmerController;

  final Map<String, Map<String, dynamic>> _reportData = {
    "Blood Test (Kozhikode Diagnostic Lab).pdf": {
      "title": "Complete Blood Count (CBC) - Diagnostic Lab",
      "title_ml": "പൂർണ്ണ രക്തപരിശോധന (സി.ബി.സി) - കോഴിക്കോട് ലാബ്",
      "date": "24 Jul 2026",
      "model": "T5-small (fine-tuned on PubMed 200k RCT)",
      "extraction": "PyMuPDF (fitz) text extraction engine",
      "metrics": [
        {
          "name": "Platelet Count",
          "name_ml": "പ്ലേറ്റ്‌ലെറ്റ് കൗണ്ട്",
          "value": "91,000 /mcL",
          "normal": "150,000 - 450,000",
          "status": "Critical Low",
          "status_ml": "അപകടനിലയിൽ",
          "color": const Color(0xFFEB5757),
        },
        {
          "name": "Hemoglobin",
          "name_ml": "ഹീമോഗ്ലോബിൻ",
          "value": "12.4 g/dL",
          "normal": "12.0 - 15.5",
          "status": "Normal",
          "status_ml": "സാധാരണ",
          "color": const Color(0xFF27AE60),
        },
        {
          "name": "Total WBC Count",
          "name_ml": "ശ്വേതരക്താണുക്കൾ (WBC)",
          "value": "3,800 /mcL",
          "normal": "4,000 - 11,000",
          "status": "Borderline Low",
          "status_ml": "കുറവ്",
          "color": const Color(0xFFF2994A),
        },
      ],
      "plainText":
          "Your platelet count of 91,000 is significantly below the normal threshold of 150,000. In endemic regions like Kozhikode during monsoon, a dropping platelet count combined with fever or rash strongly correlates with Dengue fever or Leptospirosis progression. This clinical picture requires professional medical evaluation today.",
      "plainText_ml":
          "നിങ്ങളുടെ പ്ലേറ്റ്‌ലെറ്റ് കൗണ്ട് (91,000) സാധാരണ അളവായ 150,000-ലും താഴെയാണ്. കോഴിക്കോട് പോലുള്ള പ്രദേശങ്ങളിൽ മൺസൂൺ കാലത്ത് പ്ലേറ്റ്‌ലെറ്റ് കുറയുന്നത് ഡെങ്കിപ്പനി അല്ലെങ്കിൽ എലിപ്പനി എന്നിവയുടെ ലക്ഷണമവാം. ഇന്ന് തന്നെ വിദഗ്ധ ഡോക്ടറുടെ സേവനം തേടുക.",
      "urgency": "High Urgency — Doctor Visit Required Today",
      "urgency_ml": "അതിതീവ്ര മുൻഗണന — ഇന്ന് തന്നെ ഡോക്ടറെ കാണുക",
      "urgencyColor": const Color(0xFFEB5757),
      "urgencyBg": const Color(0xFFFFE3E3),
    },
    "Complete Blood Count (CBC - Routine).pdf": {
      "title": "Annual Routine Blood Test",
      "title_ml": "വാർഷിക പതിവ് രക്തപരിശോധന",
      "date": "15 Jul 2026",
      "model": "T5-small (fine-tuned on PubMed 200k RCT)",
      "extraction": "PyMuPDF (fitz) text extraction engine",
      "metrics": [
        {
          "name": "Platelet Count",
          "name_ml": "പ്ലേറ്റ്‌ലെറ്റ് കൗണ്ട്",
          "value": "245,000 /mcL",
          "normal": "150,000 - 450,000",
          "status": "Normal",
          "status_ml": "സാധാരണ",
          "color": const Color(0xFF27AE60),
        },
        {
          "name": "Hemoglobin",
          "name_ml": "ഹീമോഗ്ലോബിൻ",
          "value": "13.8 g/dL",
          "normal": "12.0 - 15.5",
          "status": "Normal",
          "status_ml": "സാധാരണ",
          "color": const Color(0xFF27AE60),
        },
        {
          "name": "Total WBC Count",
          "name_ml": "ശ്വേതരക്താണുക്കൾ (WBC)",
          "value": "6,500 /mcL",
          "normal": "4,000 - 11,000",
          "status": "Normal",
          "status_ml": "സാധാരണ",
          "color": const Color(0xFF27AE60),
        },
      ],
      "plainText":
          "All primary hematology indicators including platelets, white blood cells, and hemoglobin are within healthy standard ranges. No acute hematological infection or abnormality detected in this sample.",
      "plainText_ml":
          "പ്ലേറ്റ്‌ലെറ്റുകൾ, ശ്വേതരക്താണുക്കൾ, ഹീമോഗ്ലോബിൻ എന്നിവയുൾപ്പെടെയുള്ള എല്ലാ പ്രധാന രക്തഘടകങ്ങളും ആരോഗ്യകരമായ സാധാരണ പരിധിക്കുള്ളിലാണ്. അണുബാധകളോ മറ്റ് പ്രശ്നങ്ങളോ ഇല്ല.",
      "urgency": "Normal — Routine Health Maintained",
      "urgency_ml": "സാധാരണ നില — ആരോഗ്യനില തൃപ്തികരമാണ്",
      "urgencyColor": const Color(0xFF2F80ED),
      "urgencyBg": const Color(0xFFE1EFFE),
    },
    "Liver Function Test (LFT - Mild SGPT).pdf": {
      "title": "Hepatic Function Panel",
      "title_ml": "കരൾ പ്രവർത്തന പരിശോധന",
      "date": "10 Jul 2026",
      "model": "T5-small (fine-tuned on PubMed 200k RCT)",
      "extraction": "PyMuPDF (fitz) text extraction engine",
      "metrics": [
        {
          "name": "SGPT / ALT",
          "name_ml": "SGPT / ALT",
          "value": "78 U/L",
          "normal": "7 - 56",
          "status": "Elevated",
          "status_ml": "വർദ്ധിച്ചു",
          "color": const Color(0xFFF2994A),
        },
        {
          "name": "SGOT / AST",
          "name_ml": "SGOT / AST",
          "value": "45 U/L",
          "normal": "10 - 40",
          "status": "Mildly High",
          "status_ml": "അല്പം കൂടുതൽ",
          "color": const Color(0xFFF2994A),
        },
        {
          "name": "Total Bilirubin",
          "name_ml": "ടോട്ടൽ ബിലിറൂബിൻ",
          "value": "0.9 mg/dL",
          "normal": "0.1 - 1.2",
          "status": "Normal",
          "status_ml": "സാധാരണ",
          "color": const Color(0xFF27AE60),
        },
      ],
      "plainText":
          "Your liver enzymes (SGPT/ALT and SGOT/AST) show mild elevation above standard limits. This indicates minor hepatic stress or inflammation, often related to recent medication, diet, or resolving viral infection. A follow-up consultation with a General Physician is recommended.",
      "plainText_ml":
          "നിങ്ങളുടെ കരൾ എൻസൈമുകൾ (SGPT/ALT, SGOT/AST) സാധാരണ പരിധിയേക്കാൾ അല്പം കൂടുതലാണ്. ഇത് കരളിലുണ്ടാകുന്ന ചെറിയ സമ്മർദ്ദം അല്ലെങ്കിൽ വീക്കം സൂചിപ്പിക്കുന്നു. ജനറൽ ഫിസിഷ്യനെ കണ്ട് തുടർപരിശോധന നടത്താൻ ശുപാർശ ചെയ്യുന്നു.",
      "urgency": "Medium Urgency — Schedule Follow-up",
      "urgency_ml": "ഇടത്തരം മുൻഗണന — ഡോക്ടറുടെ സമയം ബുക്ക് ചെയ്യുക",
      "urgencyColor": const Color(0xFFF2994A),
      "urgencyBg": const Color(0xFFFEF3C7),
    },
  };

  @override
  void initState() {
    super.initState();
    _shimmerController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1400),
    )..repeat();
  }

  @override
  void dispose() {
    _shimmerController.dispose();
    super.dispose();
  }

  void _startProcessing() async {
    setState(() {
      _isProcessing = true;
      _hasSummary = false;
      _processStep = 1;
    });

    await Future.delayed(const Duration(milliseconds: 900));
    if (!mounted) return;
    setState(() => _processStep = 2);

    await Future.delayed(const Duration(milliseconds: 900));
    if (!mounted) return;
    setState(() => _processStep = 3);

    await Future.delayed(const Duration(milliseconds: 900));
    if (!mounted) return;
    setState(() {
      _isProcessing = false;
      _hasSummary = true;
    });
  }

  Widget _buildShimmerBox(double height, double width, AppThemeProvider theme, {double radius = 16}) {
    return AnimatedBuilder(
      animation: _shimmerController,
      builder: (context, _) {
        return Container(
          height: height,
          width: width,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(radius),
            gradient: LinearGradient(
              begin: Alignment(-1.0 + (_shimmerController.value * 2.0), 0.0),
              end: Alignment(0.0 + (_shimmerController.value * 2.0), 0.0),
              colors: theme.isDark || theme.isMonsoon
                  ? [
                      const Color(0xFF1E293B),
                      const Color(0xFF334155),
                      const Color(0xFF1E293B),
                    ]
                  : [
                      const Color(0xFFE2E8F0),
                      const Color(0xFFF1F5F9),
                      const Color(0xFFE2E8F0),
                    ],
              stops: const [0.1, 0.5, 0.9],
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: AppThemeProvider(),
      builder: (context, _) {
        final theme = AppThemeProvider();
        final currentReport = _reportData[_selectedReport]!;
        final List<Map<String, dynamic>> metrics =
            (currentReport['metrics'] as List).cast<Map<String, dynamic>>();

        final appBarTitle = theme.tr("Medical Report Summarizer", "മെഡിക്കൽ റിപ്പോർട്ട് വിശകലനം");
        final pageTitle = theme.tr("AI Lab Report Translation", "AI ലാബ് റിപ്പോർട്ട് വിവർത്തനം");
        final pageDesc = theme.tr(
          "Upload blood tests or diagnostic lab PDFs. PyMuPDF extracts the raw clinical text, and T5-small converts complex medical metrics into plain language.",
          "രക്തപരിശോധനാ റിപ്പോർട്ടുകളോ ലാബ് ഫലങ്ങളോ അപ്‌ലോഡ് ചെയ്യുക. സങ്കീർണ്ണമായ മെഡിക്കൽ വിവരങ്ങൾ ലളിതമായ ഭാഷയിൽ AI വിശദീകരിച്ചു തരും.",
        );
        final selectPdfLbl = theme.tr("Select Lab Report PDF", "ലാബ് റിപ്പോർട്ട് PDF തിരഞ്ഞെടുക്കുക");
        final readyLbl = theme.tr("Simulated PyMuPDF extraction ready", "PyMuPDF പരിശോധനയ്ക്ക് സജ്ജമാണ്");
        final btnLbl = _isProcessing
            ? theme.tr("Processing Report...", "പരിശോധിച്ചുകൊണ്ടിരിക്കുന്നു...")
            : theme.tr("Summarize Report with T5-small", "T5-small ഉപയോഗിച്ച് പരിശോധിക്കുക");
        final step1Lbl = theme.tr("Extracting text from PDF (PyMuPDF / fitz)", "PDF-ൽ നിന്ന് വിവരങ്ങൾ ശേഖരിക്കുന്നു");
        final step2Lbl = theme.tr("Parsing hematology clinical values", "രക്തപരിശോധനാ ഫലങ്ങൾ തരംതിരിക്കുന്നു");
        final step3Lbl = theme.tr("Generating plain language summary (T5-small)", "ലളിതമായ വിശദീകരണം തയ്യാറാക്കുന്നു");

        final summaryHeading = theme.tr("Plain Language Summary", "ലളിതമായ വിശദീകരണം");
        final tableHeading = theme.tr("Extracted Clinical Values Table", "കണ്ടെത്തിയ പരിശോധനാ ഫലങ്ങൾ");
        final bookDoctorLbl = theme.tr("Book Doctor Appointment (Within 5 km)", "അടുത്തുള്ള ഡോക്ടറെ ബുക്ക് ചെയ്യുക (5 കി.മീ ഉള്ളിൽ)");

        final urgencyText = theme.tr(currentReport['urgency'] as String, currentReport['urgency_ml'] as String);
        final plainText = theme.tr(currentReport['plainText'] as String, currentReport['plainText_ml'] as String);

        return Scaffold(
          backgroundColor: theme.background,
          appBar: AppBar(
            backgroundColor: Colors.transparent,
            elevation: 0,
            centerTitle: true,
            iconTheme: IconThemeData(color: theme.textPrimary),
            title: Text(
              appBarTitle,
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
                  // MODEL BADGE
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                    decoration: BoxDecoration(
                      color: const Color(0xFF10B981).withValues(alpha: .12),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: const Color(0xFF10B981).withValues(alpha: .3)),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.description_rounded,
                            color: Color(0xFF10B981), size: 18),
                        const SizedBox(width: 8),
                        Text(
                          "Model 3 Output (T5-small NLP Summarizer)",
                          style: GoogleFonts.poppins(
                            color: const Color(0xFF10B981),
                            fontWeight: FontWeight.w600,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 20),

                  Text(
                    pageTitle,
                    style: GoogleFonts.poppins(
                      fontSize: 24,
                      fontWeight: FontWeight.w700,
                      color: theme.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    pageDesc,
                    style: GoogleFonts.poppins(
                      fontSize: 13.5,
                      color: theme.textSecondary,
                      height: 1.5,
                    ),
                  ),

                  const SizedBox(height: 22),

                  // PRESET SELECTOR / FILE UPLOAD BOX
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: theme.cardColor,
                      borderRadius: BorderRadius.circular(24),
                      border: Border.all(
                        color: theme.primaryAccent.withValues(alpha: .4),
                        width: 1.5,
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: .05),
                          blurRadius: 15,
                          offset: const Offset(0, 5),
                        ),
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                color: theme.primaryAccent.withValues(alpha: .15),
                                borderRadius: BorderRadius.circular(16),
                              ),
                              child: Icon(Icons.upload_file_rounded,
                                  color: theme.primaryAccent, size: 28),
                            ),
                            const SizedBox(width: 14),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    selectPdfLbl,
                                    style: GoogleFonts.poppins(
                                      fontSize: 16,
                                      fontWeight: FontWeight.w700,
                                      color: theme.textPrimary,
                                    ),
                                  ),
                                  Text(
                                    readyLbl,
                                    style: GoogleFonts.poppins(
                                      fontSize: 12,
                                      color: theme.textSecondary,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 18),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 14),
                          decoration: BoxDecoration(
                            color: theme.background,
                            borderRadius: BorderRadius.circular(14),
                            border: Border.all(color: theme.borderColor),
                          ),
                          child: DropdownButtonHideUnderline(
                            child: DropdownButton<String>(
                              value: _selectedReport,
                              isExpanded: true,
                              dropdownColor: theme.cardColor,
                              icon: Icon(Icons.keyboard_arrow_down_rounded, color: theme.textPrimary),
                              onChanged: (val) {
                                if (val != null) {
                                  setState(() {
                                    _selectedReport = val;
                                    _hasSummary = false;
                                  });
                                }
                              },
                              items: _reportData.keys.map((key) {
                                final r = _reportData[key]!;
                                final t = theme.tr(r["title"] as String, r["title_ml"] as String);
                                return DropdownMenuItem<String>(
                                  value: key,
                                  child: Text(
                                    t,
                                    style: GoogleFonts.poppins(
                                      fontSize: 13,
                                      fontWeight: FontWeight.w500,
                                      color: theme.textPrimary,
                                    ),
                                  ),
                                );
                              }).toList(),
                            ),
                          ),
                        ),
                        const SizedBox(height: 18),
                        SizedBox(
                          width: double.infinity,
                          height: 52,
                          child: ElevatedButton.icon(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: theme.primaryAccent,
                              foregroundColor: Colors.white,
                              disabledBackgroundColor: theme.borderColor,
                              elevation: 0,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(16),
                              ),
                            ),
                            onPressed: _isProcessing ? null : _startProcessing,
                            icon: _isProcessing
                                ? const SizedBox(
                                    width: 20,
                                    height: 20,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2.2,
                                      color: Colors.white,
                                    ),
                                  )
                                : const Icon(Icons.auto_awesome_rounded, size: 20),
                            label: Text(
                              btnLbl,
                              style: GoogleFonts.poppins(
                                fontSize: 15,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),

                  // PROCESSING STEPS & SHIMMER PREVIEW
                  if (_isProcessing) ...[
                    const SizedBox(height: 28),
                    Container(
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        color: theme.cardColor,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: theme.borderColor),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          _buildStepRow(1, step1Lbl, _processStep >= 1, theme),
                          const SizedBox(height: 14),
                          _buildStepRow(2, step2Lbl, _processStep >= 2, theme),
                          const SizedBox(height: 14),
                          _buildStepRow(3, step3Lbl, _processStep >= 3, theme),
                          const SizedBox(height: 24),
                          Divider(color: theme.borderColor, height: 1),
                          const SizedBox(height: 18),
                          Text(
                            theme.tr("Extracting Clinical Data...", "വിവരങ്ങൾ ശേഖരിച്ചുകൊണ്ടിരിക്കുന്നു..."),
                            style: GoogleFonts.poppins(
                              fontSize: 13,
                              fontWeight: FontWeight.w600,
                              color: theme.textSecondary,
                            ),
                          ),
                          const SizedBox(height: 14),
                          _buildShimmerBox(60, double.infinity, theme),
                          const SizedBox(height: 12),
                          _buildShimmerBox(120, double.infinity, theme),
                        ],
                      ),
                    ),
                  ],

                  // RESULTS SECTION
                  if (_hasSummary) ...[
                    const SizedBox(height: 30),

                    // URGENCY BANNER
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: theme.isDark || theme.isMonsoon
                            ? (currentReport['urgencyColor'] as Color).withValues(alpha: .2)
                            : (currentReport['urgencyBg'] as Color),
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(
                          color: (currentReport['urgencyColor'] as Color).withValues(alpha: .4),
                        ),
                      ),
                      child: Row(
                        children: [
                          Icon(
                            Icons.medical_services_rounded,
                            color: currentReport['urgencyColor'] as Color,
                            size: 24,
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Text(
                              urgencyText,
                              style: GoogleFonts.poppins(
                                fontSize: 14,
                                fontWeight: FontWeight.w700,
                                color: currentReport['urgencyColor'] as Color,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 24),

                    // PLAIN LANGUAGE SUMMARY
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(22),
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: theme.isDark || theme.isMonsoon
                              ? [const Color(0xFF1E293B), const Color(0xFF0F172A)]
                              : [const Color(0xFFEFF6FF), const Color(0xFFDBEAFE)],
                        ),
                        borderRadius: BorderRadius.circular(24),
                        border: Border.all(
                          color: theme.primaryAccent.withValues(alpha: .4),
                        ),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(Icons.translate_rounded,
                                  color: theme.primaryAccent, size: 24),
                              const SizedBox(width: 10),
                              Text(
                                summaryHeading,
                                style: GoogleFonts.poppins(
                                  fontSize: 17,
                                  fontWeight: FontWeight.w700,
                                  color: theme.textPrimary,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          Text(
                            plainText,
                            style: GoogleFonts.poppins(
                              fontSize: 14.5,
                              color: theme.textPrimary,
                              height: 1.6,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 28),

                    // VITAL TREND ANALYTICS CHART WIDGET
                    const VitalTrendChart(),

                    const SizedBox(height: 28),

                    // EXTRACTED CLINICAL VALUES TABLE
                    Text(
                      tableHeading,
                      style: GoogleFonts.poppins(
                        fontSize: 18,
                        fontWeight: FontWeight.w700,
                        color: theme.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 12),

                    Container(
                      decoration: BoxDecoration(
                        color: theme.cardColor,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: theme.borderColor),
                      ),
                      child: ListView.separated(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        itemCount: metrics.length,
                        separatorBuilder: (context, index) => Divider(height: 1, color: theme.borderColor),
                        itemBuilder: (_, idx) {
                          final m = metrics[idx];
                          final Color col = m['color'] as Color;
                          final mName = theme.tr(m['name'] as String, m['name_ml'] as String);
                          final mStatus = theme.tr(m['status'] as String, m['status_ml'] as String);

                          return Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Expanded(
                                  flex: 3,
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        mName,
                                        style: GoogleFonts.poppins(
                                          fontSize: 15,
                                          fontWeight: FontWeight.w600,
                                          color: theme.textPrimary,
                                        ),
                                      ),
                                      Text(
                                        "${theme.tr('Normal', 'സാധാരണ')}: ${m['normal']}",
                                        style: GoogleFonts.poppins(
                                          fontSize: 12,
                                          color: theme.textSecondary,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                Expanded(
                                  flex: 2,
                                  child: Text(
                                    m['value'] as String,
                                    style: GoogleFonts.poppins(
                                      fontSize: 15,
                                      fontWeight: FontWeight.w700,
                                      color: theme.textPrimary,
                                    ),
                                  ),
                                ),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: col.withValues(alpha: .15),
                                    borderRadius: BorderRadius.circular(10),
                                  ),
                                  child: Text(
                                    mStatus,
                                    style: GoogleFonts.poppins(
                                      fontSize: 12,
                                      fontWeight: FontWeight.w700,
                                      color: col,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          );
                        },
                      ),
                    ),

                    const SizedBox(height: 28),

                    // BOOK DOCTOR CTA
                    SizedBox(
                      width: double.infinity,
                      height: 56,
                      child: ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF10B981),
                          foregroundColor: Colors.white,
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
                        icon: const Icon(Icons.calendar_today_rounded),
                        label: Text(
                          bookDoctorLbl,
                          style: GoogleFonts.poppins(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildStepRow(int stepNum, String text, bool isDone, AppThemeProvider theme) {
    return Row(
      children: [
        Icon(
          isDone ? Icons.check_circle_rounded : Icons.radio_button_unchecked_rounded,
          color: isDone ? const Color(0xFF10B981) : theme.textHint,
          size: 22,
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Text(
            text,
            style: GoogleFonts.poppins(
              fontSize: 14,
              fontWeight: isDone ? FontWeight.w600 : FontWeight.w400,
              color: isDone ? theme.textPrimary : theme.textSecondary,
            ),
          ),
        ),
      ],
    );
  }
}
