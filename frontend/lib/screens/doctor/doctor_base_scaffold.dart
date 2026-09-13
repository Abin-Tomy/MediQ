import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import 'doctor_dashboard_screen.dart';
import 'doctor_availability_screen.dart';
import 'doctor_appointments_screen.dart';
import 'doctor_profile_screen.dart';

class DoctorBaseScaffold extends StatefulWidget {
  const DoctorBaseScaffold({super.key});

  @override
  State<DoctorBaseScaffold> createState() => _DoctorBaseScaffoldState();
}

class _DoctorBaseScaffoldState extends State<DoctorBaseScaffold> {
  int _currentIndex = 0;

  final List<Widget> _pages = [
    const DoctorDashboardScreen(),
    const DoctorAppointmentsScreen(),
    const DoctorAvailabilityScreen(),
    const DoctorProfileScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _pages,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        backgroundColor: Colors.white,
        indicatorColor: AppColors.primaryLight,
        destinations: const [
          NavigationDestination(icon: Icon(Icons.dashboard_rounded), label: 'Home'),
          NavigationDestination(icon: Icon(Icons.calendar_month_rounded), label: 'Visits'),
          NavigationDestination(icon: Icon(Icons.access_time_filled_rounded), label: 'Hours'),
          NavigationDestination(icon: Icon(Icons.person_rounded), label: 'Profile'),
        ],
      ),
    );
  }
}
