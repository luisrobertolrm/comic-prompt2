import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/services/file_share_service.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/error_retry.dart';
import '../../projects/project.dart';
import '../../projects/projects_repository.dart';
import '../manga_panel_view.dart';
import '../panel.dart';
import '../panels_repository.dart';
import '../production_draft.dart';
import '../production_step.dart';
import '../step_action_bar.dart';
import '../styles_repository.dart';

class FinalizeScreen extends ConsumerStatefulWidget {
  final String projectId;
  const FinalizeScreen({super.key, required this.projectId});

  @override
  ConsumerState<FinalizeScreen> createState() => _FinalizeScreenState();
}

class _FinalizeScreenState extends ConsumerState<FinalizeScreen> {
  Project? _project;
  List<Panel> _panels = [];
  Object? _error;
  bool _loading = true;
  bool _exporting = false;
  bool _togglingPublic = false;

  bool get _isPublic => _project?.status == 'Público';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final project = await ref.read(projectsRepositoryProvider).get(widget.projectId);
      final panels = await ref.read(panelsRepositoryProvider).list(widget.projectId);
      ref.read(productionDraftProvider.notifier).setTitle(project.title);
      setState(() {
        _project = project;
        _panels = panels;
      });
    } catch (e) {
      setState(() => _error = e);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _export() async {
    setState(() => _exporting = true);
    try {
      final bytes = await ref.read(projectsRepositoryProvider).exportPanelsZip(widget.projectId);
      final name = (_project?.title ?? 'hq').replaceAll(RegExp(r'[^\w\- ]'), '').trim();
      await ref
          .read(fileShareServiceProvider)
          .shareBytes(bytes, '${name.isEmpty ? 'hq' : name}.zip', 'application/zip');
    } catch (_) {
    } finally {
      if (mounted) setState(() => _exporting = false);
    }
  }

  Future<void> _togglePublic() async {
    setState(() => _togglingPublic = true);
    try {
      final updated = await ref
          .read(projectsRepositoryProvider)
          .update(widget.projectId, {'status': _isPublic ? 'Rascunho' : 'Público'});
      final detail = await ref.read(projectsRepositoryProvider).get(updated.id);
      if (mounted) setState(() => _project = detail);
    } catch (_) {
    } finally {
      if (mounted) setState(() => _togglingPublic = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) return ErrorRetry(error: _error!, onRetry: _load);
    final project = _project!;
    final styleLabel = ref
            .watch(styleCatalogProvider)
            .valueOrNull
            ?.styles
            .where((s) => s.id == project.style)
            .map((s) => s.label)
            .firstOrNull ??
        '—';
    final approved = _panels.where((p) => p.status == 'approved').length;
    final pages = <List<Panel>>[
      for (var i = 0; i < _panels.length; i += 4) _panels.skip(i).take(4).toList(),
    ];

    return Column(
      children: [
        Expanded(
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              const PageTitle(
                eyebrow: 'ETAPA 5 DE 5',
                title: 'Pronto para o leitor.',
                lede: 'Visualize a HQ completa, exporte ou compartilhe.',
              ),
              const SizedBox(height: 16),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Eyebrow('RESUMO'),
                      const SizedBox(height: 8),
                      _row('Quadros', '${_panels.length}'),
                      _row('Aprovados', '$approved'),
                      _row('Páginas', '${pages.length}'),
                      _row('Personagens', '${project.characters.length}'),
                      _row('Estilo', styleLabel),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 12),
              const Eyebrow('EXPORTAR'),
              const SizedBox(height: 8),
              FilledButton.icon(
                onPressed: _exporting ? null : _export,
                icon: const Icon(Icons.ios_share),
                label: Text(_exporting ? 'Preparando ZIP…' : 'Salvar ou compartilhar quadros (.zip)'),
              ),
              const SizedBox(height: 8),
              OutlinedButton.icon(
                onPressed: () => context.go(ProductionStep.video.location(widget.projectId)),
                icon: const Icon(Icons.play_arrow),
                label: const Text('Gerar vídeo narrado'),
              ),
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                value: _isPublic,
                onChanged: _togglingPublic ? null : (_) => _togglePublic(),
                title: const Text('Publicar na galeria'),
                subtitle: const Text('Visível na galeria pública para qualquer visitante.'),
              ),
              const SizedBox(height: 12),
              for (var i = 0; i < pages.length; i++) ...[
                Eyebrow('PÁGINA ${i + 1}'),
                const SizedBox(height: 6),
                for (final p in pages[i])
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: MangaPanelView(panel: p),
                  ),
                const SizedBox(height: 12),
              ],
              const Text('Sua HQ está pronta. Você pode voltar a qualquer etapa — o progresso fica salvo.',
                  textAlign: TextAlign.center, style: TextStyle(color: SumiColors.ink3)),
            ],
          ),
        ),
        StepActionBar(
          loading: false,
          enabled: true,
          label: 'Concluir',
          onPressed: () => context.go('/'),
          secondaryLabel: 'Editor',
          onSecondary: () => context.go(ProductionStep.editor.location(widget.projectId)),
        ),
      ],
    );
  }

  Widget _row(String label, String value) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 2),
        child: Row(
          children: [
            Text(label, style: const TextStyle(color: SumiColors.ink3)),
            const Spacer(),
            Text(value, style: const TextStyle(fontWeight: FontWeight.w600)),
          ],
        ),
      );
}
