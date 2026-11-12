import 'package:flutter/material.dart';

import '../../core/api/api_client.dart';
import '../../core/theme/app_theme.dart';
import 'jobs.dart';

/// Grade de imagens geradas pela IA (retratos ou cenários); toque para escolher.
class CandidatePicker extends StatelessWidget {
  final String title;
  final List<ImageCandidate> candidates;
  final String? pickedId;
  final ValueChanged<String?> onPick;

  const CandidatePicker({
    super.key,
    required this.title,
    required this.candidates,
    required this.pickedId,
    required this.onPick,
  });

  @override
  Widget build(BuildContext context) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Eyebrow(title),
          const SizedBox(height: 8),
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            mainAxisSpacing: 8,
            crossAxisSpacing: 8,
            children: [
              for (final c in candidates)
                GestureDetector(
                  onTap: () => onPick(pickedId == c.id ? null : c.id),
                  child: Stack(
                    fit: StackFit.expand,
                    children: [
                      Container(
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(
                            color: pickedId == c.id ? SumiColors.ink : SumiColors.rule,
                            width: pickedId == c.id ? 3 : 1,
                          ),
                        ),
                        clipBehavior: Clip.antiAlias,
                        child: Image.network(fileUrl(c.url), fit: BoxFit.cover),
                      ),
                      if (pickedId == c.id)
                        const Positioned(
                          top: 6,
                          right: 6,
                          child: CircleAvatar(
                            radius: 12,
                            backgroundColor: SumiColors.ink,
                            child: Icon(Icons.check, size: 14, color: SumiColors.paper),
                          ),
                        ),
                    ],
                  ),
                ),
            ],
          ),
        ],
      );
}

/// Indicador de geração em andamento (FR-007a: o trabalho continua no servidor).
class GeneratingNotice extends StatelessWidget {
  final String message;
  final int? progress;
  const GeneratingNotice(this.message, {super.key, this.progress});

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: SumiColors.accentSoft,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: SumiColors.accent),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const SizedBox(
                    width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)),
                const SizedBox(width: 10),
                Expanded(child: Text(message)),
              ],
            ),
            const SizedBox(height: 8),
            LinearProgressIndicator(value: progress == null ? null : progress! / 100),
            const SizedBox(height: 6),
            const Text(
              'Pode sair desta tela ou minimizar o app: a geração continua no servidor.',
              style: TextStyle(fontSize: 11, color: SumiColors.ink3),
            ),
          ],
        ),
      );
}
