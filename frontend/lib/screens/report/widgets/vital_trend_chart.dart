import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../../../core/theme/app_theme_provider.dart';

class VitalTrendChart extends StatefulWidget {
  const VitalTrendChart({super.key});

  @override
  State<VitalTrendChart> createState() => _VitalTrendChartState();
}

class _VitalTrendChartState extends State<VitalTrendChart>
    with SingleTickerProviderStateMixin {
  int _selectedTabIndex = 0; // 0: Platelets, 1: Hemoglobin, 2: Blood Sugar
  late AnimationController _chartAnimController;
  late Animation<double> _chartProgress;

  final List<Map<String, dynamic>> _vitalsData = [
    {
      "name_en": "Platelet Count",
      "name_ml": "പ്ലേറ്റ്‌ലെറ്റ് കൗണ്ട്",
      "unit": "/mcL (in 1000s)",
      "normalRange": "150 - 450",
      "normalMin": 150.0,
      "normalMax": 450.0,
      "chartMin": 50.0,
      "chartMax": 500.0,
      "color": const Color(0xFF2F80ED),
      "history": [
        {"month_en": "Jan", "month_ml": "ജനു", "value": 240.0, "status_en": "Normal", "status_ml": "സാധാരണ"},
        {"month_en": "Mar", "month_ml": "മാർ", "value": 210.0, "status_en": "Normal", "status_ml": "സാധാരണ"},
        {"month_en": "May", "month_ml": "മേയ്", "value": 175.0, "status_en": "Borderline", "status_ml": "കുറവ്"},
        {"month_en": "Jul (Now)", "month_ml": "ജൂലൈ", "value": 91.0, "status_en": "Critical Low", "status_ml": "അപകടനിലയിൽ"},
      ],
      "insight_en": "Sharp drop observed during recent monsoon onset. Immediate medical evaluation recommended for dengue/viral screening.",
      "insight_ml": "മൺസൂൺ തുടക്കത്തിൽ പ്ലേറ്റ്‌ലെറ്റ് പെട്ടെന്ന് കുറഞ്ഞിരിക്കുന്നു. ഡെങ്കിപ്പനി പരിശോധനയ്ക്കായി ഡോക്ടറെ കാണുക.",
    },
    {
      "name_en": "Hemoglobin",
      "name_ml": "ഹീമോഗ്ലോബിൻ",
      "unit": "g/dL",
      "normalRange": "12.0 - 15.5",
      "normalMin": 12.0,
      "normalMax": 15.5,
      "chartMin": 8.0,
      "chartMax": 18.0,
      "color": const Color(0xFF10B981),
      "history": [
        {"month_en": "Jan", "month_ml": "ജനു", "value": 13.5, "status_en": "Normal", "status_ml": "സാധാരണ"},
        {"month_en": "Mar", "month_ml": "മാർ", "value": 13.2, "status_en": "Normal", "status_ml": "സാധാരണ"},
        {"month_en": "May", "month_ml": "മേയ്", "value": 12.8, "status_en": "Normal", "status_ml": "സാധാരണ"},
        {"month_en": "Jul (Now)", "month_ml": "ജൂലൈ", "value": 12.4, "status_en": "Normal", "status_ml": "സാധാരണ"},
      ],
      "insight_en": "Hemoglobin remains stable and well within standard reference limits.",
      "insight_ml": "ഹീമോഗ്ലോബിൻ അളവ് ആരോഗ്യകരവും സ്ഥിരവുമാണ്.",
    },
    {
      "name_en": "Fasting Blood Sugar",
      "name_ml": "പ്രഭാത രക്തശർക്കര",
      "unit": "mg/dL",
      "normalRange": "70 - 100",
      "normalMin": 70.0,
      "normalMax": 100.0,
      "chartMin": 50.0,
      "chartMax": 160.0,
      "color": const Color(0xFFF59E0B),
      "history": [
        {"month_en": "Jan", "month_ml": "ജനു", "value": 88.0, "status_en": "Normal", "status_ml": "സാധാരണ"},
        {"month_en": "Mar", "month_ml": "മാർ", "value": 94.0, "status_en": "Normal", "status_ml": "സാധാരണ"},
        {"month_en": "May", "month_ml": "മേയ്", "value": 108.0, "status_en": "Borderline", "status_ml": "ചെറിയ വർദ്ധനവ്"},
        {"month_en": "Jul (Now)", "month_ml": "ജൂലൈ", "value": 115.0, "status_en": "Elevated", "status_ml": "വർദ്ധിച്ചു"},
      ],
      "insight_en": "Slight upward trend in glucose over the past 4 months. Dietary adjustments advised.",
      "insight_ml": "കഴിഞ്ഞ 4 മാസമായി ഷുഗർ അളവിൽ ചെറിയ വർദ്ധനവ് കാണുന്നു. ഭക്ഷണക്രമം ശ്രദ്ധിക്കുക.",
    },
  ];

  @override
  void initState() {
    super.initState();
    _chartAnimController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    );
    _chartProgress = CurvedAnimation(
      parent: _chartAnimController,
      curve: Curves.easeInOutCubic,
    );
    _chartAnimController.forward();
  }

  void _switchTab(int index) {
    if (_selectedTabIndex != index) {
      setState(() {
        _selectedTabIndex = index;
      });
      _chartAnimController.reset();
      _chartAnimController.forward();
    }
  }

  @override
  void dispose() {
    _chartAnimController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: AppThemeProvider(),
      builder: (context, _) {
        final theme = AppThemeProvider();
        final currentVital = _vitalsData[_selectedTabIndex];

        final title = theme.tr("Lab Vital Trend Analytics", "രക്തപരിശോധനാ ഫലങ്ങളുടെ മുൻകാല മാറ്റങ്ങൾ");
        final subtitle = theme.tr(
          "AI tracking across your past 4 lab diagnostics",
          "കഴിഞ്ഞ 4 പരിശോധനകളിലെ മാറ്റങ്ങൾ AI വിശകലനം ചെയ്യുന്നു",
        );
        final normalLbl = theme.tr("Normal Reference Range:", "സാധാരണ അളവ്:");

        final vitalName = theme.tr(currentVital["name_en"] as String, currentVital["name_ml"] as String);
        final insightText = theme.tr(currentVital["insight_en"] as String, currentVital["insight_ml"] as String);
        final historyList = currentVital["history"] as List<Map<String, dynamic>>;

        return Container(
          width: double.infinity,
          padding: const EdgeInsets.all(22),
          decoration: BoxDecoration(
            color: theme.cardColor,
            borderRadius: BorderRadius.circular(24),
            border: Border.all(color: theme.borderColor),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: .04),
                blurRadius: 16,
                offset: const Offset(0, 6),
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: (currentVital["color"] as Color).withValues(alpha: .15),
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: Icon(
                      Icons.insights_rounded,
                      color: currentVital["color"] as Color,
                      size: 24,
                    ),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          title,
                          style: GoogleFonts.poppins(
                            fontSize: 17,
                            fontWeight: FontWeight.w700,
                            color: theme.textPrimary,
                          ),
                        ),
                        Text(
                          subtitle,
                          style: GoogleFonts.poppins(
                            fontSize: 12,
                            color: theme.textSecondary,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 20),

              // TAB SELECTOR
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                physics: const BouncingScrollPhysics(),
                child: Row(
                  children: List.generate(_vitalsData.length, (idx) {
                    final item = _vitalsData[idx];
                    final isSel = idx == _selectedTabIndex;
                    final tabName = theme.tr(item["name_en"] as String, item["name_ml"] as String);
                    final col = item["color"] as Color;

                    return Padding(
                      padding: const EdgeInsets.only(right: 10),
                      child: InkWell(
                        onTap: () => _switchTab(idx),
                        borderRadius: BorderRadius.circular(16),
                        child: AnimatedContainer(
                          duration: const Duration(milliseconds: 200),
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                          decoration: BoxDecoration(
                            color: isSel ? col : theme.background,
                            borderRadius: BorderRadius.circular(16),
                            border: Border.all(
                              color: isSel ? col : theme.borderColor,
                            ),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(
                                Icons.fiber_manual_record_rounded,
                                size: 12,
                                color: isSel ? Colors.white : col,
                              ),
                              const SizedBox(width: 8),
                              Text(
                                tabName,
                                style: GoogleFonts.poppins(
                                  fontSize: 13,
                                  fontWeight: isSel ? FontWeight.w700 : FontWeight.w500,
                                  color: isSel ? Colors.white : theme.textPrimary,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    );
                  }),
                ),
              ),

              const SizedBox(height: 24),

              // VITAL HEADER & RANGE
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    "$vitalName (${currentVital["unit"]})",
                    style: GoogleFonts.poppins(
                      fontSize: 15,
                      fontWeight: FontWeight.w700,
                      color: theme.textPrimary,
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: const Color(0xFF10B981).withValues(alpha: .12),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Text(
                      "$normalLbl ${currentVital["normalRange"]}",
                      style: GoogleFonts.poppins(
                        fontSize: 11.5,
                        fontWeight: FontWeight.w600,
                        color: const Color(0xFF10B981),
                      ),
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 24),

              // CUSTOM PAINTED TREND CHART
              AnimatedBuilder(
                animation: _chartProgress,
                builder: (context, _) {
                  return SizedBox(
                    height: 220,
                    width: double.infinity,
                    child: CustomPaint(
                      painter: _VitalChartPainter(
                        data: historyList,
                        normalMin: currentVital["normalMin"] as double,
                        normalMax: currentVital["normalMax"] as double,
                        chartMin: currentVital["chartMin"] as double,
                        chartMax: currentVital["chartMax"] as double,
                        lineColor: currentVital["color"] as Color,
                        textColor: theme.textSecondary,
                        gridColor: theme.borderColor,
                        progress: _chartProgress.value,
                        isMalayalam: theme.isMalayalam,
                      ),
                    ),
                  );
                },
              ),

              const SizedBox(height: 20),

              // AI INSIGHT BOX
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: (currentVital["color"] as Color).withValues(alpha: .1),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: (currentVital["color"] as Color).withValues(alpha: .3),
                  ),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(
                      Icons.auto_awesome_rounded,
                      color: currentVital["color"] as Color,
                      size: 20,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            theme.tr("AI Clinical Insight", "AI ആരോഗ്യ നിർദ്ദേശം"),
                            style: GoogleFonts.poppins(
                              fontSize: 13,
                              fontWeight: FontWeight.w700,
                              color: currentVital["color"] as Color,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            insightText,
                            style: GoogleFonts.poppins(
                              fontSize: 12.5,
                              color: theme.textPrimary,
                              height: 1.4,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _VitalChartPainter extends CustomPainter {
  final List<Map<String, dynamic>> data;
  final double normalMin;
  final double normalMax;
  final double chartMin;
  final double chartMax;
  final Color lineColor;
  final Color textColor;
  final Color gridColor;
  final double progress;
  final bool isMalayalam;

  _VitalChartPainter({
    required this.data,
    required this.normalMin,
    required this.normalMax,
    required this.chartMin,
    required this.chartMax,
    required this.lineColor,
    required this.textColor,
    required this.gridColor,
    required this.progress,
    required this.isMalayalam,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final double leftPad = 40.0;
    final double rightPad = 20.0;
    final double topPad = 20.0;
    final double bottomPad = 35.0;
    final double chartWidth = size.width - leftPad - rightPad;
    final double chartHeight = size.height - topPad - bottomPad;

    double getY(double val) {
      final normalized = (val - chartMin) / (chartMax - chartMin);
      return topPad + chartHeight - (normalized * chartHeight);
    }

    // Draw normal reference range band
    final normalTop = getY(normalMax.clamp(chartMin, chartMax));
    final normalBottom = getY(normalMin.clamp(chartMin, chartMax));
    final bandPaint = Paint()
      ..color = const Color(0xFF10B981).withValues(alpha: .12)
      ..style = PaintingStyle.fill;
    canvas.drawRect(
      Rect.fromLTRB(leftPad, normalTop, size.width - rightPad, normalBottom),
      bandPaint,
    );

    // Draw grid lines and Y-axis labels
    final gridPaint = Paint()
      ..color = gridColor.withValues(alpha: .6)
      ..strokeWidth = 1.0;

    final int gridSteps = 4;
    for (int i = 0; i <= gridSteps; i++) {
      final val = chartMin + (chartMax - chartMin) * (i / gridSteps);
      final y = getY(val);

      canvas.drawLine(Offset(leftPad, y), Offset(size.width - rightPad, y), gridPaint);

      final textSpan = TextSpan(
        text: val.round().toString(),
        style: GoogleFonts.poppins(color: textColor, fontSize: 10, fontWeight: FontWeight.w500),
      );
      final textPainter = TextPainter(text: textSpan, textDirection: TextDirection.ltr);
      textPainter.layout();
      textPainter.paint(canvas, Offset(leftPad - textPainter.width - 6, y - textPainter.height / 2));
    }

    // Calculate point positions
    final List<Offset> points = [];
    final int count = data.length;
    for (int i = 0; i < count; i++) {
      final double x = leftPad + (chartWidth / (count - 1)) * i;
      final double val = (data[i]["value"] as num).toDouble();
      final double y = getY(val);
      points.add(Offset(x, y));
    }

    // Draw smooth path
    final path = Path();
    if (points.isNotEmpty) {
      path.moveTo(points[0].dx, points[0].dy);
      for (int i = 0; i < points.length - 1; i++) {
        final p0 = points[i];
        final p1 = points[i + 1];
        final midX = (p0.dx + p1.dx) / 2;
        path.cubicTo(midX, p0.dy, midX, p1.dy, p1.dx, p1.dy);
      }
    }

    // Draw animated path
    final pathMetrics = path.computeMetrics();
    final animatedPath = Path();
    for (final metric in pathMetrics) {
      animatedPath.addPath(metric.extractPath(0, metric.length * progress), Offset.zero);
    }

    // Draw gradient fill below line
    if (points.isNotEmpty && progress > 0) {
      final fillPath = Path.from(animatedPath);
      final lastPointX = leftPad + (chartWidth * progress);
      fillPath.lineTo(lastPointX, topPad + chartHeight);
      fillPath.lineTo(leftPad, topPad + chartHeight);
      fillPath.close();

      final fillPaint = Paint()
        ..shader = LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            lineColor.withValues(alpha: .35),
            lineColor.withValues(alpha: .0),
          ],
        ).createShader(Rect.fromLTRB(leftPad, topPad, size.width - rightPad, topPad + chartHeight));

      canvas.drawPath(fillPath, fillPaint);
    }

    // Draw line stroke
    final linePaint = Paint()
      ..color = lineColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3.2
      ..strokeCap = StrokeCap.round;
    canvas.drawPath(animatedPath, linePaint);

    // Draw points & X-axis labels
    for (int i = 0; i < count; i++) {
      final double pointProgress = (i / (count - 1));
      if (progress >= pointProgress) {
        final p = points[i];
        final item = data[i];

        // Outer glow
        final glowPaint = Paint()
          ..color = lineColor.withValues(alpha: .25)
          ..style = PaintingStyle.fill;
        canvas.drawCircle(p, 9, glowPaint);

        // Inner circle
        final dotPaint = Paint()
          ..color = lineColor
          ..style = PaintingStyle.fill;
        canvas.drawCircle(p, 5, dotPaint);

        final whiteDotPaint = Paint()
          ..color = Colors.white
          ..style = PaintingStyle.fill;
        canvas.drawCircle(p, 2.5, whiteDotPaint);

        // Value label above point
        final valText = item["value"].toString();
        final valSpan = TextSpan(
          text: valText,
          style: GoogleFonts.poppins(
            color: lineColor,
            fontSize: 11,
            fontWeight: FontWeight.w700,
          ),
        );
        final valPainter = TextPainter(text: valSpan, textDirection: TextDirection.ltr);
        valPainter.layout();
        valPainter.paint(canvas, Offset(p.dx - valPainter.width / 2, p.dy - 22));

        // X-axis label below chart
        final monthStr = isMalayalam ? (item["month_ml"] as String) : (item["month_en"] as String);
        final monthSpan = TextSpan(
          text: monthStr,
          style: GoogleFonts.poppins(
            color: textColor,
            fontSize: 11,
            fontWeight: FontWeight.w600,
          ),
        );
        final monthPainter = TextPainter(text: monthSpan, textDirection: TextDirection.ltr);
        monthPainter.layout();
        monthPainter.paint(canvas, Offset(p.dx - monthPainter.width / 2, topPad + chartHeight + 10));
      }
    }
  }

  @override
  bool shouldRepaint(covariant _VitalChartPainter oldDelegate) {
    return oldDelegate.progress != progress ||
        oldDelegate.lineColor != lineColor ||
        oldDelegate.isMalayalam != isMalayalam;
  }
}
