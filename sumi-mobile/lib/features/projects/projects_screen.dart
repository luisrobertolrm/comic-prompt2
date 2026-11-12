import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme/app_theme.dart';
import '../../shared/empty_state.dart';
import '../../shared/error_retry.dart';
import '../../shared/filter_chips.dart';
import '../../shared/project_cover.dart';
import '../home/home_controller.dart';
import '../production/open_project.dart';
import 'project.dart';
import 'projects_repository.dart';

final projectsListProvider =
    FutureProvider.autoDispose<List<Project>>((ref) => ref.read(projectsRepositoryProvider).list());

class ProjectsScreen extends ConsumerStatefulWidget {
  const ProjectsScreen({super.key});

  @override
  ConsumerState<ProjectsScreen> createState() => _ProjectsScreenState();
}

class _ProjectsScreenState extends ConsumerState<ProjectsScreen> {
  String _status = 'Todos';
  bool _grid = true;

  @override
  Widget build(BuildContext context) {
    final data = ref.watch(projectsListProvider);

    return RefreshIndicator(
      onRefresh: () => ref.refresh(projectsListProvider.future),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Row(
            children: [
              const Expanded(
                child: PageTitle(eyebrow: 'PROJETOS', title: 'Todas as suas HQs.'),
              ),
              IconButton(
                tooltip: 'Alternar visualização',
                onPressed: () => setState(() => _grid = !_grid),
                icon: Icon(_grid ? Icons.view_list : Icons.grid_view),
              ),
            ],
          ),
          const SizedBox(height: 12),
          FilterChips(
            options: projectStatuses,
            selected: _status,
            onSelected: (s) => setState(() => _status = s),
          ),
          const SizedBox(height: 12),
          ...data.when(
            loading: () => [const Center(child: CircularProgressIndicator())],
            error: (e, _) =>
                [ErrorRetry(error: e, onRetry: () => ref.invalidate(projectsListProvider))],
            data: (all) {
              final projects = filterByStatus(all, _status);
              if (projects.isEmpty) {
                return [
                  EmptyState(
                    message: 'Nenhum projeto ainda.',
                    actionLabel: '+ Nova HQ',
                    onAction: () => startNewProject(context, ref),
                  ),
                ];
              }
              if (!_grid) {
                return [
                  for (final p in projects)
                    ProjectRow(project: p, onTap: () => openProject(context, ref, p)),
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
                    childAspectRatio: 0.68,
                  ),
                  itemCount: projects.length,
                  itemBuilder: (_, i) => ProjectCover(
                    project: projects[i],
                    onTap: () => openProject(context, ref, projects[i]),
                  ),
                ),
              ];
            },
          ),
          const SizedBox(height: 16),
          OutlinedButton.icon(
            onPressed: () => startNewProject(context, ref),
            icon: const Icon(Icons.add),
            label: const Text('Nova HQ'),
          ),
        ],
      ),
    );
  }
}
