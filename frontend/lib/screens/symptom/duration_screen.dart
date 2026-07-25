import 'package:flutter/material.dart';

import '../../models/symptom_analysis.dart';
import 'ai_processing_screen.dart';

class DurationScreen extends StatefulWidget {
  final SymptomAnalysis analysis;

  const DurationScreen({
    super.key,
    required this.analysis,
  });

  @override
  State<DurationScreen> createState() => _DurationScreenState();
}

class _DurationScreenState extends State<DurationScreen> {
  String? selectedDuration;

  final List<Map<String, dynamic>> durations = [
    {
      "icon": Icons.today_rounded,
      "title": "Today",
      "subtitle": "Symptoms started today",
    },
    {
      "icon": Icons.nightlight_round,
      "title": "Yesterday",
      "subtitle": "Started yesterday",
    },
    {
      "icon": Icons.calendar_today_rounded,
      "title": "2–3 Days",
      "subtitle": "Present for a few days",
    },
    {
      "icon": Icons.date_range_rounded,
      "title": "1 Week",
      "subtitle": "Around one week",
    },
    {
      "icon": Icons.event_note_rounded,
      "title": "2 Weeks",
      "subtitle": "Persistent for two weeks",
    },
    {
      "icon": Icons.schedule_rounded,
      "title": "More than 1 Month",
      "subtitle": "Long-term symptoms",
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),

      appBar: AppBar(
        elevation: 0,
        centerTitle: true,
        backgroundColor: Colors.transparent,
        title: const Text("Duration"),
      ),

      body: Padding(
        padding: const EdgeInsets.all(24),

        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,

          children: [

            ClipRRect(
              borderRadius: BorderRadius.circular(20),
              child: const LinearProgressIndicator(
                value: .80,
                minHeight: 7,
              ),
            ),

            const SizedBox(height: 28),

            const Text(
              "How long have you had these symptoms?",
              style: TextStyle(
                fontSize: 30,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 8),

            const Text(
              "Choose the option that best matches your condition.",
              style: TextStyle(
                color: Colors.grey,
                height: 1.5,
              ),
            ),

            const SizedBox(height: 28),

            Expanded(
              child: ListView.builder(
                itemCount: durations.length,

                itemBuilder: (context, index) {

                  final item = durations[index];

                  final selected =
                      selectedDuration == item["title"];

                  return Padding(
                    padding: const EdgeInsets.only(bottom: 18),

                    child: InkWell(
                      borderRadius:
                          BorderRadius.circular(24),

                      onTap: () {

                        setState(() {

                          selectedDuration =
                              item["title"];

                        });

                      },

                      child: AnimatedContainer(
                        duration:
                            const Duration(milliseconds: 220),

                        padding:
                            const EdgeInsets.all(20),

                        decoration: BoxDecoration(

                          color: selected
                              ? const Color(0xFFEAF4FF)
                              : Colors.white,

                          borderRadius:
                              BorderRadius.circular(24),

                          border: Border.all(
                            color: selected
                                ? const Color(0xFF2F80ED)
                                : Colors.grey.shade300,
                            width: selected ? 2 : 1,
                          ),

                          boxShadow: [

                            BoxShadow(
                              color: Colors.black.withValues(
                                  alpha: .05),
                              blurRadius: 18,
                              offset: const Offset(0, 8),
                            ),

                          ],
                        ),

                        child: Row(

                          children: [

                            Icon(
                              item["icon"],
                              size: 32,
                              color: selected
                                  ? const Color(0xFF2F80ED)
                                  : Colors.black87,
                            ),

                            const SizedBox(width: 18),

                            Expanded(
                              child: Column(
                                crossAxisAlignment:
                                    CrossAxisAlignment.start,

                                children: [

                                  Text(
                                    item["title"],
                                    style: TextStyle(
                                      fontSize: 20,
                                      fontWeight:
                                          FontWeight.bold,
                                      color: selected
                                          ? const Color(
                                              0xFF2F80ED)
                                          : Colors.black87,
                                    ),
                                  ),

                                  const SizedBox(height: 5),

                                  Text(
                                    item["subtitle"],
                                    style: const TextStyle(
                                      color: Colors.grey,
                                    ),
                                  ),

                                ],
                              ),
                            ),

                            if (selected)
                              const Icon(
                                Icons.check_circle,
                                color: Color(0xFF27AE60),
                                size: 30,
                              ),

                          ],
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),

            SizedBox(
              width: double.infinity,
              height: 58,

              child: FilledButton.icon(

                icon: const Icon(
                  Icons.auto_awesome_rounded,
                ),

                label: const Text(
                  "Analyze Symptoms",
                  style: TextStyle(
                    fontSize: 17,
                  ),
                ),

                onPressed: selectedDuration == null
                    ? null
                    : () {

                        widget.analysis.duration =
                            selectedDuration!;

                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) =>
                                AIProcessingScreen(
                              analysis: widget.analysis,
                            ),
                          ),
                        );

                    },
              ),
            ),

          ],
        ),
      ),
    );
  }
}