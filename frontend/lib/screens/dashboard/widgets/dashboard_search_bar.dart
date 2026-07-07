import 'package:flutter/material.dart';

import '../../../core/theme/app_colors.dart';

class DashboardSearchBar extends StatelessWidget {
  final VoidCallback? onTap;

  const DashboardSearchBar({
    super.key,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(22),
        onTap: onTap,
        child: Ink(
          height: 64,
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(22),
            boxShadow: const [
              BoxShadow(
                color: AppColors.shadow,
                blurRadius: 18,
                offset: Offset(0, 8),
              ),
            ],
          ),
          child: Row(
            children: [
              const SizedBox(width: 20),

              const Icon(
                Icons.search_rounded,
                color: AppColors.primary,
                size: 28,
              ),

              const SizedBox(width: 16),

              const Expanded(
                child: Text(
                  "Search symptoms, doctors, reports...",
                  style: TextStyle(
                    fontSize: 15,
                    color: AppColors.textHint,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),

              Container(
                margin: const EdgeInsets.only(right: 12),
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: AppColors.primary.withValues(alpha: .12),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: const Icon(
                  Icons.mic_none_rounded,
                  color: AppColors.primary,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}