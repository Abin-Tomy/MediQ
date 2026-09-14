import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/theme/app_colors.dart';

class SymptomAnalysisScreen extends StatefulWidget {
  const SymptomAnalysisScreen({super.key});

  @override
  State<SymptomAnalysisScreen> createState() => _SymptomAnalysisScreenState();
}

class _SymptomAnalysisScreenState extends State<SymptomAnalysisScreen> {
  final TextEditingController _textController = TextEditingController();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF1B2A30), // Dark premium teal bg
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        title: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.medical_services_rounded, color: AppColors.secondary, size: 20),
                const SizedBox(width: 8),
                Text(
                  "MediQ",
                  style: GoogleFonts.inter(
                    fontSize: 20,
                    fontWeight: FontWeight.w700,
                    color: Colors.white,
                  ),
                ),
              ],
            ),
            Text(
              "AI Symptom Analysis",
              style: GoogleFonts.inter(
                fontSize: 14,
                color: Colors.white70,
              ),
            ),
          ],
        ),
        centerTitle: true,
        actions: const [SizedBox(width: 48)], // Balance leading icon
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(20),
              children: [
                _buildUserMessage("Hi MediQ. I have a high fever, severe headache, muscle pain, and I've been feeling very nauseous for 3 days."),
                const SizedBox(height: 24),
                _buildAiMessage("Thank you for describing your symptoms. Based on your inputs, I have analyzed your condition. Here are the possible conditions the AI has identified:"),
                const SizedBox(height: 16),
                _buildResultCard(
                  number: "1",
                  title: "Dengue Fever",
                  urgency: "HIGH",
                  urgencyColor: AppColors.error,
                  confidence: "78%",
                  confidenceValue: 0.78,
                  symptoms: "High fever, severe headache, pain behind eyes, joint/muscle pain.",
                ),
                const SizedBox(height: 12),
                _buildResultCard(
                  number: "2",
                  title: "Leptospirosis",
                  urgency: "HIGH",
                  urgencyColor: AppColors.error,
                  confidence: "64%",
                  confidenceValue: 0.64,
                  symptoms: "High fever, headache, muscle aches, vomiting, jaundice.",
                ),
                const SizedBox(height: 12),
                _buildResultCard(
                  number: "3",
                  title: "Typhoid Fever",
                  urgency: "MODERATE",
                  urgencyColor: AppColors.warning,
                  confidence: "45%",
                  confidenceValue: 0.45,
                  symptoms: "Fever, weakness, stomach pain, headache, loss of appetite.",
                ),
                const SizedBox(height: 24),
                Text(
                  "* Disclaimer: MediQ is a decision support tool and does not replace professional medical diagnosis. Please consult a doctor.",
                  style: GoogleFonts.inter(
                    fontSize: 12,
                    color: Colors.white38,
                    fontStyle: FontStyle.italic,
                  ),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
          _buildInputArea(),
        ],
      ),
    );
  }

  Widget _buildUserMessage(String text) {
    return Align(
      alignment: Alignment.centerRight,
      child: Container(
        margin: const EdgeInsets.only(left: 40),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.15),
          borderRadius: const BorderRadius.only(
            topLeft: Radius.circular(24),
            topRight: Radius.circular(24),
            bottomLeft: Radius.circular(24),
            bottomRight: Radius.circular(4),
          ),
        ),
        child: Text(
          text,
          style: GoogleFonts.inter(
            color: Colors.white,
            fontSize: 15,
            height: 1.5,
          ),
        ),
      ),
    );
  }

  Widget _buildAiMessage(String text) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(right: 40),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        decoration: BoxDecoration(
          color: AppColors.primary.withOpacity(0.2),
          borderRadius: const BorderRadius.only(
            topLeft: Radius.circular(24),
            topRight: Radius.circular(24),
            bottomRight: Radius.circular(24),
            bottomLeft: Radius.circular(4),
          ),
          border: Border.all(
            color: AppColors.primary.withOpacity(0.3),
          ),
        ),
        child: Text(
          text,
          style: GoogleFonts.inter(
            color: Colors.white.withOpacity(0.9),
            fontSize: 15,
            height: 1.5,
          ),
        ),
      ),
    );
  }

  Widget _buildResultCard({
    required String number,
    required String title,
    required String urgency,
    required Color urgencyColor,
    required String confidence,
    required double confidenceValue,
    required String symptoms,
  }) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.2),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(
          color: Colors.white.withOpacity(0.05),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            "$number. $title",
            style: GoogleFonts.inter(
              fontSize: 18,
              fontWeight: FontWeight.w700,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Icon(Icons.warning_rounded, color: urgencyColor, size: 16),
                  const SizedBox(width: 6),
                  Text(
                    "Urgency: $urgency",
                    style: GoogleFonts.inter(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: urgencyColor,
                    ),
                  ),
                ],
              ),
              Row(
                children: [
                  Text(
                    "AI Confidence: ",
                    style: GoogleFonts.inter(
                      fontSize: 13,
                      color: Colors.white70,
                    ),
                  ),
                  Text(
                    confidence,
                    style: GoogleFonts.inter(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: AppColors.secondary,
                    ),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 16),
          Text(
            "Symptoms: $symptoms",
            style: GoogleFonts.inter(
              fontSize: 14,
              color: Colors.white60,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 16),
          Align(
            alignment: Alignment.centerRight,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                border: Border.all(color: Colors.white30),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Text(
                "View Details",
                style: GoogleFonts.inter(
                  fontSize: 13,
                  fontWeight: FontWeight.w500,
                  color: Colors.white,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInputArea() {
    return Container(
      padding: const EdgeInsets.only(left: 20, right: 20, top: 16, bottom: 32),
      decoration: BoxDecoration(
        color: const Color(0xFF131D21), // Darker bottom
        border: Border(
          top: BorderSide(color: Colors.white.withOpacity(0.05)),
        ),
      ),
      child: Row(
        children: [
          Expanded(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.1),
                borderRadius: BorderRadius.circular(30),
              ),
              child: TextField(
                controller: _textController,
                style: GoogleFonts.inter(color: Colors.white),
                decoration: InputDecoration(
                  hintText: "Ask about specific symptoms...",
                  hintStyle: GoogleFonts.inter(color: Colors.white38),
                  border: InputBorder.none,
                ),
              ),
            ),
          ),
          const SizedBox(width: 12),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.1),
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.send_rounded,
              color: AppColors.secondary,
              size: 20,
            ),
          ),
        ],
      ),
    );
  }
}
