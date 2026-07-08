import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_text_styles.dart';

class DashboardHeader extends StatelessWidget {
  final String userName;
  final bool isGuest;
  final VoidCallback? onLogout;

  const DashboardHeader({
    super.key,
    required this.userName,
    this.isGuest = false,
    this.onLogout,
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

              Row(
                children: [
                  Flexible(
                    child: Text(
                      userName,
                      style: AppTextStyles.display,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  if (isGuest) ...[
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 8,
                        vertical: 3,
                      ),
                      decoration: BoxDecoration(
                        color: const Color(0xFFF2994A).withValues(alpha: .15),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        'GUEST',
                        style: GoogleFonts.poppins(
                          fontSize: 10,
                          fontWeight: FontWeight.w700,
                          color: const Color(0xFFF2994A),
                          letterSpacing: 0.5,
                        ),
                      ),
                    ),
                  ],
                ],
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

        GestureDetector(
          onTap: onLogout,
          child: CircleAvatar(
            radius: 27,
            backgroundColor: isGuest
                ? const Color(0xFFF2994A)
                : AppColors.primary,
            child: Icon(
              isGuest ? Icons.login_rounded : Icons.person,
              color: Colors.white,
            ),
          ),
        ),
      ],
    );
  }
}