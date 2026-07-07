import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';

/// Universal card widget used throughout the application.
class AppCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  final Gradient? gradient;
  final VoidCallback? onTap;
  final double borderRadius;
  final bool showShadow;

  const AppCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(20),
    this.gradient,
    this.onTap,
    this.borderRadius = 24,
    this.showShadow = true,
  });

  @override
  Widget build(BuildContext context) {
    final card = AnimatedContainer(
      duration: const Duration(milliseconds: 250),
      padding: padding,
      decoration: BoxDecoration(
        color: gradient == null ? AppColors.card : null,
        gradient: gradient,
        borderRadius: BorderRadius.circular(borderRadius),
        boxShadow: showShadow
            ? const [
                BoxShadow(
                  color: AppColors.shadow,
                  blurRadius: 24,
                  offset: Offset(0, 10),
                )
              ]
            : null,
      ),
      child: child,
    );

    if (onTap == null) return card;

    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(borderRadius),
        onTap: onTap,
        child: card,
      ),
    );
  }
}
