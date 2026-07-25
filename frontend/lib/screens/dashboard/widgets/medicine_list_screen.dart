import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../../core/theme/app_colors.dart';

class MedicineListScreen extends StatefulWidget {
  const MedicineListScreen({super.key});

  @override
  State<MedicineListScreen> createState() => _MedicineListScreenState();
}

class _MedicineListScreenState extends State<MedicineListScreen> {
  final List<Map<String, dynamic>> _medicines = [
    {
      "name": "Paracetamol (Dolo 650)",
      "dosage": "1 Tablet (650mg)",
      "time": "08:30 AM — After Breakfast",
      "taken": true,
      "color": const Color(0xFF2F80ED),
      "purpose": "Fever reduction & body pain",
    },
    {
      "name": "Doxycycline Prophylaxis",
      "dosage": "1 Capsule (100mg)",
      "time": "01:30 PM — After Lunch",
      "taken": false,
      "color": const Color(0xFF9B51E0),
      "purpose": "Leptospirosis / flood exposure prevention",
    },
    {
      "name": "Vitamin C & Zinc Supp.",
      "dosage": "1 Chewable Tablet",
      "time": "09:00 PM — Before Bed",
      "taken": false,
      "color": const Color(0xFF27AE60),
      "purpose": "Immune system support",
    },
    {
      "name": "ORS / Electrolyte Drink",
      "dosage": "1 Sachet in 1L Water",
      "time": "Throughout the day",
      "taken": true,
      "color": const Color(0xFFF2994A),
      "purpose": "Hydration maintenance",
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
          "Medication Reminders",
          style: GoogleFonts.poppins(
            color: AppColors.textPrimary,
            fontWeight: FontWeight.w600,
            fontSize: 18,
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.add_alert_rounded, color: AppColors.primary),
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text(
                    "Reminder preset added to daily schedule.",
                    style: GoogleFonts.poppins(),
                  ),
                ),
              );
            },
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // INFO BANNER
            Container(
              margin: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFFF3E8FF), Color(0xFFE9D5FF)],
                ),
                borderRadius: BorderRadius.circular(18),
                border: Border.all(color: const Color(0xFF9B51E0).withValues(alpha: .3)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.medication_liquid_rounded,
                      color: Color(0xFF9B51E0), size: 28),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          "Monsoon Care Schedule",
                          style: GoogleFonts.poppins(
                            fontSize: 14.5,
                            fontWeight: FontWeight.w700,
                            color: const Color(0xFF581C87),
                          ),
                        ),
                        Text(
                          "Keep track of your antiviral and prophylaxis dosage to ensure rapid recovery.",
                          style: GoogleFonts.poppins(
                            fontSize: 12,
                            color: const Color(0xFF6B21A8),
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
                itemCount: _medicines.length,
                separatorBuilder: (_, __) => const SizedBox(height: 14),
                itemBuilder: (_, idx) {
                  final med = _medicines[idx];
                  final bool taken = med['taken'] as bool;
                  final Color col = med['color'] as Color;

                  return Container(
                    padding: const EdgeInsets.all(18),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(
                        color: taken ? const Color(0xFF27AE60).withValues(alpha: .4) : AppColors.border,
                      ),
                      boxShadow: const [
                        BoxShadow(
                          color: Color(0x0A000000),
                          blurRadius: 10,
                          offset: Offset(0, 4),
                        ),
                      ],
                    ),
                    child: Row(
                      children: [
                        Container(
                          width: 50,
                          height: 50,
                          decoration: BoxDecoration(
                            color: col.withValues(alpha: .12),
                            borderRadius: BorderRadius.circular(16),
                          ),
                          child: Icon(Icons.medication_rounded, color: col, size: 26),
                        ),
                        const SizedBox(width: 14),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                med['name'] as String,
                                style: GoogleFonts.poppins(
                                  fontSize: 16,
                                  fontWeight: FontWeight.w700,
                                  color: taken ? AppColors.textSecondary : AppColors.textPrimary,
                                  decoration: taken ? TextDecoration.lineThrough : null,
                                ),
                              ),
                              Text(
                                "${med['dosage']} • ${med['purpose']}",
                                style: GoogleFonts.poppins(
                                  fontSize: 12,
                                  color: AppColors.textHint,
                                ),
                              ),
                              const SizedBox(height: 6),
                              Row(
                                children: [
                                  const Icon(Icons.access_time_rounded,
                                      size: 14, color: AppColors.primary),
                                  const SizedBox(width: 6),
                                  Text(
                                    med['time'] as String,
                                    style: GoogleFonts.poppins(
                                      fontSize: 12.5,
                                      fontWeight: FontWeight.w600,
                                      color: AppColors.primary,
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 10),
                        GestureDetector(
                          onTap: () {
                            setState(() {
                              med['taken'] = !taken;
                            });
                          },
                          child: Container(
                            width: 38,
                            height: 38,
                            decoration: BoxDecoration(
                              color: taken ? const Color(0xFF27AE60) : Colors.transparent,
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(
                                color: taken ? const Color(0xFF27AE60) : AppColors.textHint,
                                width: 2,
                              ),
                            ),
                            child: taken
                                ? const Icon(Icons.check_rounded, color: Colors.white, size: 22)
                                : null,
                          ),
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
