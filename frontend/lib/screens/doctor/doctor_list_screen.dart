import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/theme/app_colors.dart';
import '../../models/doctor.dart';
import '../appointment/booking_screen.dart';

class DoctorListScreen extends StatefulWidget {
  final String? initialSpecialty;

  const DoctorListScreen({
    super.key,
    this.initialSpecialty,
  });

  @override
  State<DoctorListScreen> createState() => _DoctorListScreenState();
}

class _DoctorListScreenState extends State<DoctorListScreen> {
  String _selectedSpecialty = "All";
  String _searchQuery = "";
  final TextEditingController _searchController = TextEditingController();

  final List<String> _specialties = [
    "All",
    "General Physician",
    "Infectious Disease Specialist",
    "Dermatologist",
    "ENT Specialist",
    "Ophthalmologist",
  ];

  @override
  void initState() {
    super.initState();
    if (widget.initialSpecialty != null) {
      final initial = widget.initialSpecialty!;
      if (_specialties.contains(initial)) {
        _selectedSpecialty = initial;
      } else {
        for (final spec in _specialties) {
          if (spec != "All" &&
              (initial.toLowerCase().contains(spec.toLowerCase()) ||
                  spec.toLowerCase().contains(initial.toLowerCase()) ||
                  (initial.toLowerCase().contains("infectious") &&
                      spec.toLowerCase().contains("infectious")) ||
                  (initial.toLowerCase().contains("general") &&
                      spec.toLowerCase().contains("general")))) {
            _selectedSpecialty = spec;
            break;
          }
        }
      }
    }
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  List<Doctor> get _filteredDoctors {
    return Doctor.seededDoctors.where((doc) {
      final matchesSpecialty = _selectedSpecialty == "All" ||
          doc.specialty.toLowerCase() == _selectedSpecialty.toLowerCase() ||
          doc.specialty.toLowerCase().contains(_selectedSpecialty.toLowerCase()) ||
          _selectedSpecialty.toLowerCase().contains(doc.specialty.toLowerCase()) ||
          (_selectedSpecialty.toLowerCase().contains("infectious") &&
              doc.specialty.toLowerCase().contains("infectious")) ||
          (_selectedSpecialty.toLowerCase().contains("general") &&
              doc.specialty.toLowerCase().contains("general")) ||
          (_selectedSpecialty.toLowerCase().contains("derm") &&
              doc.specialty.toLowerCase().contains("derm")) ||
          (_selectedSpecialty.toLowerCase().contains("ent") &&
              doc.specialty.toLowerCase().contains("ent")) ||
          (_selectedSpecialty.toLowerCase().contains("ophth") &&
              doc.specialty.toLowerCase().contains("ophth")) ||
          (_selectedSpecialty.toLowerCase().contains("pediatr") &&
              doc.specialty.toLowerCase().contains("pediatr")) ||
          (_selectedSpecialty.toLowerCase().contains("pulmon") &&
              doc.specialty.toLowerCase().contains("pulmon"));

      final query = _searchQuery.trim().toLowerCase();
      final matchesSearch = query.isEmpty ||
          doc.name.toLowerCase().contains(query) ||
          doc.specialty.toLowerCase().contains(query) ||
          doc.hospital.toLowerCase().contains(query) ||
          doc.qualification.toLowerCase().contains(query) ||
          doc.bio.toLowerCase().contains(query);

      return matchesSpecialty && matchesSearch;
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    final doctors = _filteredDoctors;

    return Scaffold(
      resizeToAvoidBottomInset: false,
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded, color: AppColors.textPrimary),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text(
          "Available Specialists",
          style: GoogleFonts.poppins(
            color: AppColors.textPrimary,
            fontWeight: FontWeight.w600,
            fontSize: 18,
          ),
        ),
      ),
      body: SafeArea(
        bottom: false,
        child: Column(
          children: [
            // LOCATION BANNER
            Container(
              margin: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              decoration: BoxDecoration(
                color: const Color(0xFFEAF4FF),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppColors.primary.withValues(alpha: .3)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.location_on_rounded,
                      color: AppColors.primary, size: 20),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      "Showing verified doctors near Kozhikode (within 5 km)",
                      style: GoogleFonts.poppins(
                        fontSize: 12.5,
                        fontWeight: FontWeight.w600,
                        color: AppColors.primary,
                      ),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 12),

            // SEARCH BAR
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(18),
                  border: Border.all(color: AppColors.border),
                ),
                child: TextField(
                  controller: _searchController,
                  onChanged: (val) {
                    setState(() {
                      _searchQuery = val;
                    });
                  },
                  decoration: InputDecoration(
                    hintText: "Search doctor, specialty, or hospital...",
                    hintStyle: GoogleFonts.poppins(color: AppColors.textHint, fontSize: 13.5),
                    prefixIcon: const Icon(Icons.search_rounded, color: AppColors.textHint),
                    suffixIcon: _searchQuery.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.clear_rounded, color: AppColors.textHint, size: 18),
                            onPressed: () {
                              _searchController.clear();
                              setState(() {
                                _searchQuery = "";
                              });
                            },
                          )
                        : null,
                    border: InputBorder.none,
                    contentPadding: const EdgeInsets.symmetric(vertical: 14),
                  ),
                ),
              ),
            ),

            const SizedBox(height: 16),

            // SPECIALTY CHIPS
            SizedBox(
              height: 42,
              child: ListView.separated(
                padding: const EdgeInsets.symmetric(horizontal: 24),
                scrollDirection: Axis.horizontal,
                physics: const BouncingScrollPhysics(),
                itemCount: _specialties.length,
                separatorBuilder: (context, index) => const SizedBox(width: 10),
                itemBuilder: (_, index) {
                  final spec = _specialties[index];
                  final isSelected = spec == _selectedSpecialty;

                  return GestureDetector(
                    onTap: () {
                      setState(() {
                        _selectedSpecialty = spec;
                      });
                    },
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      decoration: BoxDecoration(
                        color: isSelected ? AppColors.primary : Colors.white,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(
                          color: isSelected ? AppColors.primary : AppColors.border,
                        ),
                        boxShadow: isSelected
                            ? [
                                BoxShadow(
                                  color: AppColors.primary.withValues(alpha: .3),
                                  blurRadius: 8,
                                  offset: const Offset(0, 4),
                                )
                              ]
                            : null,
                      ),
                      child: Center(
                        child: Text(
                          spec,
                          style: GoogleFonts.poppins(
                            fontSize: 13,
                            fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500,
                            color: isSelected ? Colors.white : AppColors.textSecondary,
                          ),
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),

            const SizedBox(height: 16),

            // DOCTOR LIST
            Expanded(
              child: doctors.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.person_search_rounded,
                              size: 64, color: AppColors.textHint.withValues(alpha: .5)),
                          const SizedBox(height: 12),
                          Text(
                            "No doctors found matching your criteria.",
                            style: GoogleFonts.poppins(
                              fontSize: 15,
                              color: AppColors.textSecondary,
                            ),
                          ),
                        ],
                      ),
                    )
                  : ListView.separated(
                      padding: const EdgeInsets.fromLTRB(24, 4, 24, 30),
                      physics: const BouncingScrollPhysics(),
                      itemCount: doctors.length,
                      separatorBuilder: (context, index) => const SizedBox(height: 16),
                      itemBuilder: (_, index) {
                        final doctor = doctors[index];
                        return _buildDoctorCard(context, doctor);
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDoctorCard(BuildContext context, Doctor doctor) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: AppColors.border),
        boxShadow: const [
          BoxShadow(
            color: Color(0x0A000000),
            blurRadius: 12,
            offset: Offset(0, 5),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // AVATAR
              Container(
                width: 60,
                height: 60,
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF2F80ED), Color(0xFF56CCF2)],
                  ),
                  borderRadius: BorderRadius.circular(18),
                ),
                child: Center(
                  child: Text(
                    doctor.name.replaceFirst("Dr. ", "").substring(0, 2).toUpperCase(),
                    style: GoogleFonts.poppins(
                      color: Colors.white,
                      fontSize: 20,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 14),

              // DETAILS
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      doctor.name,
                      style: GoogleFonts.poppins(
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    Text(
                      doctor.specialty,
                      style: GoogleFonts.poppins(
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                        color: AppColors.primary,
                      ),
                    ),
                    Text(
                      doctor.qualification,
                      style: GoogleFonts.poppins(
                        fontSize: 11.5,
                        color: AppColors.textHint,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),

              // RATING & DISTANCE
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: const Color(0xFFFEF3C7),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.star_rounded, color: Color(0xFFD97706), size: 16),
                        const SizedBox(width: 4),
                        Text(
                          doctor.rating.toString(),
                          style: GoogleFonts.poppins(
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                            color: const Color(0xFF92400E),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 6),
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.directions_walk_rounded,
                          color: AppColors.textSecondary, size: 14),
                      Text(
                        "${doctor.distanceKm} km",
                        style: GoogleFonts.poppins(
                          fontSize: 11.5,
                          fontWeight: FontWeight.w600,
                          color: AppColors.textSecondary,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ],
          ),

          const Divider(height: 24),

          // HOSPITAL & NEXT SLOT
          Row(
            children: [
              const Icon(Icons.local_hospital_rounded,
                  color: AppColors.textHint, size: 16),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  doctor.hospital,
                  style: GoogleFonts.poppins(
                    fontSize: 12.5,
                    color: AppColors.textSecondary,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),

          const SizedBox(height: 14),

          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  decoration: BoxDecoration(
                    color: const Color(0xFFE8F5E9),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.access_time_rounded,
                          color: Color(0xFF27AE60), size: 14),
                      const SizedBox(width: 6),
                      Flexible(
                        child: Text(
                          "Next: ${doctor.availableSlots.first}",
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: GoogleFonts.poppins(
                            fontSize: 11.5,
                            fontWeight: FontWeight.w600,
                            color: const Color(0xFF1B5E20),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 12),

              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.white,
                  elevation: 0,
                  padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                ),
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => BookingScreen(doctor: doctor),
                    ),
                  );
                },
                child: Text(
                  "Book Now",
                  style: GoogleFonts.poppins(
                    fontSize: 13.5,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
