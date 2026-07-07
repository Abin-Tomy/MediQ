import 'package:flutter/material.dart';

import '../../../core/theme/app_text_styles.dart';
import '../../../widgets/cards/quick_action_card.dart';

class QuickActionsGrid extends StatelessWidget {
  const QuickActionsGrid({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [

        Text(
          "Quick Actions",
          style: AppTextStyles.heading,
        ),

        const SizedBox(height: 20),

        GridView.count(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisCount: 2,
          crossAxisSpacing: 16,
          mainAxisSpacing: 16,
          childAspectRatio: .95,

          children: const [

            QuickActionCard(
              icon: Icons.psychology_alt_rounded,
              title: "Symptom Checker",
              subtitle: "AI Powered",
              color: Colors.blue,
            ),

            QuickActionCard(
              icon: Icons.description_outlined,
              title: "Medical Reports",
              subtitle: "Analyze Reports",
              color: Colors.green,
            ),

            QuickActionCard(
              icon: Icons.local_hospital_rounded,
              title: "Doctors",
              subtitle: "Find Specialists",
              color: Colors.red,
            ),

            QuickActionCard(
              icon: Icons.calendar_month_rounded,
              title: "Appointments",
              subtitle: "Book Visits",
              color: Colors.orange,
            ),

            QuickActionCard(
              icon: Icons.medication_rounded,
              title: "Medicines",
              subtitle: "Reminders",
              color: Colors.purple,
            ),

            QuickActionCard(
              icon: Icons.location_on_rounded,
              title: "Nearby Hospitals",
              subtitle: "Emergency Care",
              color: Colors.teal,
            ),
          ],
        ),
      ],
    );
  }
}