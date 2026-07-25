import 'package:flutter/material.dart';

import '../../models/symptom_analysis.dart';
import 'duration_screen.dart';

class SeverityScreen extends StatefulWidget {
  final SymptomAnalysis analysis;

  const SeverityScreen({
    super.key,
    required this.analysis,
  });

  @override
  State<SeverityScreen> createState() => _SeverityScreenState();
}

class _SeverityScreenState extends State<SeverityScreen> {
  String? selectedSeverity;

  final List<Map<String, String>> severityLevels = [
    {
      "emoji": "😊",
      "title": "Mild",
      "subtitle": "Slight discomfort",
    },
    {
      "emoji": "😐",
      "title": "Moderate",
      "subtitle": "Pain is noticeable",
    },
    {
      "emoji": "😖",
      "title": "Severe",
      "subtitle": "Difficult to perform daily activities",
    },
    {
      "emoji": "🚨",
      "title": "Emergency",
      "subtitle": "Needs immediate medical attention",
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),

      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        title: const Text("Severity"),
      ),

      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),

          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,

            children: [

              const LinearProgressIndicator(
                value: 0.66,
                borderRadius: BorderRadius.all(
                  Radius.circular(20),
                ),
              ),

              const SizedBox(height: 24),

              const Text(
                "How severe is it?",
                style: TextStyle(
                  fontSize: 30,
                  fontWeight: FontWeight.bold,
                ),
              ),

              const SizedBox(height: 10),

              const Text(
                "Choose the option that best describes your discomfort.",
                style: TextStyle(
                  color: Colors.grey,
                  height: 1.5,
                ),
              ),

              const SizedBox(height: 30),

              Expanded(
                child: ListView.builder(
                  itemCount: severityLevels.length,
                  itemBuilder: (context, index) {

                    final item = severityLevels[index];

                    final selected =
                        selectedSeverity == item["title"];

                    return Padding(
                      padding: const EdgeInsets.only(bottom: 18),

                      child: InkWell(
                        borderRadius: BorderRadius.circular(22),

                        onTap: () {
                          setState(() {
                            selectedSeverity = item["title"];
                          });
                        },

                        child: AnimatedContainer(
                          duration: const Duration(
                            milliseconds: 250,
                          ),

                          padding: const EdgeInsets.all(20),

                          decoration: BoxDecoration(
                            color: selected
                                ? const Color(0xFFEAF4FF)
                                : Colors.white,

                            borderRadius:
                                BorderRadius.circular(22),

                            border: Border.all(
                              color: selected
                                  ? const Color(0xFF2F80ED)
                                  : Colors.grey.shade300,
                              width: selected ? 2 : 1,
                            ),

                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withOpacity(.05),
                                blurRadius: 12,
                                offset: const Offset(0, 5),
                              ),
                            ],
                          ),

                          child: Row(
                            children: [

                              Text(
                                item["emoji"]!,
                                style: const TextStyle(
                                  fontSize: 34,
                                ),
                              ),

                              const SizedBox(width: 18),

                              Expanded(
                                child: Column(
                                  crossAxisAlignment:
                                      CrossAxisAlignment.start,

                                  children: [

                                    Text(
                                      item["title"]!,
                                      style: TextStyle(
                                        fontWeight:
                                            FontWeight.bold,
                                        fontSize: 19,
                                        color: selected
                                            ? const Color(
                                                0xFF2F80ED)
                                            : Colors.black87,
                                      ),
                                    ),

                                    const SizedBox(height: 6),

                                    Text(
                                      item["subtitle"]!,
                                      style:
                                          const TextStyle(
                                        color: Colors.grey,
                                      ),
                                    ),

                                  ],
                                ),
                              ),

                              if (selected)
                                const Icon(
                                  Icons.check_circle,
                                  color:
                                      Color(0xFF27AE60),
                                  size: 28,
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
                    Icons.arrow_forward_rounded,
                  ),

                  label: const Text(
                    "Continue",
                    style: TextStyle(
                      fontSize: 17,
                    ),
                  ),

                  onPressed: selectedSeverity == null
                      ? null
                      : () {

                          widget.analysis.severity =
                              selectedSeverity!;

                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => DurationScreen(
                                analysis: widget.analysis,
                              ),
                            ),
                          );

                          debugPrint(widget.analysis.toString());

                        },
                ),
              ),

            ],
          ),
        ),
      ),
    );
  }
}