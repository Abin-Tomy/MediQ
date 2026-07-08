import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../auth/login_screen.dart';
import 'widgets/dashboard_header.dart';
import 'widgets/dashboard_search_bar.dart';
import 'widgets/ai_hero_card.dart';
import 'widgets/health_snapshot.dart';
import 'widgets/appointment_card.dart';
import 'widgets/quick_actions_grid.dart';
import 'widgets/daily_tip_card.dart';
import 'widgets/dashboard_bottom_nav.dart';
import '../symptom/ai_welcome_screen.dart';

class DashboardScreen extends StatefulWidget {
  final String userName;
  final bool isGuest;

  const DashboardScreen({
    super.key,
    required this.userName,
    this.isGuest = false,
  });

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {

  int currentIndex = 0;

  void _handleLogout() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(24),
        ),
        title: Text(
          widget.isGuest ? 'Exit Guest Mode?' : 'Sign Out?',
          style: GoogleFonts.poppins(fontWeight: FontWeight.w600),
        ),
        content: Text(
          widget.isGuest
              ? 'You will return to the login screen. Create an account to save your data.'
              : 'Are you sure you want to sign out?',
          style: GoogleFonts.poppins(),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: Text(
              'Cancel',
              style: GoogleFonts.poppins(color: Colors.grey.shade600),
            ),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(ctx);
              Navigator.pushReplacement(
                context,
                PageRouteBuilder(
                  pageBuilder: (_, __, ___) => const LoginScreen(),
                  transitionsBuilder: (_, animation, __, child) {
                    return FadeTransition(
                      opacity: animation,
                      child: child,
                    );
                  },
                  transitionDuration: const Duration(milliseconds: 400),
                ),
              );
            },
            child: Text(
              widget.isGuest ? 'Exit' : 'Sign Out',
              style: GoogleFonts.poppins(
                color: const Color(0xFFEB5757),
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {

    return Scaffold(

      backgroundColor: const Color(0xffF8FAFC),

      bottomNavigationBar: DashboardBottomNav(
        currentIndex: currentIndex,
        onTap: (index) {
          setState(() {
            currentIndex = index;
          });
        },
      ),

      body: SafeArea(

        child: SingleChildScrollView(

          physics: const BouncingScrollPhysics(),

          padding: const EdgeInsets.fromLTRB(
            24,
            20,
            24,
            30,
          ),

          child: Column(

            crossAxisAlignment: CrossAxisAlignment.start,

            children: [

              //-------------------------------------------------------
              // GUEST BANNER
              //-------------------------------------------------------

              if (widget.isGuest) ...[
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 12,
                  ),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [Color(0xFFFFF3E0), Color(0xFFFFE0B2)],
                    ),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                      color: const Color(0xFFF2994A).withValues(alpha: .3),
                    ),
                  ),
                  child: Row(
                    children: [
                      const Icon(
                        Icons.info_outline_rounded,
                        color: Color(0xFFF2994A),
                        size: 22,
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          "You're in Guest Mode. Sign up to save your data.",
                          style: GoogleFonts.poppins(
                            fontSize: 12.5,
                            fontWeight: FontWeight.w500,
                            color: const Color(0xFF8B5E34),
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      GestureDetector(
                        onTap: () {
                          Navigator.pushReplacement(
                            context,
                            MaterialPageRoute(
                              builder: (_) => const LoginScreen(),
                            ),
                          );
                        },
                        child: Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 12,
                            vertical: 6,
                          ),
                          decoration: BoxDecoration(
                            color: const Color(0xFFF2994A),
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Text(
                            "Sign Up",
                            style: GoogleFonts.poppins(
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                              color: Colors.white,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),
              ],

              //-------------------------------------------------------
              // HEADER
              //-------------------------------------------------------

              DashboardHeader(
                userName: widget.userName,
                isGuest: widget.isGuest,
                onLogout: _handleLogout,
              ),

              const SizedBox(height: 28),

              //-------------------------------------------------------
              // AI HERO
              //-------------------------------------------------------

             AIHeroCard(
  userName: "Vishnu",
  onStart: () {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => const AIWelcomeScreen(),
      ),
    );
  },
),

              const SizedBox(height: 28),

              //-------------------------------------------------------
              // SEARCH
              //-------------------------------------------------------

              DashboardSearchBar(
                onTap: () {},
              ),

              const SizedBox(height: 34),

              //-------------------------------------------------------
              // HEALTH
              //-------------------------------------------------------

              const HealthSnapshot(),

              const SizedBox(height: 34),

              //-------------------------------------------------------
              // APPOINTMENT
              //-------------------------------------------------------

              const AppointmentCard(),

              const SizedBox(height: 34),

              //-------------------------------------------------------
              // QUICK ACTIONS
              //-------------------------------------------------------

              const QuickActionsGrid(),

              const SizedBox(height: 34),

              //-------------------------------------------------------
              // DAILY TIP
              //-------------------------------------------------------

              const DailyTipCard(),

              const SizedBox(height: 40),

            ],
          ),
        ),
      ),
    );
  }
}