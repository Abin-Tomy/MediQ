import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import 'admin_dashboard_screen.dart';
import 'admin_doctor_approval_screen.dart';
import 'admin_user_management_screen.dart';

class AdminBaseScaffold extends StatefulWidget {
  const AdminBaseScaffold({super.key});

  @override
  State<AdminBaseScaffold> createState() => _AdminBaseScaffoldState();
}

class _AdminBaseScaffoldState extends State<AdminBaseScaffold> {
  int _currentIndex = 0;

  final List<Widget> _pages = [
    const AdminDashboardScreen(),
    const AdminDoctorApprovalScreen(),
    const AdminUserManagementScreen(),
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
          NavigationDestination(icon: Icon(Icons.verified_user_rounded), label: 'Approvals'),
          NavigationDestination(icon: Icon(Icons.people_rounded), label: 'Users'),
        ],
      ),
    );
  }
}
