import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../core/theme/app_theme.dart';
import '../features/projects/project.dart';

String formatDate(DateTime d) => DateFormat("dd 'de' MMM 'de' y", 'pt_BR').format(d.toLocal());

class ProjectCover extends StatelessWidget {
  final Project project;
  final VoidCallback onTap;

  const ProjectCover({super.key, required this.project, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final soft = SumiColors.coverAccentSoft(project.coverAccent);
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: SumiColors.rule),
          boxShadow: const [BoxShadow(color: Color(0x141E1812), offset: Offset(2, 2))],
        ),
        clipBehavior: Clip.antiAlias,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Expanded(
              child: Container(
                color: soft,
                child: CustomPaint(
                  painter: _CoverPatternPainter(project.coverTone),
                  child: Padding(
                    padding: const EdgeInsets.all(10),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            _Tag(project.genre.toUpperCase()),
                            const Spacer(),
                            _Tag('${project.pages} pg'),
                          ],
                        ),
                        const Spacer(),
                        Text(project.title,
                            maxLines: 3,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                                fontFamily: serifFamily,
                                fontSize: 18,
                                fontWeight: FontWeight.w700,
                                height: 1.1)),
                      ],
                    ),
                  ),
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(10),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(project.subtitle,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 12, color: SumiColors.ink2)),
                  Text('${project.status} · ${formatDate(project.updatedAt)}',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 11, color: SumiColors.ink3)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class ProjectRow extends StatelessWidget {
  final Project project;
  final VoidCallback onTap;

  const ProjectRow({super.key, required this.project, required this.onTap});

  @override
  Widget build(BuildContext context) => ListTile(
        onTap: onTap,
        leading: Container(
          width: 40,
          height: 52,
          decoration: BoxDecoration(
            color: SumiColors.coverAccentSoft(project.coverAccent),
            borderRadius: BorderRadius.circular(4),
            border: Border.all(color: SumiColors.rule),
          ),
        ),
        title: Text(project.title, style: const TextStyle(fontWeight: FontWeight.w600)),
        subtitle: Text('${project.genre} · ${project.status} · ${formatDate(project.updatedAt)}',
            style: const TextStyle(fontSize: 12, color: SumiColors.ink3)),
        trailing: const Icon(Icons.chevron_right),
      );
}

class _Tag extends StatelessWidget {
  final String text;
  const _Tag(this.text);

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
        decoration: BoxDecoration(
          color: SumiColors.paper,
          borderRadius: BorderRadius.circular(3),
          border: Border.all(color: SumiColors.ink),
        ),
        child: Text(text, style: const TextStyle(fontFamily: monoFamily, fontSize: 9)),
      );
}

/// Equivalente a `coverPattern`/`coverBgSize` do home.component.ts.
class _CoverPatternPainter extends CustomPainter {
  final String tone;
  _CoverPatternPainter(this.tone);

  @override
  void paint(Canvas canvas, Size size) {
    if (tone == 'diag') {
      final paint = Paint()
        ..color = const Color(0x2E1E1812)
        ..strokeWidth = 1;
      for (double x = -size.height; x < size.width; x += 6) {
        canvas.drawLine(Offset(x, size.height), Offset(x + size.height, 0), paint);
      }
      return;
    }
    final dense = tone == 'dense';
    final step = dense ? 5.0 : 7.0;
    final paint = Paint()..color = dense ? const Color(0x381E1812) : const Color(0x2E1E1812);
    for (double y = step / 2; y < size.height; y += step) {
      for (double x = step / 2; x < size.width; x += step) {
        canvas.drawCircle(Offset(x, y), dense ? 0.7 : 0.6, paint);
      }
    }
  }

  @override
  bool shouldRepaint(_CoverPatternPainter old) => old.tone != tone;
}
