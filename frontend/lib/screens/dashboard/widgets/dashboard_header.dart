import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_text_styles.dart';

class DashboardHeader extends StatelessWidget {
  final String userName;

  const DashboardHeader({
    super.key,
    required this.userName,
  });

  String _getGreeting() {
    final hour = DateTime.now().hour;

    if (hour < 12) {
      return "Good Morning";
    } else if (hour < 17) {
      return "Good Afternoon";
    } else {
      return "Good Evening";
    }
  }

  @override
  Widget build(BuildContext context) {
    final date = DateFormat("EEEE, d MMMM").format(DateTime.now());

    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [

              Text(
                _getGreeting(),
                style: AppTextStyles.caption.copyWith(
                  fontSize: 16,
                ),
              ),

              const SizedBox(height: 6),

              Text(
                userName,
                style: AppTextStyles.display,
              ),

              const SizedBox(height: 6),

              Text(
                date,
                style: AppTextStyles.caption,
              ),
            ],
          ),
        ),

        Container(
          height: 55,
          width: 55,
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(18),
            boxShadow: const [
              BoxShadow(
                color: AppColors.shadow,
                blurRadius: 18,
                offset: Offset(0, 8),
              ),
            ],
          ),
          child: IconButton(
            onPressed: () {},
            icon: const Icon(
              Icons.notifications_none_rounded,
              color: AppColors.textPrimary,
            ),
          ),
        ),

        const SizedBox(width: 14),

        const CircleAvatar(
          radius: 27,
          backgroundColor: AppColors.primary,
          child: Icon(
            Icons.person,
            color: Colors.white,
          ),
        ),
      ],
    );
  }
}