import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/theme/app_theme_provider.dart';
import '../../models/doctor.dart';
import '../../models/appointment.dart';
import 'appointment_success_screen.dart';

class BookingScreen extends StatefulWidget {
  final Doctor doctor;

  const BookingScreen({
    super.key,
    required this.doctor,
  });

  @override
  State<BookingScreen> createState() => _BookingScreenState();
}

class _BookingScreenState extends State<BookingScreen> {
  late String _selectedSlot;

  @override
  void initState() {
    super.initState();
    _selectedSlot = widget.doctor.availableSlots.first;
  }

  void _confirmBooking() {
    final newApp = Appointment(
      id: 'app_${DateTime.now().millisecondsSinceEpoch}',
      doctorName: widget.doctor.name,
      specialty: widget.doctor.specialty,
      hospital: widget.doctor.hospital,
      slot: _selectedSlot,
      fee: widget.doctor.fee,
      status: "Confirmed",
    );

    Appointment.addAppointment(newApp);

    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (_) => AppointmentSuccessScreen(
          doctor: widget.doctor,
          slot: _selectedSlot,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: AppThemeProvider(),
      builder: (context, _) {
        final theme = AppThemeProvider();

        final title = theme.tr("Two-Tap Appointment Booking", "ഒറ്റ ക്ലിക്കിൽ സമയം ബുക്ക് ചെയ്യുക");
        final tap1Lbl = theme.tr("Tap 1: Select Time Slot", "സ്റ്റെപ്പ് 1: സമയം തിരഞ്ഞെടുക്കുക");
        final locLbl = theme.tr("Consultation Location", "പരിശോധനാ കേന്ദ്രം");
        final feeLbl = theme.tr("Consultation Fee", "പരിശോധനാ ഫീസ്");
        final payLbl = theme.tr("(Pay at Clinic)", "(ക്ലിനിക്കിൽ നൽകാം)");
        final selSlotLbl = theme.tr("Selected Slot:", "തിരഞ്ഞെടുത്ത സമയം:");
        final bookBtnLbl = theme.tr("Tap 2: Book Now", "സ്റ്റെപ്പ് 2: ബുക്ക് ചെയ്യുക");

        return Scaffold(
          backgroundColor: theme.background,
          appBar: AppBar(
            backgroundColor: Colors.transparent,
            elevation: 0,
            centerTitle: true,
            iconTheme: IconThemeData(color: theme.textPrimary),
            title: Text(
              title,
              style: GoogleFonts.poppins(
                color: theme.textPrimary,
                fontWeight: FontWeight.w600,
                fontSize: 18,
              ),
            ),
          ),
          body: SafeArea(
            child: Column(
              children: [
                Expanded(
                  child: SingleChildScrollView(
                    physics: const BouncingScrollPhysics(),
                    padding: const EdgeInsets.fromLTRB(24, 10, 24, 20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // DOCTOR HEADER CARD
                        Container(
                          padding: const EdgeInsets.all(20),
                          decoration: BoxDecoration(
                            color: theme.cardColor,
                            borderRadius: BorderRadius.circular(24),
                            border: Border.all(color: theme.borderColor),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withValues(alpha: .04),
                                blurRadius: 15,
                                offset: const Offset(0, 5),
                              ),
                            ],
                          ),
                          child: Row(
                            children: [
                              Hero(
                                tag: 'doctor_avatar_${widget.doctor.id}',
                                child: Container(
                                  width: 64,
                                  height: 64,
                                  decoration: BoxDecoration(
                                    gradient: const LinearGradient(
                                      colors: [Color(0xFF2F80ED), Color(0xFF56CCF2)],
                                    ),
                                    borderRadius: BorderRadius.circular(20),
                                  ),
                                  child: Center(
                                    child: Text(
                                      widget.doctor.name
                                          .replaceFirst("Dr. ", "")
                                          .substring(0, 2)
                                          .toUpperCase(),
                                      style: GoogleFonts.poppins(
                                        color: Colors.white,
                                        fontSize: 22,
                                        fontWeight: FontWeight.w700,
                                        decoration: TextDecoration.none,
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                              const SizedBox(width: 16),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      widget.doctor.name,
                                      style: GoogleFonts.poppins(
                                        fontSize: 18,
                                        fontWeight: FontWeight.w700,
                                        color: theme.textPrimary,
                                      ),
                                    ),
                                    Text(
                                      widget.doctor.specialty,
                                      style: GoogleFonts.poppins(
                                        fontSize: 14,
                                        fontWeight: FontWeight.w600,
                                        color: theme.primaryAccent,
                                      ),
                                    ),
                                    const SizedBox(height: 4),
                                    Row(
                                      children: [
                                        const Icon(Icons.star_rounded,
                                            color: Color(0xFFD97706), size: 16),
                                        const SizedBox(width: 4),
                                        Text(
                                          "${widget.doctor.rating} (${widget.doctor.reviewsCount} reviews)",
                                          style: GoogleFonts.poppins(
                                            fontSize: 12,
                                            color: theme.textSecondary,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ),

                        const SizedBox(height: 24),

                        // TAP 1: SLOT SELECTION
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.all(8),
                              decoration: BoxDecoration(
                                color: theme.primaryAccent.withValues(alpha: .15),
                                shape: BoxShape.circle,
                              ),
                              child: Text(
                                "1",
                                style: GoogleFonts.poppins(
                                  color: theme.primaryAccent,
                                  fontWeight: FontWeight.w700,
                                  fontSize: 14,
                                ),
                              ),
                            ),
                            const SizedBox(width: 10),
                            Text(
                              tap1Lbl,
                              style: GoogleFonts.poppins(
                                fontSize: 17,
                                fontWeight: FontWeight.w700,
                                color: theme.textPrimary,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 14),

                        GridView.builder(
                          shrinkWrap: true,
                          physics: const NeverScrollableScrollPhysics(),
                          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                            crossAxisCount: 2,
                            childAspectRatio: 2.5,
                            crossAxisSpacing: 12,
                            mainAxisSpacing: 12,
                          ),
                          itemCount: widget.doctor.availableSlots.length,
                          itemBuilder: (_, idx) {
                            final slot = widget.doctor.availableSlots[idx];
                            final isSelected = slot == _selectedSlot;

                            return GestureDetector(
                              onTap: () {
                                setState(() {
                                  _selectedSlot = slot;
                                });
                              },
                              child: AnimatedContainer(
                                duration: const Duration(milliseconds: 200),
                                decoration: BoxDecoration(
                                  color: isSelected ? theme.primaryAccent : theme.cardColor,
                                  borderRadius: BorderRadius.circular(16),
                                  border: Border.all(
                                    color: isSelected ? theme.primaryAccent : theme.borderColor,
                                    width: 1.5,
                                  ),
                                  boxShadow: isSelected
                                      ? [
                                          BoxShadow(
                                            color: theme.primaryAccent.withValues(alpha: .3),
                                            blurRadius: 10,
                                            offset: const Offset(0, 4),
                                          ),
                                        ]
                                      : null,
                                ),
                                child: Center(
                                  child: Text(
                                    slot,
                                    style: GoogleFonts.poppins(
                                      fontSize: 13,
                                      fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
                                      color: isSelected ? Colors.white : theme.textPrimary,
                                    ),
                                  ),
                                ),
                              ),
                            );
                          },
                        ),

                        const SizedBox(height: 28),

                        // LOCATION & FEE DETAILS
                        Container(
                          padding: const EdgeInsets.all(18),
                          decoration: BoxDecoration(
                            color: theme.cardColor,
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(color: theme.borderColor),
                          ),
                          child: Column(
                            children: [
                              Row(
                                children: [
                                  Icon(Icons.place_rounded,
                                      color: theme.primaryAccent, size: 20),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          locLbl,
                                          style: GoogleFonts.poppins(
                                            fontSize: 12,
                                            color: theme.textHint,
                                          ),
                                        ),
                                        Text(
                                          widget.doctor.hospital,
                                          style: GoogleFonts.poppins(
                                            fontSize: 14,
                                            fontWeight: FontWeight.w600,
                                            color: theme.textPrimary,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ],
                              ),
                              Divider(color: theme.borderColor, height: 24),
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Text(
                                    feeLbl,
                                    style: GoogleFonts.poppins(
                                      fontSize: 14,
                                      color: theme.textSecondary,
                                    ),
                                  ),
                                  Text(
                                    "₹${widget.doctor.fee} $payLbl",
                                    style: GoogleFonts.poppins(
                                      fontSize: 15,
                                      fontWeight: FontWeight.w700,
                                      color: const Color(0xFF10B981),
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

                // TAP 2: CONFIRM BAR
                Container(
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    color: theme.cardColor,
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withValues(alpha: .06),
                        blurRadius: 20,
                        offset: const Offset(0, -5),
                      ),
                    ],
                  ),
                  child: Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              selSlotLbl,
                              style: GoogleFonts.poppins(
                                fontSize: 12,
                                color: theme.textHint,
                              ),
                            ),
                            Text(
                              _selectedSlot,
                              style: GoogleFonts.poppins(
                                fontSize: 15,
                                fontWeight: FontWeight.w700,
                                color: theme.textPrimary,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 16),
                      ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF10B981),
                          foregroundColor: Colors.white,
                          elevation: 0,
                          padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 14),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(18),
                          ),
                        ),
                        onPressed: _confirmBooking,
                        icon: const Icon(Icons.check_circle_rounded, size: 20),
                        label: Text(
                          bookBtnLbl,
                          style: GoogleFonts.poppins(
                            fontSize: 15,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
