import 'package:flutter/material.dart';
import '../../screens/patient/patient_base_scaffold.dart';
import '../../screens/doctor/doctor_base_scaffold.dart';
import '../../screens/admin/admin_base_scaffold.dart';

class AppRouter {
  static const String initialRoute = '/';
  static const String patientHome = '/patient/home';
  static const String doctorHome = '/doctor/home';
  static const String adminHome = '/admin/home';

  static Route<dynamic> generateRoute(RouteSettings settings) {
    switch (settings.name) {
      case patientHome:
        return MaterialPageRoute(builder: (_) => const PatientBaseScaffold());
      case doctorHome:
        return MaterialPageRoute(builder: (_) => const DoctorBaseScaffold());
      case adminHome:
        return MaterialPageRoute(builder: (_) => const AdminBaseScaffold());
      default:
        return MaterialPageRoute(
          builder: (_) => Scaffold(
            body: Center(
              child: Text('No route defined for ${settings.name}'),
            ),
          ),
        );
    }
  }
}
