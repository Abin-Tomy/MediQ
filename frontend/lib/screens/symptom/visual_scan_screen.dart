import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/theme/app_colors.dart';
import '../doctor/doctor_list_screen.dart';

class VisualScanScreen extends StatefulWidget {
  const VisualScanScreen({super.key});

  @override
  State<VisualScanScreen> createState() => _VisualScanScreenState();
}

class _VisualScanScreenState extends State<VisualScanScreen>
    with SingleTickerProviderStateMixin {
  bool _isScanning = false;
  bool _hasResult = false;
  String _selectedPreset = "Petechial Rash (Arm - Kozhikode Case)";
  late AnimationController _scannerAnimationController;

  final Map<String, Map<String, dynamic>> _presetData = {
    "Petechial Rash (Arm - Kozhikode Case)": {
      "condition": "Petechial Rash Pattern",
      "confidence": "79%",
      "model": "YOLO v8 Nano (Object Detection)",
      "boxTop": 0.25,
      "boxLeft": 0.20,
      "boxWidth": 0.60,
      "boxHeight": 0.45,
      "color": const Color(0xFFEB5757),
      "analysis":
          "Small red/purple spots indicating intradermal bleeding. High correlation with Dengue presentation and falling platelet counts.",
      "urgency": "High — Immediate Evaluation Required",
    },
    "Erythema Migrans (Leg Lesion)": {
      "condition": "Erythema Migrans Lesion",
      "confidence": "84%",
      "model": "YOLO v8 Nano (Object Detection)",
      "boxTop": 0.30,
      "boxLeft": 0.25,
      "boxWidth": 0.50,
      "boxHeight": 0.40,
      "color": const Color(0xFFF2994A),
      "analysis":
          "Target-like inflammatory skin lesion. Common in bacterial vector-borne infections. Require antibiotic evaluation.",
      "urgency": "Medium-High Priority",
    },
    "Atopic Dermatitis (Hand)": {
      "condition": "Atopic Dermatitis / Eczema",
      "confidence": "91%",
      "model": "YOLO v8 Nano (Object Detection)",
      "boxTop": 0.20,
      "boxLeft": 0.15,
      "boxWidth": 0.70,
      "boxHeight": 0.55,
      "color": const Color(0xFF2F80ED),
      "analysis":
          "Localised pruritic erythematous plaques. Non-emergency dermatological condition.",
      "urgency": "Low-Medium Priority",
    },
  };

  @override
  void initState() {
    super.initState();
    _scannerAnimationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _scannerAnimationController.dispose();
    super.dispose();
  }

  void _startScan() {
    setState(() {
      _isScanning = true;
      _hasResult = false;
    });

    Timer(const Duration(seconds: 2), () {
      if (mounted) {
        setState(() {
          _isScanning = false;
          _hasResult = true;
        });
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final currentData = _presetData[_selectedPreset]!;

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
          "Visual Condition Detector",
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
              // MODEL 2 BADGE
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                decoration: BoxDecoration(
                  color: const Color(0xFFFFF3E0),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: const Color(0xFFF2994A).withValues(alpha: .3)),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.camera_alt_rounded,
                        color: Color(0xFFF2994A), size: 18),
                    const SizedBox(width: 8),
                    Text(
                      "Model 2 Output (YOLO v8 Nano Object Detection)",
                      style: GoogleFonts.poppins(
                        color: const Color(0xFFD97706),
                        fontWeight: FontWeight.w600,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 20),

              Text(
                "AI Skin & Rash Scanner",
                style: GoogleFonts.poppins(
                  fontSize: 24,
                  fontWeight: FontWeight.w700,
                  color: AppColors.textPrimary,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                "Select a clinical sample or take a photo to detect dermatological anomalies with automated bounding boxes.",
                style: GoogleFonts.poppins(
                  fontSize: 14,
                  color: AppColors.textSecondary,
                  height: 1.4,
                ),
              ),

              const SizedBox(height: 20),

              // PRESET SELECTOR
              Text(
                "Select Test Preset (Kozhikode Dataset):",
                style: GoogleFonts.poppins(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: AppColors.textPrimary,
                ),
              ),
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.border),
                ),
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<String>(
                    value: _selectedPreset,
                    isExpanded: true,
                    icon: const Icon(Icons.keyboard_arrow_down_rounded),
                    onChanged: (val) {
                      if (val != null) {
                        setState(() {
                          _selectedPreset = val;
                          _hasResult = false;
                        });
                      }
                    },
                    items: _presetData.keys.map((key) {
                      return DropdownMenuItem<String>(
                        value: key,
                        child: Text(
                          key,
                          style: GoogleFonts.poppins(
                            fontSize: 13.5,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                ),
              ),

              const SizedBox(height: 24),

              // SCANNER VIEWPORT
              Center(
                child: Container(
                  width: double.infinity,
                  height: 320,
                  decoration: BoxDecoration(
                    color: const Color(0xFF1E293B),
                    borderRadius: BorderRadius.circular(24),
                    border: Border.all(color: const Color(0xFF334155), width: 2),
                    boxShadow: const [
                      BoxShadow(
                        color: Color(0x1F000000),
                        blurRadius: 20,
                        offset: Offset(0, 10),
                      ),
                    ],
                  ),
                  child: Stack(
                    children: [
                      // SIMULATED IMAGE BACKGROUND
                      Positioned.fill(
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(22),
                          child: CustomPaint(
                            painter: _SimulatedSkinLesionPainter(
                              preset: _selectedPreset,
                            ),
                          ),
                        ),
                      ),

                      // SCANNING LASER
                      if (_isScanning)
                        AnimatedBuilder(
                          animation: _scannerAnimationController,
                          builder: (context, child) {
                            return Positioned(
                              top: 300 * _scannerAnimationController.value,
                              left: 0,
                              right: 0,
                              child: Container(
                                height: 3,
                                decoration: BoxDecoration(
                                  gradient: const LinearGradient(
                                    colors: [
                                      Colors.transparent,
                                      Color(0xFF00E676),
                                      Colors.transparent,
                                    ],
                                  ),
                                  boxShadow: [
                                    BoxShadow(
                                      color: const Color(0xFF00E676).withValues(alpha: .6),
                                      blurRadius: 10,
                                      spreadRadius: 2,
                                    ),
                                  ],
                                ),
                              ),
                            );
                          },
                        ),

                      // BOUNDING BOX (WHEN RESULT READY)
                      if (_hasResult)
                        LayoutBuilder(
                          builder: (context, constraints) {
                            final top = constraints.maxHeight * (currentData['boxTop'] as double);
                            final left = constraints.maxWidth * (currentData['boxLeft'] as double);
                            final width = constraints.maxWidth * (currentData['boxWidth'] as double);
                            final height = constraints.maxHeight * (currentData['boxHeight'] as double);
                            final Color color = currentData['color'] as Color;

                            return Positioned(
                              top: top,
                              left: left,
                              width: width,
                              height: height,
                              child: Container(
                                decoration: BoxDecoration(
                                  border: Border.all(color: color, width: 3),
                                  color: color.withValues(alpha: .15),
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Align(
                                  alignment: Alignment.topLeft,
                                  child: Container(
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 8,
                                      vertical: 4,
                                    ),
                                    decoration: BoxDecoration(
                                      color: color,
                                      borderRadius: const BorderRadius.only(
                                        bottomRight: Radius.circular(8),
                                      ),
                                    ),
                                    child: Text(
                                      "${currentData['condition']} ${currentData['confidence']}",
                                      style: GoogleFonts.poppins(
                                        color: Colors.white,
                                        fontSize: 11,
                                        fontWeight: FontWeight.w700,
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                            );
                          },
                        ),

                      // OVERLAY SCAN BUTTON IF NOT READY
                      if (!_isScanning && !_hasResult)
                        Center(
                          child: GestureDetector(
                            onTap: _startScan,
                            child: Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 24,
                                vertical: 14,
                              ),
                              decoration: BoxDecoration(
                                color: AppColors.primary,
                                borderRadius: BorderRadius.circular(30),
                                boxShadow: [
                                  BoxShadow(
                                    color: AppColors.primary.withValues(alpha: .4),
                                    blurRadius: 15,
                                    offset: const Offset(0, 6),
                                  ),
                                ],
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  const Icon(Icons.document_scanner_rounded,
                                      color: Colors.white, size: 20),
                                  const SizedBox(width: 10),
                                  Text(
                                    "Run YOLO v8 Detection",
                                    style: GoogleFonts.poppins(
                                      color: Colors.white,
                                      fontWeight: FontWeight.w600,
                                      fontSize: 15,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),

                      if (_isScanning)
                        Center(
                          child: Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 20,
                              vertical: 12,
                            ),
                            decoration: BoxDecoration(
                              color: Colors.black.withValues(alpha: .7),
                              borderRadius: BorderRadius.circular(20),
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                const SizedBox(
                                  width: 18,
                                  height: 18,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    color: Color(0xFF00E676),
                                  ),
                                ),
                                const SizedBox(width: 12),
                                Text(
                                  "YOLO v8 Nano Processing...",
                                  style: GoogleFonts.poppins(
                                    color: Colors.white,
                                    fontSize: 13,
                                    fontWeight: FontWeight.w500,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 28),

              // RESULTS SECTION
              if (_hasResult) ...[
                Text(
                  "AI Detection Breakdown",
                  style: GoogleFonts.poppins(
                    fontSize: 20,
                    fontWeight: FontWeight.w700,
                    color: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(height: 14),

                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(22),
                    border: Border.all(color: AppColors.border),
                    boxShadow: const [
                      BoxShadow(
                        color: Color(0x0A000000),
                        blurRadius: 12,
                        offset: Offset(0, 5),
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
                              currentData['condition'],
                              style: GoogleFonts.poppins(
                                fontSize: 18,
                                fontWeight: FontWeight.w700,
                                color: AppColors.textPrimary,
                              ),
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 10,
                              vertical: 4,
                            ),
                            decoration: BoxDecoration(
                              color: (currentData['color'] as Color)
                                  .withValues(alpha: .15),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Text(
                              "Confidence: ${currentData['confidence']}",
                              style: GoogleFonts.poppins(
                                fontSize: 12.5,
                                fontWeight: FontWeight.w700,
                                color: currentData['color'],
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          const Icon(Icons.warning_amber_rounded,
                              color: Color(0xFFF2994A), size: 18),
                          const SizedBox(width: 8),
                          Text(
                            currentData['urgency'],
                            style: GoogleFonts.poppins(
                              fontSize: 13,
                              fontWeight: FontWeight.w600,
                              color: const Color(0xFFD97706),
                            ),
                          ),
                        ],
                      ),
                      const Divider(height: 24),
                      Text(
                        "Clinical Assessment:",
                        style: GoogleFonts.poppins(
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                          color: AppColors.textSecondary,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        currentData['analysis'],
                        style: GoogleFonts.poppins(
                          fontSize: 14,
                          color: AppColors.textPrimary,
                          height: 1.5,
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 24),

                // SPECIALIST RECOMMENDATION
                SizedBox(
                  width: double.infinity,
                  height: 56,
                  child: ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
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
                    icon: const Icon(Icons.local_hospital_rounded),
                    label: Text(
                      "Book Specialist Consultation (5 km)",
                      style: GoogleFonts.poppins(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ),
              ],

              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }
}

class _SimulatedSkinLesionPainter extends CustomPainter {
  final String preset;

  _SimulatedSkinLesionPainter({required this.preset});

  @override
  void paint(Canvas canvas, Size size) {
    // Base skin tone
    final paint = Paint()..color = const Color(0xFFE0AC69);
    canvas.drawRect(Rect.fromLTWH(0, 0, size.width, size.height), paint);

    // Subtle texture / shadows
    final shadowPaint = Paint()
      ..color = const Color(0xFFC68B59)
      ..style = PaintingStyle.fill;
    canvas.drawCircle(Offset(size.width * 0.5, size.height * 0.5), 100, shadowPaint);

    if (preset.contains("Petechial")) {
      // Draw small petechial red spots
      final spotPaint = Paint()..color = const Color(0xFF8B0000);
      for (int i = 0; i < 35; i++) {
        final dx = size.width * (0.25 + (i * 13) % 50 / 100.0);
        final dy = size.height * (0.30 + (i * 17) % 40 / 100.0);
        canvas.drawCircle(Offset(dx, dy), 2.5 + (i % 3), spotPaint);
      }
    } else if (preset.contains("Erythema")) {
      // Draw target bullseye lesion
      final outerPaint = Paint()
        ..color = const Color(0xFFD32F2F).withValues(alpha: .6)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 14;
      final centerPaint = Paint()..color = const Color(0xFFB71C1C);

      final center = Offset(size.width * 0.5, size.height * 0.5);
      canvas.drawCircle(center, 60, outerPaint);
      canvas.drawCircle(center, 25, centerPaint);
    } else {
      // Eczema / Dermatitis plaque
      final plaquePaint = Paint()
        ..color = const Color(0xFFD32F2F).withValues(alpha: .5)
        ..style = PaintingStyle.fill;
      canvas.drawOval(
        Rect.fromCenter(
          center: Offset(size.width * 0.5, size.height * 0.48),
          width: 160,
          height: 120,
        ),
        plaquePaint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _SimulatedSkinLesionPainter oldDelegate) {
    return oldDelegate.preset != preset;
  }
}
