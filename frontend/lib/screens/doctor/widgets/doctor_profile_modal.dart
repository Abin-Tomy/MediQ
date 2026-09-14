import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../../../core/theme/app_theme_provider.dart';
import '../../../../models/doctor.dart';
import '../../appointment/booking_screen.dart';

class DoctorProfileModal extends StatefulWidget {
  final Doctor doctor;

  const DoctorProfileModal({super.key, required this.doctor});

  @override
  State<DoctorProfileModal> createState() => _DoctorProfileModalState();
}

class _DoctorProfileModalState extends State<DoctorProfileModal>
    with SingleTickerProviderStateMixin {
  late AnimationController _radarAnimController;

  @override
  void initState() {
    super.initState();
    _radarAnimController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2500),
    )..repeat();
  }

  @override
  void dispose() {
    _radarAnimController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: AppThemeProvider(),
      builder: (context, _) {
        final theme = AppThemeProvider();
        final doctor = widget.doctor;

        final title = theme.tr("Doctor Profile & Clinic Route", "ഡോക്ടറുടെ വിവരങ്ങളും ക്ലിനിക്ക് വഴിയും");
        final distanceLbl = theme.tr("Distance from your location:", "നിങ്ങളുടെ സ്ഥാനത്ത് നിന്നുള്ള ദൂരം:");
        final mapTitle = theme.tr("Live Monsoon GPS Radar Map", "തത്സമയ മൺസൂൺ GPS റഡാർ");
        final mapSubtitle = theme.tr("Kozhikode Smart Medical Network (Flood-Safe Route Verified)", "കോഴിക്കോട് സ്മാർട്ട് മെഡിക്കൽ നെറ്റ്‌വർക്ക് (സുരക്ഷിത വഴി)");
        final prepTitle = theme.tr("Tele-Medicine & Clinic Readiness", "ടെലി-മെഡിസിൻ & ക്ലിനിക്ക് സജ്ജീകരണം");
        final feeLbl = theme.tr("Consultation Fee", "പരിശോധനാ ഫീസ്");
        final bookBtnLbl = theme.tr("Book Clinic Appointment", "ക്ലിനിക്ക് സമയം ബുക്ക് ചെയ്യുക");
        final teleBtnLbl = theme.tr("Start Tele-Medicine Consult Prep", "വീഡിയോ പരിശോധനയ്ക്ക് തയ്യാറെടുക്കുക");

        final prepItems = [
          {
            "title_en": "Monsoon Digital Health Pass Accepted",
            "title_ml": "മൺസൂൺ ഡിജിറ്റൽ ഹെൽത്ത് പാസ് സ്വീകരിക്കും",
            "desc_en": "No paper files required; instant EHR sync",
            "desc_ml": "കടലാസ് രേഖകൾ ആവശ്യമില്ല; ഡിജിറ്റൽ പരിശോധന",
            "icon": Icons.verified_user_rounded,
            "color": const Color(0xFF10B981),
          },
          {
            "title_en": "Instant E-Prescription Vault Enabled",
            "title_ml": "ഇ-പ്രിസ്ക്രിപ്ഷൻ സൗകര്യം ലഭ്യമാണ്",
            "desc_en": "Prescriptions sent directly to pharmacy QR vault",
            "desc_ml": "മരുന്ന് കുറിപ്പടി ഫോണിൽ നേരിട്ട് ലഭിക്കും",
            "icon": Icons.qr_code_rounded,
            "color": const Color(0xFF2F80ED),
          },
          {
            "title_en": "Flood-Safe Clinic Access Verified",
            "title_ml": "ക്ലിനിക്കിലേക്കുള്ള സുരക്ഷിത വഴി ഉറപ്പാക്കി",
            "desc_en": "Roads clear of waterlogging as per city sensors",
            "desc_ml": "വെള്ളക്കെട്ടില്ലാത്ത സുരക്ഷിത റോഡുകൾ",
            "icon": Icons.add_road_rounded,
            "color": const Color(0xFFF59E0B),
          },
        ];

        return Container(
          constraints: BoxConstraints(
            maxHeight: MediaQuery.of(context).size.height * 0.88,
          ),
          decoration: BoxDecoration(
            color: theme.background,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(28)),
          ),
          child: Column(
            children: [
              // HANDLE
              const SizedBox(height: 12),
              Container(
                width: 48,
                height: 5,
                decoration: BoxDecoration(
                  color: theme.borderColor,
                  borderRadius: BorderRadius.circular(10),
                ),
              ),
              const SizedBox(height: 14),

              // HEADER
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 24),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      title,
                      style: GoogleFonts.poppins(
                        fontSize: 17,
                        fontWeight: FontWeight.w700,
                        color: theme.textPrimary,
                      ),
                    ),
                    IconButton(
                      icon: Icon(Icons.close_rounded, color: theme.textSecondary),
                      onPressed: () => Navigator.pop(context),
                    ),
                  ],
                ),
              ),
              Divider(color: theme.borderColor, height: 20),

              // SCROLLABLE BODY
              Expanded(
                child: SingleChildScrollView(
                  physics: const BouncingScrollPhysics(),
                  padding: const EdgeInsets.fromLTRB(24, 6, 24, 30),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // DOCTOR HERO AVATAR & INFO
                      Row(
                        children: [
                          Hero(
                            tag: 'doctor_avatar_${doctor.id}',
                            child: Container(
                              width: 80,
                              height: 80,
                              decoration: BoxDecoration(
                                gradient: const LinearGradient(
                                  colors: [Color(0xFF2F80ED), Color(0xFF56CCF2)],
                                  begin: Alignment.topLeft,
                                  end: Alignment.bottomRight,
                                ),
                                borderRadius: BorderRadius.circular(24),
                                boxShadow: [
                                  BoxShadow(
                                    color: const Color(0xFF2F80ED).withValues(alpha: .3),
                                    blurRadius: 12,
                                    offset: const Offset(0, 6),
                                  ),
                                ],
                              ),
                              child: Center(
                                child: Text(
                                  doctor.name.replaceFirst("Dr. ", "").substring(0, 2).toUpperCase(),
                                  style: GoogleFonts.poppins(
                                    color: Colors.white,
                                    fontSize: 28,
                                    fontWeight: FontWeight.w700,
                                    decoration: TextDecoration.none,
                                  ),
                                ),
                              ),
                            ),
                          ),
                          const SizedBox(width: 18),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  doctor.name,
                                  style: GoogleFonts.poppins(
                                    fontSize: 20,
                                    fontWeight: FontWeight.w700,
                                    color: theme.textPrimary,
                                  ),
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  doctor.specialty,
                                  style: GoogleFonts.poppins(
                                    fontSize: 14.5,
                                    fontWeight: FontWeight.w600,
                                    color: theme.primaryAccent,
                                  ),
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  doctor.qualification,
                                  style: GoogleFonts.poppins(
                                    fontSize: 12.5,
                                    color: theme.textSecondary,
                                  ),
                                ),
                                const SizedBox(height: 6),
                                Row(
                                  children: [
                                    Icon(Icons.local_hospital_rounded,
                                        size: 15, color: theme.textHint),
                                    const SizedBox(width: 6),
                                    Expanded(
                                      child: Text(
                                        doctor.hospital,
                                        style: GoogleFonts.poppins(
                                          fontSize: 12.5,
                                          fontWeight: FontWeight.w500,
                                          color: theme.textSecondary,
                                        ),
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),

                      const SizedBox(height: 22),

                      // BIO CARD
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: theme.cardColor,
                          borderRadius: BorderRadius.circular(18),
                          border: Border.all(color: theme.borderColor),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              theme.tr("Clinical Experience & Bio", "വിദഗ്ധ സേവനങ്ങളും അനുഭവസമ്പത്തും"),
                              style: GoogleFonts.poppins(
                                fontSize: 13,
                                fontWeight: FontWeight.w700,
                                color: theme.textPrimary,
                              ),
                            ),
                            const SizedBox(height: 6),
                            Text(
                              doctor.bio,
                              style: GoogleFonts.poppins(
                                fontSize: 13,
                                color: theme.textSecondary,
                                height: 1.5,
                              ),
                            ),
                          ],
                        ),
                      ),

                      const SizedBox(height: 22),

                      // INTERACTIVE RADAR DISTANCE MAP
                      Text(
                        mapTitle,
                        style: GoogleFonts.poppins(
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                          color: theme.textPrimary,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        "$distanceLbl ${doctor.distanceKm} km ($mapSubtitle)",
                        style: GoogleFonts.poppins(
                          fontSize: 12,
                          color: theme.textSecondary,
                        ),
                      ),
                      const SizedBox(height: 12),

                      // RADAR MAP WIDGET
                      AnimatedBuilder(
                        animation: _radarAnimController,
                        builder: (context, _) {
                          return Container(
                            height: 180,
                            width: double.infinity,
                            decoration: BoxDecoration(
                              color: theme.isDark || theme.isMonsoon
                                  ? const Color(0xFF0F172A)
                                  : const Color(0xFFE0F2FE),
                              borderRadius: BorderRadius.circular(22),
                              border: Border.all(color: theme.primaryAccent.withValues(alpha: .4), width: 1.5),
                              boxShadow: [
                                BoxShadow(
                                  color: theme.primaryAccent.withValues(alpha: .1),
                                  blurRadius: 15,
                                  offset: const Offset(0, 5),
                                ),
                              ],
                            ),
                            child: ClipRRect(
                              borderRadius: BorderRadius.circular(20),
                              child: CustomPaint(
                                painter: _RadarMapPainter(
                                  progress: _radarAnimController.value,
                                  radarColor: theme.primaryAccent,
                                  isDark: theme.isDark || theme.isMonsoon,
                                  distanceKm: doctor.distanceKm,
                                  docName: doctor.name.replaceFirst("Dr. ", ""),
                                ),
                              ),
                            ),
                          );
                        },
                      ),

                      const SizedBox(height: 24),

                      // TELE-MEDICINE & PREP CHECKLIST
                      Text(
                        prepTitle,
                        style: GoogleFonts.poppins(
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                          color: theme.textPrimary,
                        ),
                      ),
                      const SizedBox(height: 12),

                      ...prepItems.map((item) {
                        final t = theme.tr(item["title_en"] as String, item["title_ml"] as String);
                        final d = theme.tr(item["desc_en"] as String, item["desc_ml"] as String);
                        final col = item["color"] as Color;
                        final icon = item["icon"] as IconData;

                        return Container(
                          margin: const EdgeInsets.only(bottom: 10),
                          padding: const EdgeInsets.all(14),
                          decoration: BoxDecoration(
                            color: theme.cardColor,
                            borderRadius: BorderRadius.circular(16),
                            border: Border.all(color: col.withValues(alpha: .3)),
                          ),
                          child: Row(
                            children: [
                              Container(
                                padding: const EdgeInsets.all(10),
                                decoration: BoxDecoration(
                                  color: col.withValues(alpha: .15),
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: Icon(icon, color: col, size: 22),
                              ),
                              const SizedBox(width: 14),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      t,
                                      style: GoogleFonts.poppins(
                                        fontSize: 13.5,
                                        fontWeight: FontWeight.w600,
                                        color: theme.textPrimary,
                                      ),
                                    ),
                                    Text(
                                      d,
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

                      const SizedBox(height: 24),

                      // CONSULTATION FEE BOX & CTA BUTTONS
                      Container(
                        padding: const EdgeInsets.all(18),
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: theme.isDark || theme.isMonsoon
                                ? [const Color(0xFF1E293B), const Color(0xFF334155)]
                                : [const Color(0xFFEFF6FF), const Color(0xFFDBEAFE)],
                          ),
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(color: theme.primaryAccent.withValues(alpha: .3)),
                        ),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  feeLbl,
                                  style: GoogleFonts.poppins(
                                    fontSize: 12.5,
                                    color: theme.textSecondary,
                                  ),
                                ),
                                Text(
                                  "₹350 / Consult",
                                  style: GoogleFonts.poppins(
                                    fontSize: 20,
                                    fontWeight: FontWeight.w700,
                                    color: theme.textPrimary,
                                  ),
                                ),
                              ],
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                              decoration: BoxDecoration(
                                color: const Color(0xFF10B981).withValues(alpha: .15),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  const Icon(Icons.verified_rounded,
                                      color: Color(0xFF10B981), size: 16),
                                  const SizedBox(width: 6),
                                  Text(
                                    theme.tr("Available Today", "ഇന്ന് ലഭ്യമാണ്"),
                                    style: GoogleFonts.poppins(
                                      fontSize: 12,
                                      fontWeight: FontWeight.w700,
                                      color: const Color(0xFF10B981),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),

                      const SizedBox(height: 20),

                      // BOOK CLINIC BUTTON
                      SizedBox(
                        width: double.infinity,
                        height: 54,
                        child: ElevatedButton.icon(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: theme.primaryAccent,
                            foregroundColor: Colors.white,
                            elevation: 0,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(16),
                            ),
                          ),
                          onPressed: () {
                            Navigator.pop(context);
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (_) => BookingScreen(doctor: doctor),
                              ),
                            );
                          },
                          icon: const Icon(Icons.calendar_month_rounded, size: 20),
                          label: Text(
                            bookBtnLbl,
                            style: GoogleFonts.poppins(
                              fontSize: 15.5,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ),

                      const SizedBox(height: 12),

                      // TELE-MEDICINE BUTTON
                      SizedBox(
                        width: double.infinity,
                        height: 52,
                        child: OutlinedButton.icon(
                          style: OutlinedButton.styleFrom(
                            foregroundColor: theme.textPrimary,
                            side: BorderSide(color: theme.borderColor, width: 1.5),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(16),
                            ),
                          ),
                          onPressed: () {
                            Navigator.pop(context);
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (_) => BookingScreen(doctor: doctor),
                              ),
                            );
                          },
                          icon: Icon(Icons.video_call_rounded, color: theme.primaryAccent, size: 22),
                          label: Text(
                            teleBtnLbl,
                            style: GoogleFonts.poppins(
                              fontSize: 14.5,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _RadarMapPainter extends CustomPainter {
  final double progress;
  final Color radarColor;
  final bool isDark;
  final double distanceKm;
  final String docName;

  _RadarMapPainter({
    required this.progress,
    required this.radarColor,
    required this.isDark,
    required this.distanceKm,
    required this.docName,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width * 0.35, size.height * 0.5);
    final maxRadius = math.min(size.width, size.height) * 0.75;

    // Draw grid rings
    final gridPaint = Paint()
      ..color = (isDark ? Colors.white : Colors.black).withValues(alpha: .08)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.0;

    for (int i = 1; i <= 4; i++) {
      canvas.drawCircle(center, (maxRadius / 4) * i, gridPaint);
    }

    // Draw crosshairs
    canvas.drawLine(Offset(center.dx - maxRadius, center.dy), Offset(center.dx + maxRadius, center.dy), gridPaint);
    canvas.drawLine(Offset(center.dx, center.dy - maxRadius), Offset(center.dx, center.dy + maxRadius), gridPaint);

    // Draw sweeping radar beam
    final sweepAngle = 2 * math.pi * progress;
    final beamPaint = Paint()
      ..shader = SweepGradient(
        center: Alignment(
          (center.dx / (size.width / 2)) - 1,
          (center.dy / (size.height / 2)) - 1,
        ),
        startAngle: sweepAngle - (math.pi / 3),
        endAngle: sweepAngle,
        colors: [
          radarColor.withValues(alpha: .0),
          radarColor.withValues(alpha: .35),
        ],
      ).createShader(Rect.fromCircle(center: center, radius: maxRadius));

    canvas.drawCircle(center, maxRadius, beamPaint);

    // Draw center user dot (You)
    final userDotPaint = Paint()..color = const Color(0xFF10B981);
    canvas.drawCircle(center, 6, userDotPaint);
    final userWhitePaint = Paint()..color = Colors.white;
    canvas.drawCircle(center, 2.5, userWhitePaint);

    // Draw Doctor pin
    final angle = math.pi * 0.18; // Fixed angle towards top right
    final distRatio = math.min(1.0, distanceKm / 6.0);
    final docPos = Offset(
      center.dx + math.cos(angle) * (maxRadius * distRatio * 0.8),
      center.dy - math.sin(angle) * (maxRadius * distRatio * 0.8),
    );

    // Pin pulse glow
    final pulseRadius = 8.0 + (math.sin(progress * 2 * math.pi) * 4.0).abs();
    final pulsePaint = Paint()
      ..color = const Color(0xFFEF4444).withValues(alpha: .3)
      ..style = PaintingStyle.fill;
    canvas.drawCircle(docPos, pulseRadius, pulsePaint);

    final docDotPaint = Paint()..color = const Color(0xFFEF4444);
    canvas.drawCircle(docPos, 6, docDotPaint);
    canvas.drawCircle(docPos, 2.5, userWhitePaint);

    // Doctor label
    final labelSpan = TextSpan(
      text: "📍 Dr. $docName (${distanceKm}km)",
      style: GoogleFonts.poppins(
        color: isDark ? Colors.white : const Color(0xFF0F172A),
        fontSize: 11,
        fontWeight: FontWeight.w700,
      ),
    );
    final labelPainter = TextPainter(text: labelSpan, textDirection: TextDirection.ltr);
    labelPainter.layout();

    // Draw label background badge
    final bgRect = Rect.fromCenter(
      center: Offset(docPos.dx + labelPainter.width / 2 + 10, docPos.dy - 12),
      width: labelPainter.width + 12,
      height: labelPainter.height + 6,
    );
    final bgPaint = Paint()
      ..color = (isDark ? const Color(0xFF1E293B) : Colors.white).withValues(alpha: .9)
      ..style = PaintingStyle.fill;
    canvas.drawRRect(RRect.fromRectAndRadius(bgRect, const Radius.circular(8)), bgPaint);

    labelPainter.paint(canvas, Offset(bgRect.left + 6, bgRect.top + 3));

    // User label "You"
    final youSpan = TextSpan(
      text: "You (Kozhikode)",
      style: GoogleFonts.poppins(
        color: const Color(0xFF10B981),
        fontSize: 10,
        fontWeight: FontWeight.w700,
      ),
    );
    final youPainter = TextPainter(text: youSpan, textDirection: TextDirection.ltr);
    youPainter.layout();
    youPainter.paint(canvas, Offset(center.dx - youPainter.width / 2, center.dy + 8));
  }

  @override
  bool shouldRepaint(covariant _RadarMapPainter oldDelegate) {
    return oldDelegate.progress != progress ||
        oldDelegate.radarColor != radarColor ||
        oldDelegate.isDark != isDark;
  }
}
