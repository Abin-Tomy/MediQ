class Doctor {
  final String id;
  final String name;
  final String specialty;
  final String qualification;
  final String hospital;
  final double distanceKm;
  final double rating;
  final int reviewsCount;
  final List<String> availableSlots;
  final String bio;
  final int fee;

  const Doctor({
    required this.id,
    required this.name,
    required this.specialty,
    required this.qualification,
    required this.hospital,
    required this.distanceKm,
    required this.rating,
    required this.reviewsCount,
    required this.availableSlots,
    required this.bio,
    required this.fee,
  });

  static const List<Doctor> seededDoctors = [
    Doctor(
      id: 'doc_1',
      name: 'Dr. Rajesh Kumar',
      specialty: 'General Physician',
      qualification: 'MBBS, MD (General Medicine)',
      hospital: 'Baby Memorial Hospital, Kozhikode',
      distanceKm: 1.2,
      rating: 4.9,
      reviewsCount: 142,
      availableSlots: [
        'Today, 4:30 PM',
        'Today, 6:00 PM',
        'Tomorrow, 10:00 AM',
        'Tomorrow, 11:30 AM',
      ],
      bio:
          'Senior General Physician with 15+ years of experience specializing in tropical fevers, viral infections, and metabolic disorders in Kerala.',
      fee: 500,
    ),
    Doctor(
      id: 'doc_2',
      name: 'Dr. Ananya Nair',
      specialty: 'Infectious Disease Specialist',
      qualification: 'MBBS, MD, DM (Infectious Diseases)',
      hospital: 'Aster MIMS, Kozhikode',
      distanceKm: 2.4,
      rating: 4.8,
      reviewsCount: 98,
      availableSlots: [
        'Today, 5:00 PM',
        'Tomorrow, 9:30 AM',
        'Tomorrow, 2:00 PM',
      ],
      bio:
          'Expert in vector-borne diseases (Dengue, Chikungunya, Leptospirosis, Nipah virus protocols) and acute epidemiology.',
      fee: 750,
    ),
    Doctor(
      id: 'doc_3',
      name: 'Dr. Suresh Menon',
      specialty: 'Dermatologist',
      qualification: 'MBBS, MD (Dermatology & Venereology)',
      hospital: 'Malabar Institute of Medical Sciences',
      distanceKm: 3.1,
      rating: 4.7,
      reviewsCount: 210,
      availableSlots: [
        'Today, 3:30 PM',
        'Today, 7:00 PM',
        'Tomorrow, 10:30 AM',
      ],
      bio:
          'Specializes in cutaneous manifestations of infectious diseases, allergic rashes, eczema, and skin lesions.',
      fee: 600,
    ),
    Doctor(
      id: 'doc_4',
      name: 'Dr. Meera Nambiar',
      specialty: 'General Physician',
      qualification: 'MBBS, DNB (Family Medicine)',
      hospital: 'National Hospital, Kozhikode',
      distanceKm: 1.8,
      rating: 4.9,
      reviewsCount: 175,
      availableSlots: [
        'Today, 4:00 PM',
        'Today, 5:30 PM',
        'Tomorrow, 11:00 AM',
      ],
      bio:
          'Dedicated family physician focused on early symptom detection, preventive healthcare, and outpatient disease management.',
      fee: 450,
    ),
    Doctor(
      id: 'doc_5',
      name: 'Dr. Arjun Varma',
      specialty: 'ENT Specialist',
      qualification: 'MBBS, MS (Otorhinolaryngology)',
      hospital: 'Iqraa Hospital, Kozhikode',
      distanceKm: 4.2,
      rating: 4.6,
      reviewsCount: 88,
      availableSlots: [
        'Tomorrow, 9:00 AM',
        'Tomorrow, 11:30 AM',
        'Tomorrow, 4:30 PM',
      ],
      bio:
          'Specialist in ear, nose, throat infections, sinus inflammation, and upper respiratory complications.',
      fee: 550,
    ),
    Doctor(
      id: 'doc_6',
      name: 'Dr. Fatima Pillai',
      specialty: 'Ophthalmologist',
      qualification: 'MBBS, MS (Ophthalmology)',
      hospital: 'Comtrust Eye Hospital, Kozhikode',
      distanceKm: 3.8,
      rating: 4.9,
      reviewsCount: 310,
      availableSlots: [
        'Today, 5:00 PM',
        'Tomorrow, 10:00 AM',
        'Tomorrow, 3:00 PM',
      ],
      bio:
          'Senior consultant ophthalmologist treating conjunctivitis, ocular manifestations of viral fevers, and vision care.',
      fee: 500,
    ),
    Doctor(
      id: 'doc_7',
      name: 'Dr. Thomas Kurian',
      specialty: 'General Physician',
      qualification: 'MBBS, MD (Internal Medicine)',
      hospital: 'St. Joseph\'s Hospital, Kozhikode',
      distanceKm: 2.9,
      rating: 4.8,
      reviewsCount: 164,
      availableSlots: [
        'Today, 6:30 PM',
        'Tomorrow, 10:00 AM',
        'Tomorrow, 5:00 PM',
      ],
      bio:
          'Experienced internist managing acute fevers, hematological abnormalities (low platelets), and general clinical care.',
      fee: 500,
    ),
    Doctor(
      id: 'doc_8',
      name: 'Dr. Neha Shenoy',
      specialty: 'Pediatrician',
      qualification: 'MBBS, MD (Pediatrics), DCH',
      hospital: 'Aster MIMS Hospital, Kozhikode',
      distanceKm: 2.1,
      rating: 4.9,
      reviewsCount: 215,
      availableSlots: [
        'Today, 4:00 PM',
        'Tomorrow, 10:30 AM',
        'Tomorrow, 4:30 PM',
      ],
      bio:
          'Specialist pediatrician managing childhood fevers, viral respiratory infections, and pediatric dengue monitoring.',
      fee: 550,
    ),
    Doctor(
      id: 'doc_9',
      name: 'Dr. Vivek Menon',
      specialty: 'Pulmonologist',
      qualification: 'MBBS, MD (Pulmonary Medicine)',
      hospital: 'Baby Memorial Hospital, Kozhikode',
      distanceKm: 1.5,
      rating: 4.8,
      reviewsCount: 130,
      availableSlots: [
        'Today, 5:30 PM',
        'Tomorrow, 11:00 AM',
        'Tomorrow, 6:00 PM',
      ],
      bio:
          'Consultant pulmonologist specializing in upper and lower respiratory tract infections, wheezing, and post-monsoon lung care.',
      fee: 600,
    ),
  ];
}
