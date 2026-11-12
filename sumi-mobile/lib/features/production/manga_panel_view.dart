import 'package:flutter/material.dart';

import '../../core/api/api_client.dart';
import '../../core/theme/app_theme.dart';
import 'panel.dart';

double aspectRatioOf(String aspect) => switch (aspect) {
      '3-4' => 3 / 4,
      '16-9' => 16 / 9,
      '1-1' => 1,
      _ => 4 / 3,
    };

/// Quadro com imagem e balões (equivalente ao manga-panel.component do web).
/// Com [onBubbleMoved], os balões podem ser arrastados; [onBubbleDropped] salva ao soltar.
class MangaPanelView extends StatelessWidget {
  final Panel panel;
  final bool loading;
  /// `true` ocupa todo o espaço do pai (slot do Editor) em vez de usar a proporção do quadro.
  final bool fill;
  final void Function(int index, int x, int y)? onBubbleMoved;
  final void Function(int index)? onBubbleDropped;

  const MangaPanelView({
    super.key,
    required this.panel,
    this.loading = false,
    this.fill = false,
    this.onBubbleMoved,
    this.onBubbleDropped,
  });

  @override
  Widget build(BuildContext context) {
    final content = _content();
    return fill ? content : AspectRatio(aspectRatio: aspectRatioOf(panel.aspect), child: content);
  }

  Widget _content() => LayoutBuilder(
          builder: (context, box) => Container(
            decoration: BoxDecoration(
              color: SumiColors.paper2,
              border: Border.all(color: SumiColors.ink, width: 2),
            ),
            clipBehavior: Clip.hardEdge,
            child: Stack(
              fit: StackFit.expand,
              children: [
                if (panel.hasImage)
                  Image.network(fileUrl(panel.imageUrl), fit: BoxFit.cover)
                else
                  Center(
                    child: Text(
                      panel.characterName?.substring(0, 1).toUpperCase() ?? '?',
                      style: const TextStyle(fontSize: 40, color: SumiColors.ink4),
                    ),
                  ),
                if (loading)
                  Container(
                    color: Colors.white54,
                    alignment: Alignment.center,
                    child: const CircularProgressIndicator(),
                  ),
                for (var i = 0; i < panel.bubbles.length; i++) _bubble(i, box.biggest),
              ],
            ),
          ),
      );

  Widget _bubble(int i, Size size) {
    final b = panel.bubbles[i];
    final right = b.side == 'right';
    final child = GestureDetector(
      onPanUpdate: onBubbleMoved == null
          ? null
          : (d) {
              final dx = d.delta.dx / size.width * 100;
              final x = (b.x + (right ? -dx : dx)).clamp(0, 80).round();
              final y = (b.y + d.delta.dy / size.height * 100).clamp(0, 78).round();
              onBubbleMoved!(i, x, y);
            },
      onPanEnd: onBubbleDropped == null ? null : (_) => onBubbleDropped!(i),
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: size.width * 0.58),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: _decoration(b.kind),
          child: Text(
            b.text,
            style: TextStyle(
              fontSize: 11,
              height: 1.25,
              fontStyle: b.kind == 'whisper' || b.kind == 'thought' ? FontStyle.italic : null,
              fontWeight: b.kind == 'shout' ? FontWeight.w800 : null,
              color: SumiColors.ink,
            ),
          ),
        ),
      ),
    );
    return Positioned(
      top: size.height * b.y / 100,
      left: right ? null : size.width * b.x / 100,
      right: right ? size.width * b.x / 100 : null,
      child: child,
    );
  }

  BoxDecoration _decoration(String kind) => switch (kind) {
        'narration' => BoxDecoration(
            color: SumiColors.accentSoft,
            border: Border.all(color: SumiColors.ink, width: 1.5),
          ),
        'shout' => BoxDecoration(
            color: Colors.white,
            border: Border.all(color: SumiColors.ink, width: 2.5),
            borderRadius: BorderRadius.circular(4),
          ),
        'thought' => BoxDecoration(
            color: SumiColors.paper,
            border: Border.all(color: SumiColors.ink, width: 1.5),
            borderRadius: BorderRadius.circular(20),
          ),
        'whisper' => BoxDecoration(
            color: SumiColors.paper,
            border: Border.all(color: SumiColors.ink3, width: 1),
            borderRadius: BorderRadius.circular(12),
          ),
        _ => BoxDecoration(
            color: SumiColors.paper,
            border: Border.all(color: SumiColors.ink, width: 1.5),
            borderRadius: BorderRadius.circular(12),
          ),
      };
}
