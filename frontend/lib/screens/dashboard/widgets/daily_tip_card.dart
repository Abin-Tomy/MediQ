import 'package:flutter/material.dart';

import '../../../core/theme/app_text_styles.dart';

class DailyTipCard extends StatelessWidget {
  const DailyTipCard({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Color(0xffFFF8D6),
            Color(0xffFFE082),
          ],
        ),
        borderRadius: BorderRadius.circular(28),
        boxShadow: [
          BoxShadow(
            color: Colors.amber.withValues(alpha: .18),
            blurRadius: 28,
            offset: const Offset(0, 15),
          ),
        ],
      ),

      child: Stack(
        children: [

          Positioned(
            right: -25,
            top: -25,
            child: Container(
              width: 120,
              height: 120,
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: .18),
                shape: BoxShape.circle,
              ),
            ),
          ),

          Positioned(
            bottom: -35,
            left: -35,
            child: Container(
              width: 90,
              height: 90,
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: .12),
                shape: BoxShape.circle,
              ),
            ),
          ),

          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [

              Row(
                children: [

                  Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(18),
                    ),
                    child: const Icon(
                      Icons.lightbulb_rounded,
                      color: Colors.orange,
                      size: 30,
                    ),
                  ),

                  const SizedBox(width: 16),

                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [

                        Text(
                          "Today's AI Health Tip",
                          style: AppTextStyles.heading.copyWith(
                            fontSize: 20,
                          ),
                        ),

                        const SizedBox(height: 4),

                        Text(
                          "Generated just for you",
                          style: AppTextStyles.caption,
                        ),
                      ],
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 28),

              Text(
                "💧 Drink 3 more glasses of water today to improve hydration and reduce fatigue.",
                style: AppTextStyles.body.copyWith(
                  height: 1.7,
                  fontSize: 16,
                ),
              ),

              const SizedBox(height: 24),

              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 18,
                  vertical: 14,
                ),
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: .75),
                  borderRadius: BorderRadius.circular(18),
                ),
                child: const Row(
                  children: [

                    Icon(
                      Icons.auto_awesome,
                      color: Colors.orange,
                    ),

                    SizedBox(width: 12),

                    Expanded(
                      child: Text(
                        "Hydration improves memory, focus and mood throughout the day.",
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 24),

              Align(
                alignment: Alignment.centerRight,
                child: FilledButton.icon(
                  style: FilledButton.styleFrom(
                    backgroundColor: Colors.orange,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(
                      horizontal: 22,
                      vertical: 16,
                    ),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(18),
                    ),
                  ),
                  onPressed: () {},

                  icon: const Icon(Icons.arrow_forward),

                  label: const Text("Learn More"),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}