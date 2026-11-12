import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_theme.dart';
import '../../shared/empty_state.dart';
import '../../shared/error_retry.dart';
import '../../shared/filter_chips.dart';
import '../../shared/project_cover.dart';
import '../library/character.dart';
import '../production/open_project.dart';
import 'home_controller.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  String _status = 'Todos';

  @override
  Widget build(BuildContext context) {
    final data = ref.watch(homeDataProvider);

    return RefreshIndicator(
      onRefresh: () => ref.refresh(homeDataProvider.future),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const PageTitle(
            eyebrow: 'SEUS PROJETOS',
            title: 'Onde sua próxima história começa.',
            lede: 'Continue um capítulo em andamento ou inicie uma nova HQ.',
          ),
          const SizedBox(height: 16),
          Align(
            alignment: Alignment.centerLeft,
            child: FilledButton.icon(
              onPressed: () => startNewProject(context, ref),
              icon: const Icon(Icons.add),
              label: const Text('Nova HQ'),
            ),
          ),
          const SizedBox(height: 16),
          FilterChips(
            options: projectStatuses,
            selected: _status,
            onSelected: (s) => setState(() => _status = s),
          ),
          const SizedBox(height: 16),
          ...data.when(
            loading: () => [const _Skeleton()],
            error: (e, _) => [ErrorRetry(error: e, onRetry: () => ref.invalidate(homeDataProvider))],
            data: (d) {
              final projects = filterByStatus(d.projects, _status);
              return [
                if (projects.isEmpty)
                  EmptyState(
                    message: 'Nenhum projeto ainda.',
                    actionLabel: 'Começar uma nova história',
                    onAction: () => startNewProject(context, ref),
                  )
                else
                  GridView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      mainAxisSpacing: 12,
                      crossAxisSpacing: 12,
                      childAspectRatio: 0.68,
                    ),
                    itemCount: projects.length,
                    itemBuilder: (_, i) => ProjectCover(
                      project: projects[i],
                      onTap: () => openProject(context, ref, projects[i]),
                    ),
                  ),
                const SizedBox(height: 28),
                const Eyebrow('BIBLIOTECA — PERSONAGENS RECENTES'),
                const SizedBox(height: 12),
                _RecentCharacters(d.recentCharacters),
              ];
            },
          ),
        ],
      ),
    );
  }
}

class _RecentCharacters extends StatelessWidget {
  final List<Character> characters;
  const _RecentCharacters(this.characters);

  @override
  Widget build(BuildContext context) => Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (characters.isEmpty)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 8),
              child: Text('Nenhum personagem ainda.', style: TextStyle(color: SumiColors.ink3)),
            ),
          for (final c in characters)
            ListTile(
              contentPadding: EdgeInsets.zero,
              leading: CircleAvatar(
                backgroundColor: SumiColors.accentSoft,
                foregroundColor: SumiColors.ink,
                child: Text(c.initial),
              ),
              title: Text(c.name),
              subtitle: Text(c.role, style: const TextStyle(color: SumiColors.ink3)),
            ),
          const SizedBox(height: 8),
          OutlinedButton.icon(
            onPressed: () => context.go('/library'),
            icon: const Icon(Icons.add),
            label: const Text('Ver biblioteca completa'),
          ),
        ],
      );
}

class _Skeleton extends StatelessWidget {
  const _Skeleton();

  @override
  Widget build(BuildContext context) => Row(
        children: [
          for (var i = 0; i < 2; i++)
            Expanded(
              child: Container(
                height: 220,
                margin: EdgeInsets.only(right: i == 0 ? 12 : 0),
                decoration: BoxDecoration(
                  color: SumiColors.paper2,
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
            ),
        ],
      );
}
