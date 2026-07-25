class Appointment {
  final String id;
  final String doctorName;
  final String specialty;
  final String hospital;
  final String slot;
  final String status;
  final int fee;

  const Appointment({
    required this.id,
    required this.doctorName,
    required this.specialty,
    required this.hospital,
    required this.slot,
    this.status = "Confirmed",
    required this.fee,
  });

  static final List<Appointment> userAppointments = [
    const Appointment(
      id: 'app_prev_1',
      doctorName: 'Dr. Rajesh Kumar',
      specialty: 'General Physician',
      hospital: 'Baby Memorial Hospital, Kozhikode',
      slot: 'Yesterday, 11:30 AM',
      status: 'Completed',
      fee: 500,
    ),
    const Appointment(
      id: 'app_prev_2',
      doctorName: 'Dr. Suresh Menon',
      specialty: 'Dermatologist',
      hospital: 'Malabar Institute of Medical Sciences',
      slot: '12 Jul 2026, 4:00 PM',
      status: 'Completed',
      fee: 600,
    ),
  ];

  static void addAppointment(Appointment app) {
    userAppointments.insert(0, app);
  }
}
