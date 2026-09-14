import 'package:flutter/material.dart';
import '../dashboard/patient_dashboard.dart';
import '../appointment/appointments_screen.dart';
import '../dashboard/widgets/dashboard_bottom_nav.dart';
import 'patient_profile_screen.dart';

class PatientBaseScaffold extends StatefulWidget {
  const PatientBaseScaffold({super.key});

  @override
  State<PatientBaseScaffold> createState() => _PatientBaseScaffoldState();
}

class _PatientBaseScaffoldState extends State<PatientBaseScaffold> {
  int _currentIndex = 0;

  final List<Widget> _pages = [
    const PatientDashboard(userName: "Sarah"),
    const AppointmentsScreen(), // Ensure this widget exists
    const Center(child: Text('Messages/Notifications (Coming Soon)')),
    const PatientProfileScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _pages,
      ),
      bottomNavigationBar: DashboardBottomNav(
        currentIndex: _currentIndex,
        onTap: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
      ),
    );
  }
}
