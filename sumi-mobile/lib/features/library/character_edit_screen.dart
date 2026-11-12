import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/services/notification_service.dart';
import '../../shared/error_retry.dart';
import '../production/styles_repository.dart';
import 'character_form.dart';
import 'library_screen.dart';

/// Criar (`/library/new`) ou editar (`/library/:cid`) personagem fora da produção.
/// Sem projeto, o retrato usa o estilo e o modo de cor padrão do catálogo.
class CharacterEditScreen extends ConsumerWidget {
  final String? characterId;
  const CharacterEditScreen({super.key, this.characterId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final catalog = ref.watch(styleCatalogProvider);
    final characters = ref.watch(libraryCharactersProvider);

    return catalog.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => ErrorRetry(error: e, onRetry: () => ref.invalidate(styleCatalogProvider)),
      data: (styles) => characters.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) =>
            ErrorRetry(error: e, onRetry: () => ref.invalidate(libraryCharactersProvider)),
        data: (all) {
          final character =
              characterId == null ? null : all.where((c) => c.id == characterId).firstOrNull;
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Text(character == null ? 'Novo personagem' : 'Editar personagem',
                  style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 12),
              CharacterForm(
                character: character,
                style: character?.style.isNotEmpty == true ? character!.style : styles.defaultStyle,
                colorMode: styles.defaultColorMode,
                onSaved: (_) {
                  ref.read(notificationServiceProvider).success('Personagem salvo.');
                  context.pop();
                },
              ),
            ],
          );
        },
      ),
    );
  }
}
