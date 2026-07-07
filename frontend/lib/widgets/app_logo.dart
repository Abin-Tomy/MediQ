import 'package:flutter/material.dart';

class AppLogo extends StatelessWidget {
  final double size;

  const AppLogo({super.key, this.size = 110});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,

      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF2F80ED), Color(0xFF56CCF2)],
        ),
        borderRadius: BorderRadius.circular(28),

        boxShadow: [
          BoxShadow(
            color: Colors.blue.withValues(alpha: .25),
            blurRadius: 25,
            offset: const Offset(0, 12),
          ),
        ],
      ),

      child: const Icon(
        Icons.monitor_heart_rounded,
        color: Colors.white,
        size: 58,
      ),
    );
  }
}
