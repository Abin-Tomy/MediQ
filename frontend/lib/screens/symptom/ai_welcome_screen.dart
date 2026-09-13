import 'package:flutter/material.dart';
import 'body_area_screen.dart';
import 'visual_scan_screen.dart';
import '../report/report_upload_screen.dart';

class AIWelcomeScreen extends StatelessWidget {
  const AIWelcomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            physics: const BouncingScrollPhysics(),
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const SizedBox(height: 10),
                Container(
                  width: 140,
                  height: 140,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    image: const DecorationImage(
                      image: AssetImage('assets/images/ai_avatar.jpg'),
                      fit: BoxFit.cover,
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFF2F80ED).withOpacity(0.3),
                        blurRadius: 24,
                        offset: const Offset(0, 8),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 28),
                const Text('AI Health Assistant',
                    style: TextStyle(fontSize: 30,fontWeight: FontWeight.bold)),
                const SizedBox(height: 20),
                const Text(
                  "Hello Vishnu 👋\n\nI'm here to understand how you're feeling today.\n\nI'll ask a few simple questions before analyzing your symptoms.\n\nThis usually takes less than 30 seconds.",
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 17,height: 1.6),
                ),
                const SizedBox(height: 28),
                _feature(Icons.psychology_alt_rounded,'AI Symptom Analysis'),
                const SizedBox(height: 12),
                _feature(Icons.medical_information_outlined,'Medical Knowledge'),
                const SizedBox(height: 12),
                _feature(Icons.local_hospital_outlined,'Doctor Recommendation'),
                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  height: 56,
                  child: FilledButton.icon(
                    onPressed: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => const BodyAreaScreen(),
                        ),
                      );
                    },
                    icon: const Icon(Icons.psychology_alt_rounded),
                    label: const Text(
                      'Start Text Symptom Check (Model 1)',
                      style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                SizedBox(
                  width: double.infinity,
                  height: 56,
                  child: OutlinedButton.icon(
                    style: OutlinedButton.styleFrom(
                      foregroundColor: const Color(0xFF2F80ED),
                      side: const BorderSide(color: Color(0xFF2F80ED), width: 1.5),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(30),
                      ),
                    ),
                    onPressed: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => const VisualScanScreen(),
                        ),
                      );
                    },
                    icon: const Icon(Icons.camera_alt_rounded),
                    label: const Text(
                      'Scan Rash / Lesion (Model 2 YOLO)',
                      style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                SizedBox(
                  width: double.infinity,
                  height: 56,
                  child: OutlinedButton.icon(
                    style: OutlinedButton.styleFrom(
                      foregroundColor: const Color(0xFF27AE60),
                      side: const BorderSide(color: Color(0xFF27AE60), width: 1.5),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(30),
                      ),
                    ),
                    onPressed: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => const ReportUploadScreen(),
                        ),
                      );
                    },
                    icon: const Icon(Icons.description_rounded),
                    label: const Text(
                      'Upload Lab Report (Model 3 T5)',
                      style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
                    ),
                  ),
                ),
                const SizedBox(height: 14),
                const Text('Select AI Model Mode', style: TextStyle(color: Colors.grey, fontSize: 13)),
                const SizedBox(height: 10),
              ],
            ),
          ),
        ),
      ),
    );
  }

  static Widget _feature(IconData icon,String title){
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: const [BoxShadow(color: Color(0x14000000),blurRadius:18,offset: Offset(0,8))]
      ),
      child: Row(
        children:[
          Icon(icon,color: Color(0xFF2F80ED)),
          const SizedBox(width:12),
          Expanded(child: Text(title,style: const TextStyle(fontWeight: FontWeight.w600))),
          const Icon(Icons.check_circle,color: Color(0xFF27AE60))
        ],
      ),
    );
  }
}
