import 'package:flutter/material.dart';

import '../../models/body_area.dart';
import '../../models/symptom_analysis.dart';
import 'symptom_input_screen.dart';

class BodyAreaScreen extends StatefulWidget {
  const BodyAreaScreen({super.key});

  @override
  State<BodyAreaScreen> createState() => _BodyAreaScreenState();
}

class _BodyAreaScreenState extends State<BodyAreaScreen> {
  BodyArea? selected;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),

      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: const Text("Where does it hurt?"),
      ),

      body: Padding(
        padding: const EdgeInsets.all(24),

        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,

          children: [

            const Text(
              "Select the area where you're experiencing discomfort.",
              style: TextStyle(
                color: Colors.grey,
                fontSize: 16,
              ),
            ),

            const SizedBox(height: 24),

            Expanded(
              child: GridView.builder(
                itemCount: BodyArea.items.length,

                gridDelegate:
                    const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  crossAxisSpacing: 16,
                  mainAxisSpacing: 16,
                  childAspectRatio: 1,
                ),

                itemBuilder: (context, index) {
                  final area = BodyArea.items[index];

                  final isSelected = selected == area;

                  return InkWell(
                    borderRadius: BorderRadius.circular(22),

                    onTap: () {
                      setState(() {
                        selected = area;
                      });
                    },

                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 250),

                      decoration: BoxDecoration(
                        color: isSelected
                            ? const Color(0xFFEAF4FF)
                            : Colors.white,

                        borderRadius: BorderRadius.circular(22),

                        border: Border.all(
                          color: isSelected
                              ? const Color(0xFF2F80ED)
                              : Colors.grey.shade300,
                          width: isSelected ? 2 : 1,
                        ),

                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(.05),
                            blurRadius: 12,
                            offset: const Offset(0, 6),
                          ),
                        ],
                      ),

                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,

                        children: [

                          Icon(
                            area.icon,
                            size: 42,
                            color: isSelected
                                ? const Color(0xFF2F80ED)
                                : Colors.black87,
                          ),

                          const SizedBox(height: 12),

                          Text(
                            area.name,
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 17,
                              color: isSelected
                                  ? const Color(0xFF2F80ED)
                                  : Colors.black87,
                            ),
                          ),

                          if (isSelected) ...[
                            const SizedBox(height: 10),
                            const Icon(
                              Icons.check_circle,
                              color: Color(0xFF27AE60),
                            ),
                          ],
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),

            const SizedBox(height: 18),

            SizedBox(
              width: double.infinity,
              height: 58,

              child: FilledButton.icon(
                icon: const Icon(Icons.arrow_forward_rounded),

                label: const Text(
                  "Continue",
                  style: TextStyle(fontSize: 17),
                ),

                onPressed: selected == null
                    ? null
                    : () {
                        final analysis = SymptomAnalysis();

                        analysis.bodyArea = selected!.name;

                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => SymptomInputScreen(
                              analysis: analysis,
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