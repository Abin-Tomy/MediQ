import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../../core/theme/app_theme_provider.dart';
import '../../../../models/body_area.dart';

class AnatomicalBodyDiagram extends StatefulWidget {
  final BodyArea? selectedArea;
  final ValueChanged<BodyArea> onAreaSelected;

  const AnatomicalBodyDiagram({
    super.key,
    required this.selectedArea,
    required this.onAreaSelected,
  });

  @override
  State<AnatomicalBodyDiagram> createState() => _AnatomicalBodyDiagramState();
}

class _AnatomicalBodyDiagramState extends State<AnatomicalBodyDiagram>
    with SingleTickerProviderStateMixin {
  late AnimationController _glowController;
  late Animation<double> _glowAnimation;

  @override
  void initState() {
    super.initState();
    _glowController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat(reverse: true);

    _glowAnimation = Tween<double>(begin: 0.5, end: 1.0).animate(
      CurvedAnimation(parent: _glowController, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _glowController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: Listenable.merge([AppThemeProvider(), _glowAnimation]),
      builder: (context, _) {
        final theme = AppThemeProvider();

        return Container(
          height: 280,
          width: double.infinity,
          decoration: BoxDecoration(
            color: theme.isDark || theme.isMonsoon
                ? const Color(0xFF1E293B).withValues(alpha: .4)
                : const Color(0xFFEFF6FF),
            borderRadius: BorderRadius.circular(28),
            border: Border.all(
              color: theme.primaryAccent.withValues(alpha: .3),
              width: 1.5,
            ),
          ),
          child: Stack(
            alignment: Alignment.center,
            children: [
              // BACKGROUND ANATOMICAL SILHOUETTE PAINTER
              CustomPaint(
                size: const Size(160, 240),
                painter: _HumanSilhouettePainter(
                  accentColor: theme.primaryAccent,
                  isDark: theme.isDark || theme.isMonsoon,
                ),
              ),

              // INTERACTIVE HOTSPOTS
              _buildHotspot(
                context: context,
                areaName: 'Head',
                alignment: const Alignment(0.0, -0.72),
                label: theme.tr("Head", "തല"),
                theme: theme,
              ),
              _buildHotspot(
                context: context,
                areaName: 'Chest',
                alignment: const Alignment(0.0, -0.32),
                label: theme.tr("Chest", "നെഞ്ച്"),
                theme: theme,
              ),
              _buildHotspot(
                context: context,
                areaName: 'Abdomen',
                alignment: const Alignment(0.0, 0.05),
                label: theme.tr("Abdomen", "വയർ"),
                theme: theme,
              ),
              _buildHotspot(
                context: context,
                areaName: 'Arms',
                alignment: const Alignment(-0.55, -0.15),
                label: theme.tr("Arms", "കൈകൾ"),
                theme: theme,
              ),
              _buildHotspot(
                context: context,
                areaName: 'Legs',
                alignment: const Alignment(0.22, 0.55),
                label: theme.tr("Legs", "കാലുകൾ"),
                theme: theme,
              ),
              _buildHotspot(
                context: context,
                areaName: 'Skin',
                alignment: const Alignment(0.55, -0.15),
                label: theme.tr("Skin", "ചർമ്മം"),
                theme: theme,
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildHotspot({
    required BuildContext context,
    required String areaName,
    required Alignment alignment,
    required String label,
    required AppThemeProvider theme,
  }) {
    final area = BodyArea.items.firstWhere(
      (item) => item.name.toLowerCase() == areaName.toLowerCase(),
      orElse: () => BodyArea.items.first,
    );
    final isSelected = widget.selectedArea?.name.toLowerCase() == areaName.toLowerCase();

    return Align(
      alignment: alignment,
      child: GestureDetector(
        onTap: () => widget.onAreaSelected(area),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 300),
          padding: EdgeInsets.symmetric(
            horizontal: isSelected ? 12 : 8,
            vertical: isSelected ? 6 : 4,
          ),
          decoration: BoxDecoration(
            color: isSelected
                ? theme.primaryAccent
                : (theme.isDark || theme.isMonsoon
                    ? const Color(0xFF0F172A).withValues(alpha: .8)
                    : Colors.white.withValues(alpha: .9)),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: isSelected ? Colors.white : theme.primaryAccent,
              width: isSelected ? 2 : 1.2,
            ),
            boxShadow: isSelected
                ? [
                    BoxShadow(
                      color: theme.primaryAccent.withValues(alpha: _glowAnimation.value * 0.6),
                      blurRadius: 16,
                      spreadRadius: 4,
                    )
                  ]
                : [
                    const BoxShadow(
                      color: Colors.black12,
                      blurRadius: 4,
                      offset: Offset(0, 2),
                    ),
                  ],
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 8,
                height: 8,
                decoration: BoxDecoration(
                  color: isSelected ? Colors.white : theme.primaryAccent,
                  shape: BoxShape.circle,
                ),
              ),
              const SizedBox(width: 5),
              Text(
                label,
                style: GoogleFonts.poppins(
                  fontSize: 11,
                  fontWeight: isSelected ? FontWeight.w700 : FontWeight.w600,
                  color: isSelected
                      ? Colors.white
                      : (theme.isDark || theme.isMonsoon
                          ? Colors.white
                          : const Color(0xFF1E293B)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _HumanSilhouettePainter extends CustomPainter {
  final Color accentColor;
  final bool isDark;

  _HumanSilhouettePainter({required this.accentColor, required this.isDark});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = isDark
          ? const Color(0xFF334155).withValues(alpha: .5)
          : const Color(0xFFCBD5E1).withValues(alpha: .7)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.5
      ..strokeCap = StrokeCap.round;

    final fillPaint = Paint()
      ..color = isDark
          ? const Color(0xFF1E293B).withValues(alpha: .3)
          : const Color(0xFFF1F5F9).withValues(alpha: .5)
      ..style = PaintingStyle.fill;

    final centerX = size.width / 2;

    // Head
    canvas.drawCircle(Offset(centerX, size.height * 0.12), 22, fillPaint);
    canvas.drawCircle(Offset(centerX, size.height * 0.12), 22, paint);

    // Torso / Chest / Abdomen
    final torsoPath = Path()
      ..moveTo(centerX - 35, size.height * 0.25)
      ..lineTo(centerX + 35, size.height * 0.25)
      ..lineTo(centerX + 28, size.height * 0.60)
      ..lineTo(centerX - 28, size.height * 0.60)
      ..close();
    canvas.drawPath(torsoPath, fillPaint);
    canvas.drawPath(torsoPath, paint);

    // Arms
    canvas.drawLine(
      Offset(centerX - 35, size.height * 0.26),
      Offset(centerX - 60, size.height * 0.50),
      paint,
    );
    canvas.drawLine(
      Offset(centerX + 35, size.height * 0.26),
      Offset(centerX + 60, size.height * 0.50),
      paint,
    );

    // Legs
    canvas.drawLine(
      Offset(centerX - 16, size.height * 0.60),
      Offset(centerX - 24, size.height * 0.95),
      paint,
    );
    canvas.drawLine(
      Offset(centerX + 16, size.height * 0.60),
      Offset(centerX + 24, size.height * 0.95),
      paint,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
