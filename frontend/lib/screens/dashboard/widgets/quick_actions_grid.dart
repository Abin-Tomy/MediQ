import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../../core/theme/app_colors.dart';
import '../../../widgets/cards/quick_action_card.dart';
import '../../symptom/ai_welcome_screen.dart';
import '../../report/report_upload_screen.dart';
import '../../doctor/doctor_list_screen.dart';
import '../../appointment/appointments_screen.dart';
import 'medicine_list_screen.dart';
import 'hospital_list_screen.dart';

class QuickActionsGrid extends StatelessWidget {
  const QuickActionsGrid({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              children: [
                Container(
                  width: 6,
                  height: 22,
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [Color(0xFF2F80ED), Color(0xFF56CCF2)],
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                    ),
                    borderRadius: BorderRadius.circular(4),
                  ),
                ),
                const SizedBox(width: 10),
                Text(
                  "Quick Actions",
                  style: GoogleFonts.poppins(
                    fontSize: 20,
                    fontWeight: FontWeight.w700,
                    color: AppColors.textPrimary,
                  ),
                ),
              ],
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: const Color(0xFFEAF4FF),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                "6 Modules",
                style: GoogleFonts.poppins(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: AppColors.primary,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 18),
        GridView.count(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisCount: 2,
          crossAxisSpacing: 16,
          mainAxisSpacing: 16,
          childAspectRatio: .92,
          children: [
            QuickActionCard(
              icon: Icons.psychology_alt_rounded,
              title: "Symptom Checker",
              subtitle: "AI Powered (Model 1 & 2)",
              gradientColors: const [Color(0xFF0072FF), Color(0xFF00C6FF)],
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => const AIWelcomeScreen(),
                  ),
                );
              },
            ),
            QuickActionCard(
              icon: Icons.description_outlined,
              title: "Medical Reports",
              subtitle: "T5-small Summarizer",
              gradientColors: const [Color(0xFF11998E), Color(0xFF38EF7D)],
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => const ReportUploadScreen(),
                  ),
                );
              },
            ),
            QuickActionCard(
              icon: Icons.local_hospital_rounded,
              title: "Doctors",
              subtitle: "Find Specialists",
              gradientColors: const [Color(0xFFFF416C), Color(0xFFFF4B2B)],
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => const DoctorListScreen(),
                  ),
                );
              },
            ),
            QuickActionCard(
              icon: Icons.calendar_month_rounded,
              title: "Appointments",
              subtitle: "Book Visits (2 Taps)",
              gradientColors: const [Color(0xFFF7971E), Color(0xFFFFD200)],
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => const AppointmentsScreen(),
                  ),
                );
              },
            ),
            QuickActionCard(
              icon: Icons.medication_rounded,
              title: "Medicines",
              subtitle: "Monsoon Prophylaxis",
              gradientColors: const [Color(0xFF8A2387), Color(0xFFE94057)],
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => const MedicineListScreen(),
                  ),
                );
              },
            ),
            QuickActionCard(
              icon: Icons.location_on_rounded,
              title: "Nearby Hospitals",
              subtitle: "Casualty Care",
              gradientColors: const [Color(0xFFED213A), Color(0xFF93291E)],
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => const HospitalListScreen(),
                  ),
                );
              },
            ),
          ],
        ),
      ],
    );
  }
}