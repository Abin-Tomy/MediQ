import 'package:flutter/material.dart';

import '../../models/symptom_analysis.dart';
import 'severity_screen.dart';

class SymptomInputScreen extends StatefulWidget {
  final SymptomAnalysis analysis;

  const SymptomInputScreen({
    super.key,
    required this.analysis,
  });

  @override
  State<SymptomInputScreen> createState() => _SymptomInputScreenState();
}

class _SymptomInputScreenState extends State<SymptomInputScreen> {
  final TextEditingController _controller = TextEditingController();

  @override
  void initState() {
    super.initState();

    _controller.addListener(() {
      setState(() {});
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  bool get canContinue => _controller.text.trim().isNotEmpty;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),

      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        title: const Text("Describe Symptoms"),
      ),

      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),

          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,

            children: [

              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 12,
                ),
                decoration: BoxDecoration(
                  color: const Color(0xFFEAF4FF),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Row(
                  children: [

                    const Icon(
                      Icons.place_rounded,
                      color: Color(0xFF2F80ED),
                    ),

                    const SizedBox(width: 12),

                    Expanded(
                      child: Text(
                        "Affected Area : ${widget.analysis.bodyArea}",
                        style: const TextStyle(
                          color: Color(0xFF2F80ED),
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                        ),
                      ),
                    ),

                  ],
                ),
              ),

              const SizedBox(height: 28),

              const Text(
                "Describe your symptoms",
                style: TextStyle(
                  fontSize: 30,
                  fontWeight: FontWeight.bold,
                ),
              ),

              const SizedBox(height: 8),

              const Text(
                "Tell the AI exactly what you're experiencing.\nThe more details you provide, the better the prediction.",
                style: TextStyle(
                  color: Colors.grey,
                  height: 1.5,
                ),
              ),

              const SizedBox(height: 24),

              Expanded(
                child: Container(
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(22),
                    border: Border.all(
                      color: const Color(0xFF2F80ED),
                    ),
                  ),

                  child: TextField(
                    controller: _controller,
                    expands: true,
                    maxLines: null,
                    textAlignVertical: TextAlignVertical.top,

                    decoration: const InputDecoration(
                      border: InputBorder.none,
                      contentPadding: EdgeInsets.all(20),

                      hintText:
                          "Example:\n\n"
                          "• Sharp pain while walking\n"
                          "• Swelling since yesterday\n"
                          "• Burning sensation\n"
                          "• Fever with chills",
                    ),
                  ),
                ),
              ),

              const SizedBox(height: 12),

              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,

                children: [

                  Text(
                    canContinue
                        ? "✓ Looks good"
                        : "Please describe your symptoms",
                    style: TextStyle(
                      color: canContinue
                          ? Colors.green
                          : Colors.grey,
                      fontWeight: FontWeight.w600,
                    ),
                  ),

                  Text(
                    "${_controller.text.length}/500",
                    style: const TextStyle(
                      color: Colors.grey,
                    ),
                  ),

                ],
              ),

              const SizedBox(height: 20),

              SizedBox(
                width: double.infinity,
                height: 58,

                child: FilledButton.icon(

                  icon: const Icon(Icons.arrow_forward_rounded),

                  label: const Text(
                    "Continue to Severity",
                    style: TextStyle(
                      fontSize: 17,
                      fontWeight: FontWeight.w600,
                    ),
                  ),

                  onPressed: canContinue
                      ? () {

                          widget.analysis.symptoms =
                              _controller.text.trim();

                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => SeverityScreen(
                                analysis: widget.analysis,
                              ),
                            ),
                          );

                        }
                      : null,
                ),
              ),

            ],
          ),
        ),
      ),
    );
  }
}