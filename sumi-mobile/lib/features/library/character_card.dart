import 'package:flutter/material.dart';

import '../../core/api/api_client.dart';
import '../../core/theme/app_theme.dart';
import 'character.dart';

const _palettes = ['blush', 'peach', 'mint', 'lilac', 'accent'];

/// Mesmo hash de `accentFor` em library.component.ts, para a cor bater com o web.
String accentOf(String name) {
  var h = 0;
  for (final c in name.codeUnits) {
    h = (h * 31 + c) & 0xFFFFFFFF;
  }
  return _palettes[h % _palettes.length];
}

/// Cartão de personagem da Biblioteca e da etapa Personagens.
class CharacterCard extends StatelessWidget {
  final Character character;
  final bool? selected;
  final VoidCallback onTap;
  final VoidCallback? onEdit;

  const CharacterCard({
    super.key,
    required this.character,
    required this.onTap,
    this.selected,
    this.onEdit,
  });

  @override
  Widget build(BuildContext context) {
    final c = character;
    final accent = accentOf(c.name);
    final meta = [
      if (c.age != null) '${c.age} anos',
      if (c.height != null && c.height!.isNotEmpty) c.height!,
    ].join(' · ');

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: selected == true ? SumiColors.ink : SumiColors.rule,
            width: selected == true ? 2 : 1,
          ),
        ),
        clipBehavior: Clip.antiAlias,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            AspectRatio(
              aspectRatio: 1,
              child: Stack(
                fit: StackFit.expand,
                children: [
                  if (c.imageUrl != null && c.imageUrl!.isNotEmpty)
                    Image.network(fileUrl(c.imageUrl), fit: BoxFit.cover)
                  else
                    Container(
                      color: SumiColors.coverAccentSoft(accent),
                      alignment: Alignment.center,
                      child: CircleAvatar(
                        radius: 28,
                        backgroundColor: SumiColors.coverAccent(accent),
                        foregroundColor: SumiColors.ink,
                        child: Text(c.initial, style: const TextStyle(fontSize: 22)),
                      ),
                    ),
                  Positioned(
                    left: 6,
                    bottom: 6,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      color: SumiColors.paper,
                      child: Text(c.role.toUpperCase(),
                          style: const TextStyle(fontFamily: monoFamily, fontSize: 9)),
                    ),
                  ),
                  if (selected != null)
                    Positioned(
                      top: 6,
                      right: 6,
                      child: CircleAvatar(
                        radius: 12,
                        backgroundColor: selected! ? SumiColors.ink : Colors.white70,
                        child: selected!
                            ? const Icon(Icons.check, size: 14, color: SumiColors.paper)
                            : null,
                      ),
                    ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(c.name,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(fontWeight: FontWeight.w600)),
                      ),
                      if (onEdit != null)
                        InkWell(
                          onTap: onEdit,
                          child: const Padding(
                            padding: EdgeInsets.all(2),
                            child: Icon(Icons.edit_outlined, size: 16),
                          ),
                        ),
                    ],
                  ),
                  if (meta.isNotEmpty)
                    Text(meta, style: const TextStyle(fontSize: 11, color: SumiColors.ink3)),
                  if (c.summary != null && c.summary!.isNotEmpty)
                    Text(c.summary!,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontSize: 11, color: SumiColors.ink2)),
                  if (c.traits.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(top: 4),
                      child: Text(c.traits.take(3).join(' · '),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(fontSize: 10, color: SumiColors.ink3)),
                    ),
                  if (!c.approved)
                    const Padding(
                      padding: EdgeInsets.only(top: 4),
                      child: Text('RASCUNHO',
                          style: TextStyle(
                              fontFamily: monoFamily, fontSize: 9, color: SumiColors.accentInk)),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
