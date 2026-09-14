import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/theme/app_theme_provider.dart';
import '../../models/body_area.dart';
import '../../models/symptom_analysis.dart';
import 'symptom_input_screen.dart';
import 'widgets/anatomical_body_diagram.dart';

class BodyAreaScreen extends StatefulWidget {
  const BodyAreaScreen({super.key});

  @override
  State<BodyAreaScreen> createState() => _BodyAreaScreenState();
}

class _BodyAreaScreenState extends State<BodyAreaScreen> {
  BodyArea? selected;

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: AppThemeProvider(),
      builder: (context, _) {
        final theme = AppThemeProvider();

        final title = theme.tr("Where does it hurt?", "എവിടെയാണ് ബുദ്ധിമുട്ട്?");
        final subtitle = theme.tr(
          "Tap the anatomical diagram or select a zone below.",
          "ഡയഗ്രാമിലോ താഴെയുള്ള ലിസ്റ്റിലോ തൊടുക.",
        );
        final continueLbl = theme.tr("Continue", "തുടരുക");

        return Scaffold(
          backgroundColor: theme.background,
          appBar: AppBar(
            backgroundColor: Colors.transparent,
            elevation: 0,
            iconTheme: IconThemeData(color: theme.textPrimary),
            title: Text(
              title,
              style: GoogleFonts.poppins(
                fontWeight: FontWeight.w600,
                color: theme.textPrimary,
              ),
            ),
          ),
          body: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  subtitle,
                  style: GoogleFonts.poppins(
                    color: theme.textSecondary,
                    fontSize: 14,
                  ),
                ),

                const SizedBox(height: 18),

                // ANATOMICAL BODY MAPPER
                AnatomicalBodyDiagram(
                  selectedArea: selected,
                  onAreaSelected: (area) {
                    setState(() {
                      selected = area;
                    });
                  },
                ),

                const SizedBox(height: 20),

                Text(
                  theme.tr("Or choose from categories:", "അല്ലെങ്കിൽ താഴെ നിന്ന് തിരഞ്ഞെടുക്കുക:"),
                  style: GoogleFonts.poppins(
                    fontSize: 12.5,
                    fontWeight: FontWeight.w600,
                    color: theme.textSecondary,
                  ),
                ),

                const SizedBox(height: 12),

                // COMPACT CHIPS GRID
                Expanded(
                  child: GridView.builder(
                    itemCount: BodyArea.items.length,
                    physics: const BouncingScrollPhysics(),
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 3,
                      crossAxisSpacing: 12,
                      mainAxisSpacing: 12,
                      childAspectRatio: 1.3,
                    ),
                    itemBuilder: (context, index) {
                      final area = BodyArea.items[index];
                      final isSelected = selected == area;

                      return InkWell(
                        borderRadius: BorderRadius.circular(16),
                        onTap: () {
                          setState(() {
                            selected = area;
                          });
                        },
                        child: AnimatedContainer(
                          duration: const Duration(milliseconds: 250),
                          decoration: BoxDecoration(
                            color: isSelected
                                ? theme.primaryAccent.withValues(alpha: .15)
                                : theme.cardColor,
                            borderRadius: BorderRadius.circular(16),
                            border: Border.all(
                              color: isSelected
                                  ? theme.primaryAccent
                                  : theme.borderColor,
                              width: isSelected ? 2 : 1,
                            ),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withValues(alpha: .04),
                                blurRadius: 8,
                                offset: const Offset(0, 4),
                              ),
                            ],
                          ),
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(
                                area.icon,
                                size: 26,
                                color: isSelected
                                    ? theme.primaryAccent
                                    : theme.textPrimary,
                              ),
                              const SizedBox(height: 4),
                              Text(
                                area.name,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: GoogleFonts.poppins(
                                  fontWeight: isSelected
                                      ? FontWeight.w700
                                      : FontWeight.w500,
                                  fontSize: 12,
                                  color: isSelected
                                      ? theme.primaryAccent
                                      : theme.textPrimary,
                                ),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),

                const SizedBox(height: 16),

                // CONTINUE BUTTON
                SizedBox(
                  width: double.infinity,
                  height: 56,
                  child: ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: theme.primaryAccent,
                      foregroundColor: Colors.white,
                      disabledBackgroundColor: theme.borderColor,
                      elevation: 0,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(18),
                      ),
                    ),
                    icon: const Icon(Icons.arrow_forward_rounded, size: 20),
                    label: Text(
                      continueLbl,
                      style: GoogleFonts.poppins(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
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
      },
    );
  }
}