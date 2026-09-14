import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../auth/login_screen.dart';
import 'widgets/dashboard_header.dart';
import 'widgets/dashboard_search_bar.dart';
import 'widgets/appointment_card.dart';
import 'widgets/popular_doctors_list.dart';
import 'widgets/dashboard_bottom_nav.dart';
import '../appointment/appointments_screen.dart';
import '../report/report_upload_screen.dart';
import '../profile/profile_screen.dart';
import '../doctor/doctor_list_screen.dart';
import '../../core/theme/app_theme_provider.dart';
import '../../core/theme/app_text_styles.dart';

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
    return AnimatedBuilder(
      animation: AppThemeProvider(),
      builder: (context, _) {
        final theme = AppThemeProvider();

        return Scaffold(
          extendBody: true,
          backgroundColor: theme.background,
          bottomNavigationBar: DashboardBottomNav(
            currentIndex: currentIndex,
            onTap: (index) {
              if (index == 1) {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const AppointmentsScreen()),
                );
              } else if (index == 2) {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const ReportUploadScreen()), // We can change this to messages later
                );
              } else if (index == 3) {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const ProfileScreen()),
                );
              } else {
                setState(() {
                  currentIndex = index;
                });
              }
            },
          ),
          body: SafeArea(
            child: SingleChildScrollView(
              physics: const BouncingScrollPhysics(),
              padding: const EdgeInsets.fromLTRB(24, 20, 24, 30),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
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

                  DashboardHeader(
                    userName: widget.userName,
                    isGuest: widget.isGuest,
                    onLogout: _handleLogout,
                  ),

                  const SizedBox(height: 32),
                  
                  Text(
                    "How are your feeling\ntoday?",
                    style: AppTextStyles.display.copyWith(
                      fontSize: 28,
                      height: 1.2,
                    ),
                  ),

                  const SizedBox(height: 24),

                  DashboardSearchBar(
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => const DoctorListScreen()),
                      );
                    },
                  ),

                  const SizedBox(height: 34),

                  const AppointmentCard(),

                  const SizedBox(height: 34),

                  const PopularDoctorsList(),

                  const SizedBox(height: 40),

                ],
              ),
            ),
          ),
        );
      },
    );
  }
}