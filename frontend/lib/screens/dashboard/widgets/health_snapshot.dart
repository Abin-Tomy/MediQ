import 'package:flutter/material.dart';

import '../../../core/theme/app_text_styles.dart';
import '../../../widgets/cards/health_metric_card.dart';

class HealthSnapshot extends StatelessWidget {
  const HealthSnapshot({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [

        Text(
          "Today's Health",
          style: AppTextStyles.heading,
        ),

        const SizedBox(height: 20),

        GridView.count(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisCount: 2,
          crossAxisSpacing: 16,
          mainAxisSpacing: 16,
          childAspectRatio: 1.05,

          children: const [

            HealthMetricCard(
              icon: Icons.favorite_rounded,
              iconColor: Colors.red,
              title: "Heart Rate",
              value: "72",
              unit: "bpm",
            ),

            HealthMetricCard(
              icon: Icons.bedtime_rounded,
              iconColor: Colors.indigo,
              title: "Sleep",
              value: "7.5",
              unit: "hrs",
            ),

            HealthMetricCard(
              icon: Icons.water_drop_rounded,
              iconColor: Colors.lightBlue,
              title: "Water",
              value: "5 / 8",
            ),

            HealthMetricCard(
              icon: Icons.monitor_heart_rounded,
              iconColor: Colors.green,
              title: "Wellness",
              value: "92",
              unit: "%",
              subtitle: "Excellent",
            ),
          ],
        ),
      ],
    );
  }
}