import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_theme.dart';
import '../../shared/empty_state.dart';
import '../../shared/error_retry.dart';
import '../../shared/filter_chips.dart';
import 'character.dart';
import 'character_card.dart';
import 'characters_repository.dart';

const roleFilters = ['Todos', 'Protagonistas', 'Coadjuvantes', 'Mascotes'];

final libraryCharactersProvider = FutureProvider.autoDispose<List<Character>>(
    (ref) => ref.read(charactersRepositoryProvider).list());

/// Mesmas regras de `matchesRole` em library.component.ts.
bool matchesRole(String role, String filter) {
  final r = role.toLowerCase();
  return switch (filter) {
    'Protagonistas' => r.contains('protagonista') || r.contains('heroi') || r.contains('herói'),
    'Coadjuvantes' => ['coadjuvante', 'interesse', 'mentor', 'rival'].any(r.contains),
    'Mascotes' => r.contains('mascote') || r.contains('animal'),
    _ => true,
  };
}

List<Character> filterCharacters(List<Character> all, String search, String role) {
  final q = search.trim().toLowerCase();
  return all
      .where((c) => (q.isEmpty || c.name.toLowerCase().contains(q)) && matchesRole(c.role, role))
      .toList();
}

class LibraryScreen extends ConsumerStatefulWidget {
  const LibraryScreen({super.key});

  @override
  ConsumerState<LibraryScreen> createState() => _LibraryScreenState();
}

class _LibraryScreenState extends ConsumerState<LibraryScreen> {
  String _search = '';
  String _role = 'Todos';

  Future<void> _open(String path) async {
    await context.push(path);
    ref.invalidate(libraryCharactersProvider);
  }

  @override
  Widget build(BuildContext context) {
    final data = ref.watch(libraryCharactersProvider);

    return RefreshIndicator(
      onRefresh: () => ref.refresh(libraryCharactersProvider.future),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const PageTitle(
            eyebrow: 'BIBLIOTECA',
            title: 'Personagens reutilizáveis.',
            lede: 'Cada personagem mantém ficha visual e personalidade. Aparecem em várias HQs '
                'sem perder coerência.',
          ),
          const SizedBox(height: 12),
          FilledButton.icon(
            onPressed: () => _open('/library/new'),
            icon: const Icon(Icons.add),
            label: const Text('Novo personagem'),
          ),
          const SizedBox(height: 12),
          TextField(
            decoration: const InputDecoration(
              prefixIcon: Icon(Icons.search),
              hintText: 'Buscar personagem…',
            ),
            onChanged: (v) => setState(() => _search = v),
          ),
          const SizedBox(height: 12),
          FilterChips(
            options: roleFilters,
            selected: _role,
            onSelected: (r) => setState(() => _role = r),
          ),
          const SizedBox(height: 12),
          ...data.when(
            loading: () => [const Center(child: CircularProgressIndicator())],
            error: (e, _) =>
                [ErrorRetry(error: e, onRetry: () => ref.invalidate(libraryCharactersProvider))],
            data: (all) {
              final chars = filterCharacters(all, _search, _role);
              if (chars.isEmpty) {
                return [
                  EmptyState(
                    message: 'Nenhum personagem encontrado.',
                    actionLabel: 'Criar o primeiro personagem',
                    onAction: () => _open('/library/new'),
                  ),
                ];
              }
              return [
                GridView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2,
                    mainAxisSpacing: 12,
                    crossAxisSpacing: 12,
                    childAspectRatio: 0.62,
                  ),
                  itemCount: chars.length,
                  itemBuilder: (_, i) => CharacterCard(
                    character: chars[i],
                    onTap: () => _open('/library/${chars[i].id}'),
                  ),
                ),
              ];
            },
          ),
        ],
      ),
    );
  }
}
