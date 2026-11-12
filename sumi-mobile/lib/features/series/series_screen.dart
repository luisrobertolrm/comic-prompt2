import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme/app_theme.dart';
import '../../shared/empty_state.dart';
import '../../shared/error_retry.dart';
import '../projects/project.dart';
import '../projects/projects_repository.dart';
import 'series.dart';
import 'series_repository.dart';

class SeriesData {
  final List<Series> series;
  final List<Project> projects;
  const SeriesData(this.series, this.projects);

  String projectTitle(String id) =>
      projects.where((p) => p.id == id).map((p) => p.title).firstOrNull ?? '—';
}

final seriesDataProvider = FutureProvider.autoDispose<SeriesData>((ref) async {
  final results = await Future.wait([
    ref.read(seriesRepositoryProvider).list(),
    ref.read(projectsRepositoryProvider).list(),
  ]);
  return SeriesData(results[0] as List<Series>, results[1] as List<Project>);
});

class SeriesScreen extends ConsumerWidget {
  const SeriesScreen({super.key});

  Future<void> _openForm(BuildContext context, WidgetRef ref, List<Project> projects,
      {Series? series}) async {
    final saved = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (_) => _SeriesForm(series: series, projects: projects),
    );
    if (saved == true) ref.invalidate(seriesDataProvider);
  }

  Future<void> _remove(BuildContext context, WidgetRef ref, Series s) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Excluir a série "${s.name}"?'),
        content: const Text('Os projetos continuam existindo.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancelar')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Excluir')),
        ],
      ),
    );
    if (ok != true) return;
    await ref.read(seriesRepositoryProvider).delete(s.id);
    ref.invalidate(seriesDataProvider);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final data = ref.watch(seriesDataProvider);

    return RefreshIndicator(
      onRefresh: () => ref.refresh(seriesDataProvider.future),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const PageTitle(
            eyebrow: 'SUAS SÉRIES',
            title: 'Agrupe seus projetos em séries.',
            lede: 'Uma série reúne HQs relacionadas — uma temporada, uma saga ou uma coleção.',
          ),
          const SizedBox(height: 12),
          ...data.when(
            loading: () => [const Center(child: CircularProgressIndicator())],
            error: (e, _) => [ErrorRetry(error: e, onRetry: () => ref.invalidate(seriesDataProvider))],
            data: (d) => [
              FilledButton.icon(
                onPressed: () => _openForm(context, ref, d.projects),
                icon: const Icon(Icons.add),
                label: const Text('Nova série'),
              ),
              const SizedBox(height: 12),
              if (d.series.isEmpty) const EmptyState(message: 'Nenhuma série ainda. Crie a primeira.'),
              for (final s in d.series)
                Card(
                  margin: const EdgeInsets.only(bottom: 10),
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(s.name,
                            style: const TextStyle(
                                fontFamily: serifFamily, fontSize: 18, fontWeight: FontWeight.w700)),
                        if (s.description != null && s.description!.isNotEmpty)
                          Text(s.description!, style: const TextStyle(color: SumiColors.ink2)),
                        const SizedBox(height: 6),
                        Text(
                          s.projectIds.isEmpty
                              ? 'Sem projetos vinculados'
                              : '${s.projectIds.length} projeto(s): ${s.projectIds.map(d.projectTitle).join(', ')}',
                          style: const TextStyle(fontSize: 12, color: SumiColors.ink3),
                        ),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.end,
                          children: [
                            TextButton(
                                onPressed: () => _openForm(context, ref, d.projects, series: s),
                                child: const Text('Editar')),
                            TextButton(
                              onPressed: () => _remove(context, ref, s),
                              child: const Text('Excluir', style: TextStyle(color: SumiColors.danger)),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
            ],
          ),
        ],
      ),
    );
  }
}

class _SeriesForm extends ConsumerStatefulWidget {
  final Series? series;
  final List<Project> projects;
  const _SeriesForm({required this.series, required this.projects});

  @override
  ConsumerState<_SeriesForm> createState() => _SeriesFormState();
}

class _SeriesFormState extends ConsumerState<_SeriesForm> {
  late final _name = TextEditingController(text: widget.series?.name ?? '');
  late final _description = TextEditingController(text: widget.series?.description ?? '');
  late final Set<String> _selected = {...?widget.series?.projectIds};
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _name.addListener(() => setState(() {}));
  }

  @override
  void dispose() {
    _name.dispose();
    _description.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    final repo = ref.read(seriesRepositoryProvider);
    final name = _name.text.trim();
    final description = _description.text.trim().isEmpty ? null : _description.text.trim();
    try {
      final saved = widget.series == null
          ? await repo.create(name, description)
          : await repo.update(widget.series!.id, name, description);
      await repo.setProjects(saved.id, _selected.toList());
      if (mounted) Navigator.of(context).pop(true);
    } catch (_) {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) => Padding(
        padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(widget.series == null ? 'Nova série' : 'Editar série',
                  style: const TextStyle(fontFamily: serifFamily, fontSize: 20, fontWeight: FontWeight.w700)),
              const SizedBox(height: 12),
              TextField(
                controller: _name,
                decoration: const InputDecoration(labelText: 'Nome', hintText: 'Ex: Crônicas de Outono'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _description,
                minLines: 2,
                maxLines: 5,
                decoration: const InputDecoration(
                    labelText: 'Descrição', hintText: 'Do que se trata esta série?'),
              ),
              const SizedBox(height: 16),
              const Eyebrow('PROJETOS DA SÉRIE'),
              if (widget.projects.isEmpty)
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 8),
                  child: Text('Nenhum projeto disponível.'),
                ),
              for (final p in widget.projects)
                CheckboxListTile(
                  contentPadding: EdgeInsets.zero,
                  value: _selected.contains(p.id),
                  title: Text(p.title),
                  subtitle: Text(p.genre),
                  onChanged: (_) => setState(() {
                    if (!_selected.remove(p.id)) _selected.add(p.id);
                  }),
                ),
              const SizedBox(height: 12),
              FilledButton(
                onPressed: _name.text.trim().isEmpty || _saving ? null : _save,
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  child: Text(_saving ? 'Salvando…' : 'Salvar'),
                ),
              ),
            ],
          ),
        ),
      );
}
