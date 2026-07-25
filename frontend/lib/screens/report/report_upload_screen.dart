import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/theme/app_colors.dart';
import '../doctor/doctor_list_screen.dart';

class ReportUploadScreen extends StatefulWidget {
  const ReportUploadScreen({super.key});

  @override
  State<ReportUploadScreen> createState() => _ReportUploadScreenState();
}

class _ReportUploadScreenState extends State<ReportUploadScreen>
    with SingleTickerProviderStateMixin {
  bool _isProcessing = false;
  bool _hasSummary = false;
  String _selectedReport = "Blood Test (Kozhikode Diagnostic Lab).pdf";
  int _processStep = 0;

  final Map<String, Map<String, dynamic>> _reportData = {
    "Blood Test (Kozhikode Diagnostic Lab).pdf": {
      "title": "Complete Blood Count (CBC) - Diagnostic Lab",
      "date": "24 Jul 2026",
      "model": "T5-small (fine-tuned on PubMed 200k RCT)",
      "extraction": "PyMuPDF (fitz) text extraction engine",
      "metrics": [
        {
          "name": "Platelet Count",
          "value": "91,000 /mcL",
          "normal": "150,000 - 450,000",
          "status": "Critical Low",
          "color": const Color(0xFFEB5757),
        },
        {
          "name": "Hemoglobin",
          "value": "12.4 g/dL",
          "normal": "12.0 - 15.5",
          "status": "Normal",
          "color": const Color(0xFF27AE60),
        },
        {
          "name": "Total WBC Count",
          "value": "3,800 /mcL",
          "normal": "4,000 - 11,000",
          "status": "Borderline Low",
          "color": const Color(0xFFF2994A),
        },
      ],
      "plainText":
          "Your platelet count of 91,000 is significantly below the normal threshold of 150,000. In endemic regions like Kozhikode during monsoon, a dropping platelet count combined with fever or rash strongly correlates with Dengue fever or Leptospirosis progression. This clinical picture requires professional medical evaluation today.",
      "urgency": "High Urgency — Doctor Visit Required Today",
      "urgencyColor": const Color(0xFF9B1C1C),
      "urgencyBg": const Color(0xFFFFE3E3),
    },
    "Complete Blood Count (CBC - Routine).pdf": {
      "title": "Annual Routine Blood Test",
      "date": "15 Jul 2026",
      "model": "T5-small (fine-tuned on PubMed 200k RCT)",
      "extraction": "PyMuPDF (fitz) text extraction engine",
      "metrics": [
        {
          "name": "Platelet Count",
          "value": "245,000 /mcL",
          "normal": "150,000 - 450,000",
          "status": "Normal",
          "color": const Color(0xFF27AE60),
        },
        {
          "name": "Hemoglobin",
          "value": "13.8 g/dL",
          "normal": "12.0 - 15.5",
          "status": "Normal",
          "color": const Color(0xFF27AE60),
        },
        {
          "name": "Total WBC Count",
          "value": "6,500 /mcL",
          "normal": "4,000 - 11,000",
          "status": "Normal",
          "color": const Color(0xFF27AE60),
        },
      ],
      "plainText":
          "All primary hematology indicators including platelets, white blood cells, and hemoglobin are within healthy standard ranges. No acute hematological infection or abnormality detected in this sample.",
      "urgency": "Normal — Routine Health Maintained",
      "urgencyColor": const Color(0xFF1E429F),
      "urgencyBg": const Color(0xFFE1EFFE),
    },
    "Liver Function Test (LFT - Mild SGPT).pdf": {
      "title": "Hepatic Function Panel",
      "date": "10 Jul 2026",
      "model": "T5-small (fine-tuned on PubMed 200k RCT)",
      "extraction": "PyMuPDF (fitz) text extraction engine",
      "metrics": [
        {
          "name": "SGPT / ALT",
          "value": "78 U/L",
          "normal": "7 - 56",
          "status": "Elevated",
          "color": const Color(0xFFF2994A),
        },
        {
          "name": "SGOT / AST",
          "value": "45 U/L",
          "normal": "10 - 40",
          "status": "Mildly High",
          "color": const Color(0xFFF2994A),
        },
        {
          "name": "Total Bilirubin",
          "value": "0.9 mg/dL",
          "normal": "0.1 - 1.2",
          "status": "Normal",
          "color": const Color(0xFF27AE60),
        },
      ],
      "plainText":
          "Your liver enzymes (SGPT/ALT and SGOT/AST) show mild elevation above standard limits. This indicates minor hepatic stress or inflammation, often related to recent medication, diet, or resolving viral infection. A follow-up consultation with a General Physician is recommended.",
      "urgency": "Medium Urgency — Schedule Follow-up",
      "urgencyColor": const Color(0xFF92400E),
      "urgencyBg": const Color(0xFFFEF3C7),
    },
  };

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

    await Future.delayed(const Duration(milliseconds: 800));
    if (!mounted) return;
    setState(() {
      _isProcessing = false;
      _hasSummary = true;
    });
  }

  @override
  Widget build(BuildContext context) {
    final currentReport = _reportData[_selectedReport]!;
    final List<Map<String, dynamic>> metrics =
        (currentReport['metrics'] as List).cast<Map<String, dynamic>>();

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded, color: AppColors.textPrimary),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text(
          "Medical Report Summarizer",
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
              // MODEL 3 BADGE
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                decoration: BoxDecoration(
                  color: const Color(0xFFE8F5E9),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: const Color(0xFF27AE60).withValues(alpha: .3)),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.description_rounded,
                        color: Color(0xFF27AE60), size: 18),
                    const SizedBox(width: 8),
                    Text(
                      "Model 3 Output (T5-small NLP Summarizer)",
                      style: GoogleFonts.poppins(
                        color: const Color(0xFF1B5E20),
                        fontWeight: FontWeight.w600,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 20),

              Text(
                "AI Lab Report Translation",
                style: GoogleFonts.poppins(
                  fontSize: 24,
                  fontWeight: FontWeight.w700,
                  color: AppColors.textPrimary,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                "Upload blood tests or diagnostic lab PDFs. PyMuPDF extracts the raw clinical text, and T5-small converts complex medical metrics into plain language.",
                style: GoogleFonts.poppins(
                  fontSize: 14,
                  color: AppColors.textSecondary,
                  height: 1.4,
                ),
              ),

              const SizedBox(height: 20),

              // PRESET SELECTOR / FILE UPLOAD BOX
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(24),
                  border: Border.all(
                      color: AppColors.primary.withValues(alpha: .3), width: 1.5),
                  boxShadow: const [
                    BoxShadow(
                      color: Color(0x0A000000),
                      blurRadius: 15,
                      offset: Offset(0, 5),
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
                            color: const Color(0xFF2F80ED).withValues(alpha: .1),
                            borderRadius: BorderRadius.circular(16),
                          ),
                          child: const Icon(Icons.upload_file_rounded,
                              color: AppColors.primary, size: 28),
                        ),
                        const SizedBox(width: 14),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                "Select Lab Report PDF",
                                style: GoogleFonts.poppins(
                                  fontSize: 16,
                                  fontWeight: FontWeight.w700,
                                  color: AppColors.textPrimary,
                                ),
                              ),
                              Text(
                                "Simulated PyMuPDF extraction ready",
                                style: GoogleFonts.poppins(
                                  fontSize: 12,
                                  color: AppColors.textHint,
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
                        color: const Color(0xFFF8FAFC),
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: AppColors.border),
                      ),
                      child: DropdownButtonHideUnderline(
                        child: DropdownButton<String>(
                          value: _selectedReport,
                          isExpanded: true,
                          icon: const Icon(Icons.keyboard_arrow_down_rounded),
                          onChanged: (val) {
                            if (val != null) {
                              setState(() {
                                _selectedReport = val;
                                _hasSummary = false;
                              });
                            }
                          },
                          items: _reportData.keys.map((key) {
                            return DropdownMenuItem<String>(
                              value: key,
                              child: Text(
                                key,
                                style: GoogleFonts.poppins(
                                  fontSize: 13,
                                  fontWeight: FontWeight.w500,
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
                          backgroundColor: AppColors.primary,
                          foregroundColor: Colors.white,
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
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ),
                              )
                            : const Icon(Icons.auto_awesome_rounded, size: 20),
                        label: Text(
                          _isProcessing ? "Processing..." : "Summarize Report with T5-small",
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

              // PROCESSING STEPS
              if (_isProcessing) ...[
                const SizedBox(height: 28),
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: Column(
                    children: [
                      _buildStepRow(1, "Extracting text from PDF (PyMuPDF / fitz)", _processStep >= 1),
                      const SizedBox(height: 14),
                      _buildStepRow(2, "Parsing hematology clinical values", _processStep >= 2),
                      const SizedBox(height: 14),
                      _buildStepRow(3, "Generating plain language summary (T5-small)", _processStep >= 3),
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
                    color: currentReport['urgencyBg'] as Color,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: (currentReport['urgencyColor'] as Color).withValues(alpha: .3)),
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
                          currentReport['urgency'] as String,
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
                    gradient: const LinearGradient(
                      colors: [Color(0xFFEFF6FF), Color(0xFFDBEAFE)],
                    ),
                    borderRadius: BorderRadius.circular(24),
                    border: Border.all(color: const Color(0xFF3B82F6).withValues(alpha: .4)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Icon(Icons.translate_rounded,
                              color: Color(0xFF1E40AF), size: 24),
                          const SizedBox(width: 10),
                          Text(
                            "Plain Language Summary",
                            style: GoogleFonts.poppins(
                              fontSize: 17,
                              fontWeight: FontWeight.w700,
                              color: const Color(0xFF1E3A8A),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Text(
                        currentReport['plainText'] as String,
                        style: GoogleFonts.poppins(
                          fontSize: 14.5,
                          color: const Color(0xFF1E3A8A),
                          height: 1.6,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 24),

                // EXTRACTED CLINICAL VALUES TABLE
                Text(
                  "Extracted Clinical Values Table",
                  style: GoogleFonts.poppins(
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                    color: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(height: 12),

                Container(
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: ListView.separated(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: metrics.length,
                    separatorBuilder: (_, __) => const Divider(height: 1),
                    itemBuilder: (_, idx) {
                      final m = metrics[idx];
                      final Color col = m['color'] as Color;

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
                                    m['name'] as String,
                                    style: GoogleFonts.poppins(
                                      fontSize: 15,
                                      fontWeight: FontWeight.w600,
                                      color: AppColors.textPrimary,
                                    ),
                                  ),
                                  Text(
                                    "Normal: ${m['normal']}",
                                    style: GoogleFonts.poppins(
                                      fontSize: 12,
                                      color: AppColors.textHint,
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
                                  color: AppColors.textPrimary,
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
                                m['status'] as String,
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
                      backgroundColor: const Color(0xFF27AE60),
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
                      "Book Doctor Appointment (Within 5 km)",
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
  }

  Widget _buildStepRow(int stepNum, String text, bool isDone) {
    return Row(
      children: [
        Icon(
          isDone ? Icons.check_circle_rounded : Icons.radio_button_unchecked_rounded,
          color: isDone ? const Color(0xFF27AE60) : AppColors.textHint,
          size: 22,
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Text(
            text,
            style: GoogleFonts.poppins(
              fontSize: 14,
              fontWeight: isDone ? FontWeight.w600 : FontWeight.w400,
              color: isDone ? AppColors.textPrimary : AppColors.textSecondary,
            ),
          ),
        ),
      ],
    );
  }
}
