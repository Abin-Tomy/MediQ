import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../../core/theme/app_colors.dart';

class HospitalListScreen extends StatelessWidget {
  const HospitalListScreen({super.key});

  final List<Map<String, dynamic>> _hospitals = const [
    {
      "name": "Baby Memorial Hospital (BMH)",
      "address": "Indira Gandhi Rd, Arayidathupalam, Kozhikode",
      "distance": "0.8 km away",
      "phone": "0495 272 3272",
      "emergency": "24/7 casualty & ICU care available",
      "specialty": "Multi-Specialty Emergency Care",
      "color": Color(0xFFEB5757),
    },
    {
      "name": "Aster MIMS Kozhikode",
      "address": "Mini Bypass Rd, Govindapuram, Kozhikode",
      "distance": "2.1 km away",
      "phone": "0495 248 8000",
      "emergency": "Dedicated Infectious Disease Isolation Ward",
      "specialty": "Epidemic & Virology Referral",
      "color": Color(0xFF2F80ED),
    },
    {
      "name": "Government Medical College, Kozhikode",
      "address": "Medical College Campus Rd, Calicut",
      "distance": "5.5 km away",
      "phone": "0495 235 0216",
      "emergency": "State Nipah & Tropical Fever Referral Centre",
      "specialty": "Public Health & Critical Virology",
      "color": Color(0xFF27AE60),
    },
    {
      "name": "Iqraa International Hospital",
      "address": "Civil Station, Malaparamba, Kozhikode",
      "distance": "4.2 km away",
      "phone": "0495 237 9100",
      "emergency": "24/7 Rapid Diagnostic Laboratory",
      "specialty": "General Medicine & Pediatrics",
      "color": Color(0xFFF2994A),
    },
    {
      "name": "Malabar Hospitals & Urology Centre",
      "address": "Eranhipalam, Kozhikode",
      "distance": "3.2 km away",
      "phone": "0495 276 0000",
      "emergency": "Casualty & Outpatient consultation",
      "specialty": "General Care & Diagnostics",
      "color": Color(0xFF9B51E0),
    },
  ];

  @override
  Widget build(BuildContext context) {
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
          "Nearby Emergency Care",
          style: GoogleFonts.poppins(
            color: AppColors.textPrimary,
            fontWeight: FontWeight.w600,
            fontSize: 18,
          ),
        ),
      ),
      body: SafeArea(
        child: Column(
          children: [
            // LOCATION BANNER
            Container(
              margin: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFFFFF5F5), Color(0xFFFFE3E3)],
                ),
                borderRadius: BorderRadius.circular(18),
                border: Border.all(color: const Color(0xFFEB5757).withValues(alpha: .4)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.emergency_rounded,
                      color: Color(0xFFEB5757), size: 28),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          "Kozhikode Casualty Locator",
                          style: GoogleFonts.poppins(
                            fontSize: 14.5,
                            fontWeight: FontWeight.w700,
                            color: const Color(0xFF9B1C1C),
                          ),
                        ),
                        Text(
                          "In case of acute symptoms (low platelets, breathing distress), visit the nearest casualty immediately.",
                          style: GoogleFonts.poppins(
                            fontSize: 12,
                            color: const Color(0xFF771D1D),
                            height: 1.3,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 12),

            Expanded(
              child: ListView.separated(
                padding: const EdgeInsets.fromLTRB(24, 10, 24, 30),
                physics: const BouncingScrollPhysics(),
                itemCount: _hospitals.length,
                separatorBuilder: (_, __) => const SizedBox(height: 16),
                itemBuilder: (_, idx) {
                  final hosp = _hospitals[idx];
                  final Color col = hosp['color'] as Color;

                  return Container(
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
                            Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 10, vertical: 4),
                              decoration: BoxDecoration(
                                color: col.withValues(alpha: .12),
                                borderRadius: BorderRadius.circular(10),
                              ),
                              child: Text(
                                hosp['specialty'] as String,
                                style: GoogleFonts.poppins(
                                  fontSize: 11.5,
                                  fontWeight: FontWeight.w700,
                                  color: col,
                                ),
                              ),
                            ),
                            Row(
                              children: [
                                const Icon(Icons.directions_walk_rounded,
                                    size: 14, color: AppColors.textSecondary),
                                Text(
                                  hosp['distance'] as String,
                                  style: GoogleFonts.poppins(
                                    fontSize: 12,
                                    fontWeight: FontWeight.w600,
                                    color: AppColors.textSecondary,
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        Text(
                          hosp['name'] as String,
                          style: GoogleFonts.poppins(
                            fontSize: 17,
                            fontWeight: FontWeight.w700,
                            color: AppColors.textPrimary,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Icon(Icons.place_rounded,
                                size: 16, color: AppColors.textHint),
                            const SizedBox(width: 6),
                            Expanded(
                              child: Text(
                                hosp['address'] as String,
                                style: GoogleFonts.poppins(
                                  fontSize: 13,
                                  color: AppColors.textSecondary,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Row(
                          children: [
                            const Icon(Icons.info_outline_rounded,
                                size: 16, color: Color(0xFFEB5757)),
                            const SizedBox(width: 6),
                            Expanded(
                              child: Text(
                                hosp['emergency'] as String,
                                style: GoogleFonts.poppins(
                                  fontSize: 12.5,
                                  fontWeight: FontWeight.w600,
                                  color: const Color(0xFF9B1C1C),
                                ),
                              ),
                            ),
                          ],
                        ),
                        const Divider(height: 24),
                        Row(
                          children: [
                            Expanded(
                              child: OutlinedButton.icon(
                                style: OutlinedButton.styleFrom(
                                  foregroundColor: AppColors.primary,
                                  side: const BorderSide(color: AppColors.primary),
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(14),
                                  ),
                                ),
                                onPressed: () {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    SnackBar(
                                      content: Text(
                                        "Calling Casualty: ${hosp['phone']}...",
                                        style: GoogleFonts.poppins(),
                                      ),
                                    ),
                                  );
                                },
                                icon: const Icon(Icons.phone_rounded, size: 18),
                                label: Text(
                                  "Call Casualty",
                                  style: GoogleFonts.poppins(
                                    fontSize: 13.5,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: ElevatedButton.icon(
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: AppColors.primary,
                                  foregroundColor: Colors.white,
                                  elevation: 0,
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(14),
                                  ),
                                ),
                                onPressed: () {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    SnackBar(
                                      content: Text(
                                        "Opening Maps navigation to ${hosp['name']}...",
                                        style: GoogleFonts.poppins(),
                                      ),
                                    ),
                                  );
                                },
                                icon: const Icon(Icons.navigation_rounded, size: 18),
                                label: Text(
                                  "Navigate",
                                  style: GoogleFonts.poppins(
                                    fontSize: 13.5,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
