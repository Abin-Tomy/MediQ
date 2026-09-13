import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/theme/app_theme_provider.dart';
import '../../models/doctor.dart';
import '../appointment/booking_screen.dart';
import 'widgets/doctor_profile_modal.dart';

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

  String _translateSpecialty(String spec, AppThemeProvider theme) {
    switch (spec) {
      case "All":
        return theme.tr("All", "എല്ലാം");
      case "General Physician":
        return theme.tr("General Physician", "ജനറൽ ഫിസിഷ്യൻ");
      case "Infectious Disease Specialist":
        return theme.tr("Infectious Disease Specialist", "രോഗസംക്രമണ വിദഗ്ധൻ");
      case "Dermatologist":
        return theme.tr("Dermatologist", "ത്വക്ക് രോഗ വിദഗ്ധൻ");
      case "ENT Specialist":
        return theme.tr("ENT Specialist", "ENT വിദഗ്ധൻ");
      case "Ophthalmologist":
        return theme.tr("Ophthalmologist", "നേത്രരോഗ വിദഗ്ധൻ");
      default:
        return spec;
    }
  }

  void _openDoctorProfile(BuildContext context, Doctor doctor) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => DoctorProfileModal(doctor: doctor),
    );
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: AppThemeProvider(),
      builder: (context, _) {
        final theme = AppThemeProvider();
        final doctors = _filteredDoctors;

        final appBarTitle = theme.tr("Available Specialists", "ലഭ്യമായ ഡോക്ടർമാർ");
        final locationBannerText = theme.tr(
          "Showing verified doctors near Kozhikode (within 5 km)",
          "കോഴിക്കോടിനടുത്തുള്ള ഡോക്ടർമാർ (5 കി.മീ ഉള്ളിൽ)",
        );
        final searchHint = theme.tr(
          "Search by doctor name, hospital, or symptom...",
          "പേര്, ആശുപത്രി അല്ലെങ്കിൽ രോഗലക്ഷണം തിരയുക...",
        );
        final emptyText = theme.tr(
          "No doctors found matching your criteria.",
          "നിങ്ങൾ തിരഞ്ഞ വിവരങ്ങൾക്ക് അനുയോജ്യമായ ഡോക്ടർമാരില്ല.",
        );

        return Scaffold(
          resizeToAvoidBottomInset: false,
          backgroundColor: theme.background,
          appBar: AppBar(
            backgroundColor: Colors.transparent,
            elevation: 0,
            centerTitle: true,
            iconTheme: IconThemeData(color: theme.textPrimary),
            title: Text(
              appBarTitle,
              style: GoogleFonts.poppins(
                color: theme.textPrimary,
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
                    color: theme.isDark || theme.isMonsoon
                        ? theme.primaryAccent.withValues(alpha: .15)
                        : const Color(0xFFEAF4FF),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: theme.primaryAccent.withValues(alpha: .3)),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.location_on_rounded,
                          color: theme.primaryAccent, size: 20),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          locationBannerText,
                          style: GoogleFonts.poppins(
                            fontSize: 12.5,
                            fontWeight: FontWeight.w600,
                            color: theme.primaryAccent,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 8),

                // SEARCH BAR
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 24),
                  child: Container(
                    decoration: BoxDecoration(
                      color: theme.cardColor,
                      borderRadius: BorderRadius.circular(18),
                      border: Border.all(color: theme.borderColor),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: .04),
                          blurRadius: 10,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    ),
                    child: TextField(
                      controller: _searchController,
                      style: GoogleFonts.poppins(
                        fontSize: 14,
                        color: theme.textPrimary,
                      ),
                      onChanged: (val) {
                        setState(() {
                          _searchQuery = val;
                        });
                      },
                      decoration: InputDecoration(
                        hintText: searchHint,
                        hintStyle: GoogleFonts.poppins(
                          fontSize: 13,
                          color: theme.textHint,
                        ),
                        prefixIcon: Icon(
                          Icons.search_rounded,
                          color: theme.primaryAccent,
                          size: 22,
                        ),
                        suffixIcon: _searchQuery.isNotEmpty
                            ? IconButton(
                                icon: Icon(Icons.clear_rounded, color: theme.textHint, size: 18),
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

                // SPECIALTY PILLS
                SizedBox(
                  height: 40,
                  child: ListView.separated(
                    padding: const EdgeInsets.symmetric(horizontal: 24),
                    scrollDirection: Axis.horizontal,
                    physics: const BouncingScrollPhysics(),
                    itemCount: _specialties.length,
                    separatorBuilder: (context, index) => const SizedBox(width: 10),
                    itemBuilder: (context, index) {
                      final spec = _specialties[index];
                      final isSelected = spec == _selectedSpecialty;
                      final specLabel = _translateSpecialty(spec, theme);

                      return GestureDetector(
                        onTap: () {
                          setState(() {
                            _selectedSpecialty = spec;
                          });
                        },
                        child: AnimatedContainer(
                          duration: const Duration(milliseconds: 200),
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                          decoration: BoxDecoration(
                            color: isSelected ? theme.primaryAccent : theme.cardColor,
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(
                              color: isSelected ? theme.primaryAccent : theme.borderColor,
                            ),
                            boxShadow: isSelected
                                ? [
                                    BoxShadow(
                                      color: theme.primaryAccent.withValues(alpha: .3),
                                      blurRadius: 8,
                                      offset: const Offset(0, 4),
                                    )
                                  ]
                                : null,
                          ),
                          child: Center(
                            child: Text(
                              specLabel,
                              style: GoogleFonts.poppins(
                                fontSize: 13,
                                fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500,
                                color: isSelected ? Colors.white : theme.textSecondary,
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
                                  size: 64, color: theme.textHint.withValues(alpha: .5)),
                              const SizedBox(height: 12),
                              Text(
                                emptyText,
                                style: GoogleFonts.poppins(
                                  fontSize: 15,
                                  color: theme.textSecondary,
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
                          itemBuilder: (context, index) {
                            final doctor = doctors[index];
                            return _buildDoctorCard(context, doctor, theme);
                          },
                        ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildDoctorCard(BuildContext context, Doctor doctor, AppThemeProvider theme) {
    final viewProfileLbl = theme.tr("View Profile & Radar Route", "പ്രൊഫൈലും റഡാർ വഴിയും കാണുക");
    final bookLbl = theme.tr("Book Now", "ബുക്ക് ചെയ്യുക");
    final nextLbl = theme.tr("Next:", "അടുത്ത സമയം:");

    return InkWell(
      onTap: () => _openDoctorProfile(context, doctor),
      borderRadius: BorderRadius.circular(22),
      child: Container(
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          color: theme.cardColor,
          borderRadius: BorderRadius.circular(22),
          border: Border.all(color: theme.borderColor),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: .04),
              blurRadius: 12,
              offset: const Offset(0, 5),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // HERO AVATAR
                Hero(
                  tag: 'doctor_avatar_${doctor.id}',
                  child: Container(
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
                          decoration: TextDecoration.none,
                        ),
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
                          color: theme.textPrimary,
                        ),
                      ),
                      Text(
                        doctor.specialty,
                        style: GoogleFonts.poppins(
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                          color: theme.primaryAccent,
                        ),
                      ),
                      Text(
                        doctor.qualification,
                        style: GoogleFonts.poppins(
                          fontSize: 11.5,
                          color: theme.textHint,
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
                        Icon(Icons.directions_walk_rounded,
                            color: theme.textSecondary, size: 14),
                        Text(
                          "${doctor.distanceKm} km",
                          style: GoogleFonts.poppins(
                            fontSize: 11.5,
                            fontWeight: FontWeight.w600,
                            color: theme.textSecondary,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ],
            ),

            Divider(color: theme.borderColor, height: 24),

            // HOSPITAL & NEXT SLOT
            Row(
              children: [
                Icon(Icons.local_hospital_rounded,
                    color: theme.textHint, size: 16),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    doctor.hospital,
                    style: GoogleFonts.poppins(
                      fontSize: 12.5,
                      color: theme.textSecondary,
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
                      color: theme.isDark || theme.isMonsoon
                          ? const Color(0xFF10B981).withValues(alpha: .15)
                          : const Color(0xFFE8F5E9),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.access_time_rounded,
                            color: Color(0xFF10B981), size: 14),
                        const SizedBox(width: 6),
                        Flexible(
                          child: Text(
                            "$nextLbl ${doctor.availableSlots.first}",
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: GoogleFonts.poppins(
                              fontSize: 11.5,
                              fontWeight: FontWeight.w600,
                              color: const Color(0xFF10B981),
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
                    backgroundColor: theme.primaryAccent,
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
                    bookLbl,
                    style: GoogleFonts.poppins(
                      fontSize: 13.5,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 12),

            // VIEW PROFILE LINK
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  viewProfileLbl,
                  style: GoogleFonts.poppins(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: theme.primaryAccent,
                  ),
                ),
                const SizedBox(width: 4),
                Icon(Icons.arrow_forward_rounded, color: theme.primaryAccent, size: 14),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
