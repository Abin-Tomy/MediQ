import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/theme/app_theme_provider.dart';
import '../../models/doctor.dart';
import 'appointments_screen.dart';

class AppointmentSuccessScreen extends StatefulWidget {
  final Doctor doctor;
  final String slot;

  const AppointmentSuccessScreen({
    super.key,
    required this.doctor,
    required this.slot,
  });

  @override
  State<AppointmentSuccessScreen> createState() => _AppointmentSuccessScreenState();
}

class _AppointmentSuccessScreenState extends State<AppointmentSuccessScreen>
    with TickerProviderStateMixin {
  late AnimationController _checkAnimController;
  late Animation<double> _checkScaleAnim;

  bool _isSharing = false;
  bool _isSaved = false;

  @override
  void initState() {
    super.initState();
    _checkAnimController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );
    _checkScaleAnim = CurvedAnimation(
      parent: _checkAnimController,
      curve: Curves.elasticOut,
    );
    _checkAnimController.forward();
  }

  @override
  void dispose() {
    _checkAnimController.dispose();
    super.dispose();
  }

  void _shareToPharmacy(AppThemeProvider theme) async {
    setState(() => _isSharing = true);
    await Future.delayed(const Duration(milliseconds: 1000));
    if (!mounted) return;
    setState(() => _isSharing = false);

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          theme.tr(
            "E-Prescription securely sent to verified Kozhikode Pharmacies!",
            "ഇ-പ്രിസ്ക്രിപ്ഷൻ കോഴിക്കോട്ടെ ഫാർമസികൾക്ക് അയച്ചു നൽകി!",
          ),
          style: GoogleFonts.poppins(color: Colors.white),
        ),
        backgroundColor: const Color(0xFF10B981),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  void _saveToVault(AppThemeProvider theme) {
    setState(() => _isSaved = true);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          theme.tr(
            "Prescription PDF stored in your Offline Digital Vault.",
            "പ്രിസ്ക്രിപ്ഷൻ PDF നിങ്ങളുടെ ഫോണിലെ സുരക്ഷിത ഫോൾഡറിൽ സൂക്ഷിച്ചു.",
          ),
          style: GoogleFonts.poppins(color: Colors.white),
        ),
        backgroundColor: theme.primaryAccent,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: AppThemeProvider(),
      builder: (context, _) {
        final theme = AppThemeProvider();
        final doctor = widget.doctor;

        final title = theme.tr("Booking Confirmed!", "ബുക്കിംഗ് വിജയകരം!");
        final subtitle = theme.tr(
          "Your appointment & E-Prescription vault are ready",
          "നിങ്ങളുടെ അപ്പോയിന്റ്മെന്റും ഇ-പ്രിസ്ക്രിപ്ഷനും തയ്യാറാണ്",
        );
        final vaultTitle = theme.tr("Digital Prescription Vault", "ഡിജിറ്റൽ പ്രിസ്ക്രിപ്ഷൻ വോൾട്ട്");
        final idLbl = theme.tr("E-Prescription ID: #MEDIQ-RX-KL11", "ഇ-കുറിപ്പടി നമ്പർ: #MEDIQ-RX-KL11");
        final patientLbl = theme.tr("Patient: Vishnu (Monsoon Health Pass Verified ✅)", "രോഗി: വിഷ്ണു (മൺസൂൺ ഹെൽത്ത് പാസ് പരിശോധിച്ചു ✅)");
        final medsTitle = theme.tr("Prescribed Prophylaxis Starter Pack", "പ്രാഥമിക പ്രതിരോധ മരുന്നുകൾ");

        final shareBtnLbl = _isSharing
            ? theme.tr("Sending to Smart Pharmacy...", "ഫാർമസിക്ക് അയയ്ക്കുന്നു...")
            : theme.tr("One-Tap Pharmacy Sharing (Instant Dispense)", "ഫാർമസിക്ക് ഒറ്റ ക്ലിക്കിൽ അയയ്ക്കുക");
        final saveBtnLbl = _isSaved
            ? theme.tr("Saved in Offline Vault ✓", "ഫോണിൽ സൂക്ഷിച്ചു ✓")
            : theme.tr("Save PDF to Offline Vault", "PDF ഫോണിൽ സൂക്ഷിക്കുക");
        final viewAppBtnLbl = theme.tr("View All Appointments", "എല്ലാ അപ്പോയിന്റ്മെന്റുകളും കാണുക");

        final medsList = [
          {
            "name_en": "Doxycycline Prophylaxis 100mg",
            "name_ml": "ഡോക്സിസൈക്ലിൻ 100mg",
            "dos_en": "1 Capsule daily after food (5 days)",
            "dos_ml": "ദിവസവും 1 ഗുളിക ഭക്ഷണത്തിന് ശേഷം (5 ദിവസം)",
          },
          {
            "name_en": "Paracetamol (Dolo 650mg)",
            "name_ml": "പാരസെറ്റമോൾ (Dolo 650mg)",
            "dos_en": "Take SOS for fever > 100°F or body pain",
            "dos_ml": "പനിയോ കഠിനമായ വേദനയോ ഉണ്ടെങ്കിൽ കഴിക്കുക",
          },
          {
            "name_en": "Electrolyte ORS Sachet",
            "name_ml": "ORS ലായനി പാക്കറ്റ്",
            "dos_en": "1 sachet in 1 liter boiled water",
            "dos_ml": "1 പാക്കറ്റ് 1 ലിറ്റർ തിളപ്പിച്ചാറ്റിയ വെള്ളത്തിൽ",
          },
        ];

        return Scaffold(
          backgroundColor: theme.background,
          body: SafeArea(
            child: SingleChildScrollView(
              physics: const BouncingScrollPhysics(),
              padding: const EdgeInsets.fromLTRB(24, 20, 24, 30),
              child: Column(
                children: [
                  const SizedBox(height: 10),

                  // CELEBRATION CHECKMARK
                  ScaleTransition(
                    scale: _checkScaleAnim,
                    child: Container(
                      width: 84,
                      height: 84,
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [Color(0xFF10B981), Color(0xFF059669)],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                        shape: BoxShape.circle,
                        boxShadow: [
                          BoxShadow(
                            color: const Color(0xFF10B981).withValues(alpha: .35),
                            blurRadius: 18,
                            offset: const Offset(0, 8),
                          ),
                        ],
                      ),
                      child: const Icon(
                        Icons.check_rounded,
                        color: Colors.white,
                        size: 48,
                      ),
                    ),
                  ),

                  const SizedBox(height: 18),

                  Text(
                    title,
                    style: GoogleFonts.poppins(
                      fontSize: 24,
                      fontWeight: FontWeight.w700,
                      color: theme.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    subtitle,
                    style: GoogleFonts.poppins(
                      fontSize: 13.5,
                      color: theme.textSecondary,
                    ),
                  ),

                  const SizedBox(height: 24),

                  // DIGITAL PRESCRIPTION VAULT CARD
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(22),
                    decoration: BoxDecoration(
                      color: theme.cardColor,
                      borderRadius: BorderRadius.circular(24),
                      border: Border.all(
                        color: theme.primaryAccent.withValues(alpha: .5),
                        width: 1.5,
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: .05),
                          blurRadius: 16,
                          offset: const Offset(0, 6),
                        ),
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // VAULT HEADER
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Expanded(
                              child: Row(
                                children: [
                                  Container(
                                    padding: const EdgeInsets.all(8),
                                    decoration: BoxDecoration(
                                      color: theme.primaryAccent.withValues(alpha: .15),
                                      borderRadius: BorderRadius.circular(10),
                                    ),
                                    child: Icon(Icons.shield_rounded,
                                        color: theme.primaryAccent, size: 20),
                                  ),
                                  const SizedBox(width: 10),
                                  Expanded(
                                    child: Text(
                                      vaultTitle,
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                      style: GoogleFonts.poppins(
                                        fontSize: 15,
                                        fontWeight: FontWeight.w700,
                                        color: theme.textPrimary,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(width: 8),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: const Color(0xFF10B981).withValues(alpha: .15),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Text(
                                "VERIFIED Rx",
                                style: GoogleFonts.poppins(
                                  fontSize: 11,
                                  fontWeight: FontWeight.w700,
                                  color: const Color(0xFF10B981),
                                ),
                              ),
                            ),
                          ],
                        ),

                        const SizedBox(height: 14),
                        Text(
                          idLbl,
                          style: GoogleFonts.poppins(
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                            color: theme.primaryAccent,
                          ),
                        ),
                        Text(
                          patientLbl,
                          style: GoogleFonts.poppins(
                            fontSize: 12,
                            color: theme.textSecondary,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          "${doctor.name.startsWith('Dr.') ? doctor.name : 'Dr. ${doctor.name}'} (${doctor.specialty}) • ${doctor.hospital}",
                          style: GoogleFonts.poppins(
                            fontSize: 12.5,
                            fontWeight: FontWeight.w600,
                            color: theme.textPrimary,
                          ),
                        ),

                        Divider(color: theme.borderColor, height: 26),

                        // PRESCRIBED MEDS
                        Text(
                          medsTitle,
                          style: GoogleFonts.poppins(
                            fontSize: 13.5,
                            fontWeight: FontWeight.w700,
                            color: theme.textPrimary,
                          ),
                        ),
                        const SizedBox(height: 12),

                        ...medsList.map((m) {
                          final mName = theme.tr(m["name_en"] as String, m["name_ml"] as String);
                          final mDos = theme.tr(m["dos_en"] as String, m["dos_ml"] as String);

                          return Padding(
                            padding: const EdgeInsets.only(bottom: 12),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Icon(Icons.medication_rounded,
                                    color: Color(0xFF10B981), size: 18),
                                const SizedBox(width: 10),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        mName,
                                        style: GoogleFonts.poppins(
                                          fontSize: 13.5,
                                          fontWeight: FontWeight.w600,
                                          color: theme.textPrimary,
                                        ),
                                      ),
                                      Text(
                                        mDos,
                                        style: GoogleFonts.poppins(
                                          fontSize: 11.5,
                                          color: theme.textSecondary,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          );
                        }),

                        Divider(color: theme.borderColor, height: 26),

                        // QR CODE VERIFICATION BOX
                        Row(
                          children: [
                            Container(
                              width: 80,
                              height: 80,
                              padding: const EdgeInsets.all(6),
                              decoration: BoxDecoration(
                                color: Colors.white,
                                borderRadius: BorderRadius.circular(14),
                                border: Border.all(color: Colors.black12),
                              ),
                              child: CustomPaint(
                                painter: _QrCodePainter(),
                              ),
                            ),
                            const SizedBox(width: 16),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    theme.tr(
                                      "Cryptographic QR Code Verified",
                                      "QR കോഡ് സുരക്ഷ ഉറപ്പാക്കിയിരിക്കുന്നു",
                                    ),
                                    style: GoogleFonts.poppins(
                                      fontSize: 13,
                                      fontWeight: FontWeight.w700,
                                      color: theme.textPrimary,
                                    ),
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    theme.tr(
                                      "Show this QR at any Kozhikode Smart Pharmacy for instant dispensing without paper prescriptions.",
                                      "കോഴിക്കോട്ടെ ഏതെങ്കിലും സ്മാർട്ട് ഫാർമസിയിൽ ഈ QR കോഡ് കാണിച്ച് മരുന്ന് വാങ്ങാവുന്നതാണ്.",
                                    ),
                                    style: GoogleFonts.poppins(
                                      fontSize: 11.5,
                                      color: theme.textSecondary,
                                      height: 1.3,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 26),

                  // ONE-TAP PHARMACY SHARING BUTTON
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
                      onPressed: _isSharing ? null : () => _shareToPharmacy(theme),
                      icon: _isSharing
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(strokeWidth: 2.2, color: Colors.white),
                            )
                          : const Icon(Icons.local_pharmacy_rounded, size: 22),
                      label: Text(
                        shareBtnLbl,
                        style: GoogleFonts.poppins(
                          fontSize: 15,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ),

                  const SizedBox(height: 12),

                  // SAVE TO VAULT BUTTON
                  SizedBox(
                    width: double.infinity,
                    height: 52,
                    child: OutlinedButton.icon(
                      style: OutlinedButton.styleFrom(
                        foregroundColor: theme.primaryAccent,
                        side: BorderSide(color: theme.primaryAccent, width: 1.5),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16),
                        ),
                      ),
                      onPressed: _isSaved ? null : () => _saveToVault(theme),
                      icon: Icon(_isSaved ? Icons.check_circle_rounded : Icons.download_rounded, size: 20),
                      label: Text(
                        saveBtnLbl,
                        style: GoogleFonts.poppins(
                          fontSize: 14.5,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ),

                  const SizedBox(height: 22),

                  // VIEW MY APPOINTMENTS LINK
                  TextButton.icon(
                    onPressed: () {
                      Navigator.pushAndRemoveUntil(
                        context,
                        MaterialPageRoute(builder: (_) => const AppointmentsScreen()),
                        (route) => route.isFirst,
                      );
                    },
                    icon: Icon(Icons.calendar_today_rounded, color: theme.textSecondary, size: 18),
                    label: Text(
                      viewAppBtnLbl,
                      style: GoogleFonts.poppins(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: theme.textSecondary,
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
}

class _QrCodePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = const Color(0xFF0F172A)
      ..style = PaintingStyle.fill;

    final double cellSize = size.width / 9;

    // Draw 3 corner positioning squares
    void drawCorner(int row, int col) {
      canvas.drawRect(Rect.fromLTWH(col * cellSize, row * cellSize, cellSize * 3, cellSize * 3), paint);
      final whitePaint = Paint()..color = Colors.white;
      canvas.drawRect(Rect.fromLTWH((col + 0.6) * cellSize, (row + 0.6) * cellSize, cellSize * 1.8, cellSize * 1.8), whitePaint);
      canvas.drawRect(Rect.fromLTWH((col + 1.1) * cellSize, (row + 1.1) * cellSize, cellSize * 0.8, cellSize * 0.8), paint);
    }

    drawCorner(0, 0);
    drawCorner(0, 6);
    drawCorner(6, 0);

    // Draw random data cells for realistic QR appearance
    final rng = math.Random(42);
    for (int r = 0; r < 9; r++) {
      for (int c = 0; c < 9; c++) {
        if ((r < 3 && c < 3) || (r < 3 && c >= 6) || (r >= 6 && c < 3)) continue;
        if (rng.nextBool()) {
          canvas.drawRect(
            Rect.fromLTWH(c * cellSize + 1, r * cellSize + 1, cellSize - 2, cellSize - 2),
            paint,
          );
        }
      }
    }

    // Center MediQ Cross
    final centerPaint = Paint()..color = const Color(0xFF10B981);
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromCenter(center: Offset(size.width / 2, size.height / 2), width: cellSize * 2.5, height: cellSize * 2.5),
        const Radius.circular(4),
      ),
      centerPaint,
    );
    final crossWhite = Paint()..color = Colors.white;
    canvas.drawRect(Rect.fromCenter(center: Offset(size.width / 2, size.height / 2), width: cellSize * 1.5, height: cellSize * 0.5), crossWhite);
    canvas.drawRect(Rect.fromCenter(center: Offset(size.width / 2, size.height / 2), width: cellSize * 0.5, height: cellSize * 1.5), crossWhite);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
