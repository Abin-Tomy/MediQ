import 'package:flutter/material.dart';

class AIWelcomeScreen extends StatelessWidget {
  const AIWelcomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            children: [
              const Spacer(),
              Container(
                width: 120,
                height: 120,
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF2F80ED), Color(0xFF56CCF2)],
                  ),
                  borderRadius: BorderRadius.circular(32),
                ),
                child: const Icon(Icons.smart_toy_rounded,
                    color: Colors.white, size: 64),
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
              const Spacer(),
              SizedBox(
                width: double.infinity,
                height: 58,
                child: FilledButton.icon(
                  onPressed: () {},
                  icon: const Icon(Icons.arrow_forward_rounded),
                  label: const Text('Continue'),
                ),
              ),
              const SizedBox(height: 16),
              const Text('Step 1 of 6',style: TextStyle(color: Colors.grey)),
            ],
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
