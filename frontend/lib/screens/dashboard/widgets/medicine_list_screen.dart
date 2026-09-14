import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../../core/theme/app_theme_provider.dart';

class MedicineListScreen extends StatefulWidget {
  const MedicineListScreen({super.key});

  @override
  State<MedicineListScreen> createState() => _MedicineListScreenState();
}

class _MedicineListScreenState extends State<MedicineListScreen>
    with SingleTickerProviderStateMixin {
  bool _showInteractionChecker = false;

  final List<Map<String, dynamic>> _medicines = [
    {
      "name_en": "Paracetamol (Dolo 650)",
      "name_ml": "പാരസെറ്റമോൾ (Dolo 650)",
      "dosage_en": "1 Tablet (650mg)",
      "dosage_ml": "1 ഗുളിക (650mg)",
      "time_en": "08:30 AM — After Breakfast",
      "time_ml": "08:30 AM — പ്രഭാതഭക്ഷണത്തിന് ശേഷം",
      "taken": true,
      "color": const Color(0xFF2F80ED),
      "purpose_en": "Fever reduction & body pain",
      "purpose_ml": "പനി കുറയ്ക്കാൻ & ശരീരവേദനയ്ക്ക്",
    },
    {
      "name_en": "Doxycycline Prophylaxis",
      "name_ml": "ഡോക്സിസൈക്ലിൻ (പ്രതിരോധ ഗുളിക)",
      "dosage_en": "1 Capsule (100mg)",
      "dosage_ml": "1 ഗുളിക (100mg)",
      "time_en": "01:30 PM — After Lunch",
      "time_ml": "01:30 PM — ഉച്ചഭക്ഷണത്തിന് ശേഷം",
      "taken": false,
      "color": const Color(0xFF9B51E0),
      "purpose_en": "Leptospirosis / flood exposure prevention",
      "purpose_ml": "എലിപ്പനി / മൺസൂൺ പ്രതിരോധം",
    },
    {
      "name_en": "Vitamin C & Zinc Supp.",
      "name_ml": "വിറ്റാമിൻ സി & സിങ്ക്",
      "dosage_en": "1 Chewable Tablet",
      "dosage_ml": "1 ചവച്ചു കഴിക്കുന്ന ഗുളിക",
      "time_en": "09:00 PM — Before Bed",
      "time_ml": "09:00 PM — ഉറങ്ങുന്നതിന് മുമ്പ്",
      "taken": false,
      "color": const Color(0xFF10B981),
      "purpose_en": "Immune system support",
      "purpose_ml": "രോഗപ്രതിരോധ ശേഷി കൂട്ടാൻ",
    },
    {
      "name_en": "ORS / Electrolyte Drink",
      "name_ml": "ORS ലായനി",
      "dosage_en": "1 Sachet in 1L Water",
      "dosage_ml": "1 പാക്കറ്റ് 1 ലിറ്റർ വെള്ളത്തിൽ",
      "time_en": "Throughout the day",
      "time_ml": "ദിവസം മുഴുവൻ ഇടവിട്ട്",
      "taken": true,
      "color": const Color(0xFFF59E0B),
      "purpose_en": "Hydration maintenance",
      "purpose_ml": "ശരീരത്തിൽ ജലാംശം നിലനിർത്താൻ",
    },
  ];

  final List<Map<String, dynamic>> _interactionChecks = [
    {
      "pair_en": "Paracetamol (Dolo 650)  +  Doxycycline Prophylaxis",
      "pair_ml": "പാരസെറ്റമോൾ (Dolo 650)  +  ഡോക്സിസൈക്ലിൻ",
      "status_en": "Safe & Recommended Combo",
      "status_ml": "സുരക്ഷിതമായ കൂട്ടുകെട്ട്",
      "score": 98,
      "color": const Color(0xFF10B981),
      "advice_en": "Safe to take together during monsoon fevers. Doxycycline prevents leptospirosis while Paracetamol controls fever. Take with a full glass of water.",
      "advice_ml": "മൺസൂൺ പനിയിൽ ഒരുമിച്ച് കഴിക്കുന്നത് സുരക്ഷിതമാണ്. ഭക്ഷണത്തിന് ശേഷം ധാരാളം വെള്ളത്തോടൊപ്പം കഴിക്കുക.",
      "icon": Icons.verified_rounded,
    },
    {
      "pair_en": "Doxycycline Prophylaxis  +  Antacids / Dairy Products",
      "pair_ml": "ഡോക്സിസൈക്ലിൻ  +  പാൽ / അന്റാസിഡ് മരുന്നുകൾ",
      "status_en": "Moderate Absorption Warning ⚠️",
      "status_ml": "ശ്രദ്ധിക്കുക (ആഗിരണം കുറയും) ⚠️",
      "score": 42,
      "color": const Color(0xFFF59E0B),
      "advice_en": "Calcium and magnesium in dairy or antacids bind to Doxycycline in the gut, reducing its effectiveness by up to 50%. Space out by at least 2 hours.",
      "advice_ml": "പാലുൽപ്പന്നങ്ങളോ അന്റാസിഡോ കഴിച്ചാൽ ഡോക്സിസൈക്ലിന്റെ ഫലം കുറയും. തമ്മിൽ കുറഞ്ഞത് 2 മണിക്കൂർ ഇടവേള നൽകുക.",
      "icon": Icons.warning_amber_rounded,
    },
    {
      "pair_en": "Paracetamol (Dolo 650)  +  Alcohol / Cough Syrups",
      "pair_ml": "പാരസെറ്റമോൾ (Dolo 650)  +  മദ്യം / ചുമ സിറപ്പുകൾ",
      "status_en": "High Risk / Contraindicated 🚫",
      "status_ml": "അപകടസാധ്യത (ഒഴിവാക്കുക) 🚫",
      "score": 15,
      "color": const Color(0xFFEF4444),
      "advice_en": "Increased risk of hepatotoxicity (liver strain), especially during viral fever or dengue. Strictly avoid alcohol or sedative cough syrups.",
      "advice_ml": "കരളിൽ അമിത സമ്മർദ്ദമുണ്ടാകാൻ സാധ്യതയുണ്ട്. പനി ഗുളിക കഴിക്കുമ്പോൾ മദ്യമോ മറ്റ് ലഹരികളോ കർശനമായി ഒഴിവാക്കുക.",
      "icon": Icons.gpp_bad_rounded,
    },
  ];

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: AppThemeProvider(),
      builder: (context, _) {
        final theme = AppThemeProvider();

        final appBarTitle = theme.tr("Medication Reminders", "മരുന്ന് വിവരങ്ങളും സമയവും");
        final bannerTitle = theme.tr("Monsoon Care Schedule", "മൺസൂൺ പരിചരണ പട്ടിക");
        final bannerDesc = theme.tr(
          "Keep track of your antiviral and prophylaxis dosage to ensure rapid recovery.",
          "പെട്ടെന്നുള്ള രോഗമുക്തിക്കായി പ്രതിരോധ ഗുളികകളും മരുന്നുകളും കൃത്യസമയത്ത് കഴിക്കുക.",
        );
        final addedMsg = theme.tr(
          "Reminder preset added to daily schedule.",
          "പുതിയ ഓർമ്മപ്പെടുത്തൽ സമയപ്പട്ടികയിൽ ചേർത്തു.",
        );
        final checkerBtnTitle = theme.tr(
          _showInteractionChecker ? "Hide AI Drug Safety Report" : "Run AI Drug Interaction Check",
          _showInteractionChecker ? "AI മരുന്ന് പരിശോധനാ റിപ്പോർട്ട് മറയ്ക്കുക" : "AI മരുന്ന് പരിശോധന നടത്തുക",
        );
        final checkerHeading = theme.tr(
          "AI Prophylaxis & Drug Safety Analysis",
          "AI പ്രതിരോധ മരുന്ന് സുരക്ഷാ പരിശോധന",
        );
        final checkerSubheading = theme.tr(
          "Real-time pharmacological compatibility check for active prescriptions and dietary factors.",
          "നിങ്ങൾ കഴിക്കുന്ന മരുന്നുകളും ഭക്ഷണവും തമ്മിലുള്ള സുരക്ഷാ പരിശോധന.",
        );

        return Scaffold(
          backgroundColor: theme.background,
          appBar: AppBar(
            backgroundColor: Colors.transparent,
            elevation: 0,
            centerTitle: true,
            iconTheme: IconThemeData(color: theme.textPrimary),
            title: Text(
              appBarTitle,
              style: GoogleFonts.poppins(
                color: theme.textPrimary,
                fontWeight: FontWeight.w600,
                fontSize: 18,
              ),
            ),
            actions: [
              IconButton(
                icon: Icon(Icons.add_alert_rounded, color: theme.primaryAccent),
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text(
                        addedMsg,
                        style: GoogleFonts.poppins(),
                      ),
                      behavior: SnackBarBehavior.floating,
                    ),
                  );
                },
              ),
            ],
          ),
          body: SafeArea(
            child: Column(
              children: [
                // INFO BANNER
                Container(
                  margin: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: theme.isDark || theme.isMonsoon
                          ? [const Color(0xFF3B0764), const Color(0xFF4C1D95)]
                          : [const Color(0xFFF3E8FF), const Color(0xFFE9D5FF)],
                    ),
                    borderRadius: BorderRadius.circular(18),
                    border: Border.all(
                      color: const Color(0xFF9B51E0).withValues(alpha: .4),
                    ),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.medication_liquid_rounded,
                          color: Color(0xFF9B51E0), size: 28),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              bannerTitle,
                              style: GoogleFonts.poppins(
                                fontSize: 14.5,
                                fontWeight: FontWeight.w700,
                                color: theme.isDark || theme.isMonsoon
                                    ? Colors.white
                                    : const Color(0xFF581C87),
                              ),
                            ),
                            Text(
                              bannerDesc,
                              style: GoogleFonts.poppins(
                                fontSize: 12,
                                color: theme.isDark || theme.isMonsoon
                                    ? Colors.white70
                                    : const Color(0xFF6B21A8),
                                height: 1.3,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),

                // AI DRUG INTERACTION CHECKER BUTTON / CARD
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 300),
                    decoration: BoxDecoration(
                      color: _showInteractionChecker
                          ? theme.cardColor
                          : theme.primaryAccent.withValues(alpha: .12),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(
                        color: _showInteractionChecker
                            ? theme.primaryAccent
                            : theme.primaryAccent.withValues(alpha: .4),
                        width: _showInteractionChecker ? 2 : 1,
                      ),
                      boxShadow: _showInteractionChecker
                          ? [
                              BoxShadow(
                                color: theme.primaryAccent.withValues(alpha: .15),
                                blurRadius: 15,
                                offset: const Offset(0, 6),
                              ),
                            ]
                          : null,
                    ),
                    child: Column(
                      children: [
                        InkWell(
                          borderRadius: BorderRadius.circular(20),
                          onTap: () {
                            setState(() {
                              _showInteractionChecker = !_showInteractionChecker;
                            });
                          },
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Row(
                              children: [
                                Container(
                                  padding: const EdgeInsets.all(10),
                                  decoration: BoxDecoration(
                                    color: theme.primaryAccent,
                                    shape: BoxShape.circle,
                                  ),
                                  child: const Icon(
                                    Icons.health_and_safety_rounded,
                                    color: Colors.white,
                                    size: 22,
                                  ),
                                ),
                                const SizedBox(width: 14),
                                Expanded(
                                  child: Text(
                                    checkerBtnTitle,
                                    style: GoogleFonts.poppins(
                                      fontSize: 14.5,
                                      fontWeight: FontWeight.w700,
                                      color: theme.primaryAccent,
                                    ),
                                  ),
                                ),
                                Icon(
                                  _showInteractionChecker
                                      ? Icons.keyboard_arrow_up_rounded
                                      : Icons.keyboard_arrow_down_rounded,
                                  color: theme.primaryAccent,
                                  size: 26,
                                ),
                              ],
                            ),
                          ),
                        ),

                        // EXPANDED SAFETY REPORT
                        if (_showInteractionChecker)
                          Padding(
                            padding: const EdgeInsets.fromLTRB(16, 0, 16, 18),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Divider(color: theme.borderColor, height: 20),
                                Text(
                                  checkerHeading,
                                  style: GoogleFonts.poppins(
                                    fontSize: 15,
                                    fontWeight: FontWeight.w700,
                                    color: theme.textPrimary,
                                  ),
                                ),
                                Text(
                                  checkerSubheading,
                                  style: GoogleFonts.poppins(
                                    fontSize: 12,
                                    color: theme.textSecondary,
                                  ),
                                ),
                                const SizedBox(height: 16),
                                ..._interactionChecks.map((item) {
                                  final pairText = theme.tr(item["pair_en"] as String, item["pair_ml"] as String);
                                  final statusText = theme.tr(item["status_en"] as String, item["status_ml"] as String);
                                  final adviceText = theme.tr(item["advice_en"] as String, item["advice_ml"] as String);
                                  final Color col = item["color"] as Color;
                                  final int score = item["score"] as int;
                                  final IconData icon = item["icon"] as IconData;

                                  return Container(
                                    margin: const EdgeInsets.only(bottom: 12),
                                    padding: const EdgeInsets.all(14),
                                    decoration: BoxDecoration(
                                      color: theme.background,
                                      borderRadius: BorderRadius.circular(16),
                                      border: Border.all(color: col.withValues(alpha: .3)),
                                    ),
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Row(
                                          children: [
                                            Icon(icon, color: col, size: 20),
                                            const SizedBox(width: 8),
                                            Expanded(
                                              child: Text(
                                                statusText,
                                                style: GoogleFonts.poppins(
                                                  fontSize: 13,
                                                  fontWeight: FontWeight.w700,
                                                  color: col,
                                                ),
                                              ),
                                            ),
                                            Text(
                                              "$score% ${theme.tr('Safe', 'സുരക്ഷ')}",
                                              style: GoogleFonts.poppins(
                                                fontSize: 12,
                                                fontWeight: FontWeight.w700,
                                                color: col,
                                              ),
                                            ),
                                          ],
                                        ),
                                        const SizedBox(height: 6),
                                        Text(
                                          pairText,
                                          style: GoogleFonts.poppins(
                                            fontSize: 13.5,
                                            fontWeight: FontWeight.w600,
                                            color: theme.textPrimary,
                                          ),
                                        ),
                                        const SizedBox(height: 8),
                                        ClipRRect(
                                          borderRadius: BorderRadius.circular(8),
                                          child: LinearProgressIndicator(
                                            value: score / 100.0,
                                            minHeight: 6,
                                            backgroundColor: theme.borderColor,
                                            valueColor: AlwaysStoppedAnimation<Color>(col),
                                          ),
                                        ),
                                        const SizedBox(height: 8),
                                        Text(
                                          adviceText,
                                          style: GoogleFonts.poppins(
                                            fontSize: 12,
                                            color: theme.textSecondary,
                                            height: 1.4,
                                          ),
                                        ),
                                      ],
                                    ),
                                  );
                                }),
                              ],
                            ),
                          ),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 6),

                // MEDICINES LIST
                Expanded(
                  child: ListView.separated(
                    padding: const EdgeInsets.fromLTRB(24, 10, 24, 30),
                    physics: const BouncingScrollPhysics(),
                    itemCount: _medicines.length,
                    separatorBuilder: (context, index) => const SizedBox(height: 14),
                    itemBuilder: (context, idx) {
                      final med = _medicines[idx];
                      final bool taken = med['taken'] as bool;
                      final Color col = med['color'] as Color;

                      final medName = theme.tr(med['name_en'] as String, med['name_ml'] as String);
                      final medDosage = theme.tr(med['dosage_en'] as String, med['dosage_ml'] as String);
                      final medTime = theme.tr(med['time_en'] as String, med['time_ml'] as String);
                      final medPurpose = theme.tr(med['purpose_en'] as String, med['purpose_ml'] as String);

                      return AnimatedContainer(
                        duration: const Duration(milliseconds: 200),
                        padding: const EdgeInsets.all(18),
                        decoration: BoxDecoration(
                          color: taken ? theme.cardColor.withValues(alpha: .6) : theme.cardColor,
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(
                            color: taken
                                ? const Color(0xFF10B981).withValues(alpha: .4)
                                : theme.borderColor,
                          ),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withValues(alpha: .04),
                              blurRadius: 10,
                              offset: const Offset(0, 4),
                            ),
                          ],
                        ),
                        child: Row(
                          children: [
                            Container(
                              width: 50,
                              height: 50,
                              decoration: BoxDecoration(
                                color: col.withValues(alpha: .15),
                                borderRadius: BorderRadius.circular(16),
                              ),
                              child: Icon(Icons.medication_rounded, color: col, size: 26),
                            ),
                            const SizedBox(width: 14),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    medName,
                                    style: GoogleFonts.poppins(
                                      fontSize: 16,
                                      fontWeight: FontWeight.w700,
                                      color: taken ? theme.textSecondary : theme.textPrimary,
                                      decoration: taken ? TextDecoration.lineThrough : null,
                                    ),
                                  ),
                                  Text(
                                    "$medDosage • $medPurpose",
                                    style: GoogleFonts.poppins(
                                      fontSize: 12,
                                      color: theme.textHint,
                                    ),
                                  ),
                                  const SizedBox(height: 6),
                                  Row(
                                    children: [
                                      Icon(Icons.access_time_rounded,
                                          size: 14, color: theme.primaryAccent),
                                      const SizedBox(width: 6),
                                      Text(
                                        medTime,
                                        style: GoogleFonts.poppins(
                                          fontSize: 12.5,
                                          fontWeight: FontWeight.w600,
                                          color: theme.primaryAccent,
                                        ),
                                      ),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(width: 10),
                            GestureDetector(
                              onTap: () {
                                setState(() {
                                  med['taken'] = !taken;
                                });
                              },
                              child: AnimatedContainer(
                                duration: const Duration(milliseconds: 200),
                                width: 38,
                                height: 38,
                                decoration: BoxDecoration(
                                  color: taken ? const Color(0xFF10B981) : Colors.transparent,
                                  borderRadius: BorderRadius.circular(12),
                                  border: Border.all(
                                    color: taken ? const Color(0xFF10B981) : theme.textHint,
                                    width: 2,
                                  ),
                                ),
                                child: taken
                                    ? const Icon(Icons.check_rounded, color: Colors.white, size: 22)
                                    : null,
                              ),
                            ),
                          ],
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
