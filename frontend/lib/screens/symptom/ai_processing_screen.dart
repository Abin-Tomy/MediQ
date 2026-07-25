import 'dart:async';
import 'package:flutter/material.dart';

import '../../models/symptom_analysis.dart';
import 'diagnosis_screen.dart';

class AIProcessingScreen extends StatefulWidget {
  final SymptomAnalysis analysis;

  const AIProcessingScreen({
    super.key,
    required this.analysis,
  });

  @override
  State<AIProcessingScreen> createState() =>
      _AIProcessingScreenState();
}

class _AIProcessingScreenState
    extends State<AIProcessingScreen>
    with TickerProviderStateMixin {

  late AnimationController pulseController;

  int currentStep = 0;

  int confidence = 0;

  final steps = [

    "Understanding your symptoms",

    "Reviewing medical knowledge",

    "Comparing similar medical cases",

    "Finding possible conditions",

    "Selecting the right specialist",

    "Generating health report",

  ];

  @override
  void initState() {
    super.initState();

    pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1400),
    )..repeat(reverse: true);

    startAnalysis();
  }

  Future<void> startAnalysis() async {

    for (int i = 0; i < steps.length; i++) {

      await Future.delayed(
        const Duration(milliseconds: 900),
      );

      if (!mounted) return;

      setState(() {
        currentStep = i + 1;
        confidence =
            ((i + 1) / steps.length * 94).round();
      });

    }

    await Future.delayed(
      const Duration(milliseconds: 1200),
    );

    if (!mounted) return;

    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (_) => DiagnosisScreen(
          analysis: widget.analysis,
        ),
      ),
    );

  }

  @override
  void dispose() {

    pulseController.dispose();

    super.dispose();

  }

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

              AnimatedBuilder(

                animation: pulseController,

                builder: (_, child) {

                  final scale =
                      1 + pulseController.value * .08;

                  return Transform.scale(
                    scale: scale,
                    child: child,
                  );

                },

                child: Container(

                  width: 130,

                  height: 130,

                  decoration: BoxDecoration(

                    shape: BoxShape.circle,

                    gradient: const LinearGradient(

                      colors: [

                        Color(0xFF2F80ED),

                        Color(0xFF56CCF2),

                      ],

                    ),

                    boxShadow: [

                      BoxShadow(

                        color: Colors.blue.withValues(
                            alpha: .25),

                        blurRadius: 30,

                        spreadRadius: 10,

                      ),

                    ],

                  ),

                  child: const Icon(

                    Icons.psychology_alt_rounded,

                    color: Colors.white,

                    size: 70,

                  ),

                ),

              ),

              const SizedBox(height: 28),

              const Text(

                "MediQ AI",

                style: TextStyle(

                  fontSize: 34,

                  fontWeight: FontWeight.bold,

                ),

              ),

              const SizedBox(height: 10),

              const Text(

                "Analyzing your symptoms...",

                style: TextStyle(

                  color: Colors.grey,

                  fontSize: 16,

                ),

              ),

              const SizedBox(height: 35),

              TweenAnimationBuilder<double>(

                tween: Tween(

                  begin: 0,

                  end: currentStep / steps.length,

                ),

                duration:
                    const Duration(milliseconds: 700),

                builder: (_, value, __) {

                  return ClipRRect(

                    borderRadius:
                        BorderRadius.circular(20),

                    child: LinearProgressIndicator(

                      value: value,

                      minHeight: 8,

                    ),

                  );

                },

              ),

              const SizedBox(height: 15),

              Text(

                "AI Confidence  $confidence%",

                style: const TextStyle(

                  fontWeight: FontWeight.bold,

                  color: Color(0xFF2F80ED),

                ),

              ),

              const SizedBox(height: 35),

              Expanded(

                child: ListView.builder(

                  physics:
                      const NeverScrollableScrollPhysics(),

                  itemCount: steps.length,

                  itemBuilder: (_, index) {

                    final completed =
                        currentStep > index;

                    final active =
                        currentStep == index;

                    return AnimatedOpacity(

                      duration:
                          const Duration(milliseconds: 500),

                      opacity:
                          completed || active ? 1 : .35,

                      child: Container(

                        margin:
                            const EdgeInsets.only(bottom: 16),

                        padding:
                            const EdgeInsets.all(18),

                        decoration: BoxDecoration(

                          color: Colors.white,

                          borderRadius:
                              BorderRadius.circular(20),

                          boxShadow: [

                            BoxShadow(

                              color: Colors.black
                                  .withValues(alpha: .04),

                              blurRadius: 12,

                            ),

                          ],

                        ),

                        child: Row(

                          children: [

                            if (completed)

                              const Icon(

                                Icons.check_circle,

                                color:
                                    Color(0xFF27AE60),

                              )

                            else if (active)

                              const SizedBox(

                                width: 22,

                                height: 22,

                                child:
                                    CircularProgressIndicator(
                                  strokeWidth: 2.5,
                                ),

                              )

                            else

                              const Icon(

                                Icons.radio_button_unchecked,

                                color: Colors.grey,

                              ),

                            const SizedBox(width: 15),

                            Expanded(

                              child: Text(

                                steps[index],

                                style: TextStyle(

                                  fontSize: 16,

                                  fontWeight: completed
                                      ? FontWeight.bold
                                      : FontWeight.w500,

                                ),

                              ),

                            ),

                          ],

                        ),

                      ),

                    );

                  },

                ),

              ),

              const Text(

                "Please wait while MediQ prepares your report.",

                textAlign: TextAlign.center,

                style: TextStyle(

                  color: Colors.grey,

                ),

              ),

              const SizedBox(height: 15),

            ],

          ),

        ),

      ),

    );

  }

}