import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../core/theme/app_colors.dart';
import 'admin_doctor_creation_screen.dart';

class AdminUserManagementScreen extends StatelessWidget {
  const AdminUserManagementScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: Text("User Management", style: GoogleFonts.inter(fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: false,
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () {
          Navigator.push(context, MaterialPageRoute(builder: (_) => const AdminDoctorCreationScreen()));
        },
        backgroundColor: AppColors.primary,
        icon: const Icon(Icons.add, color: Colors.white),
        label: Text("Add Doctor", style: GoogleFonts.inter(color: Colors.white, fontWeight: FontWeight.w600)),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(24),
          children: [
            _buildUserItem("Sarah Jenkins", "Patient", "Active"),
            _buildUserItem("Dr. John Doe", "Doctor", "Active"),
            _buildUserItem("Mike Ross", "Patient", "Suspended", isSuspended: true),
          ],
        ),
      ),
    );
  }

  Widget _buildUserItem(String name, String role, String status, {bool isSuspended = false}) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.divider),
      ),
      child: Row(
        children: [
          CircleAvatar(
            backgroundColor: isSuspended ? AppColors.error.withOpacity(0.1) : AppColors.primaryLight,
            child: Icon(Icons.person, color: isSuspended ? AppColors.error : AppColors.primary),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(name, style: GoogleFonts.inter(fontWeight: FontWeight.w600, fontSize: 16)),
                Text(role, style: GoogleFonts.inter(color: AppColors.textSecondary, fontSize: 13)),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: (isSuspended ? AppColors.error : AppColors.success).withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Text(status, style: GoogleFonts.inter(fontSize: 12, fontWeight: FontWeight.w600, color: isSuspended ? AppColors.error : AppColors.success)),
          ),
          const SizedBox(width: 8),
          Icon(Icons.more_vert, color: AppColors.textSecondary),
        ],
      ),
    );
  }
}
