import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/api/api_client.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/error_retry.dart';
import '../../projects/project.dart';
import '../../projects/projects_repository.dart';
import '../candidate_picker.dart';
import '../panel.dart';
import '../panels_repository.dart';
import '../poll_job.dart';
import '../production_draft.dart';
import '../production_step.dart';
import '../run_limited.dart';
import '../step_action_bar.dart';
import '../../../shared/dictation_button.dart';

class ScriptScreen extends ConsumerStatefulWidget {
  final String projectId;
  const ScriptScreen({super.key, required this.projectId});

  @override
  ConsumerState<ScriptScreen> createState() => _ScriptScreenState();
}

class _ScriptScreenState extends ConsumerState<ScriptScreen> {
  Project? _project;
  List<Panel> _panels = [];
  Object? _error;
  bool _loading = true;
  bool _generatingSlots = false;
  bool _generatingSynopsis = false;
  final Set<String> _contentInProgress = {};
  final Set<String> _imageInProgress = {};
  int _imagesTotal = 0;
  int _imagesDone = 0;
  int _targetPanels = 12;
  late final ResumeListener _resume;

  PanelsRepository get _panelsRepo => ref.read(panelsRepositoryProvider);
  ProjectsRepository get _projectsRepo => ref.read(projectsRepositoryProvider);

  @override
  void initState() {
    super.initState();
    _resume = ResumeListener(_reloadPanels);
    _load();
  }

  @override
  void dispose() {
    _resume.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final project = await _projectsRepo.get(widget.projectId);
      final panels = await _panelsRepo.list(widget.projectId);
      ref.read(productionDraftProvider.notifier).setTitle(project.title);
      setState(() {
        _project = project;
        _panels = panels;
        _targetPanels = panels.isNotEmpty ? panels.length : (project.pages * 3).clamp(5, 30);
      });
    } catch (e) {
      setState(() => _error = e);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _reloadPanels() async {
    try {
      final panels = await _panelsRepo.list(widget.projectId);
      if (mounted) setState(() => _panels = panels);
    } catch (_) {}
  }

  void _replace(Panel updated) {
    if (!mounted) return;
    setState(() => _panels = [for (final p in _panels) p.id == updated.id ? updated : p]);
  }

  String get _synopsisText {
    final p = _project;
    if (p == null) return '';
    if (p.synopsis?.isNotEmpty ?? false) return p.synopsis!;
    if (p.premise?.isNotEmpty ?? false) return p.premise!;
    return p.title;
  }

  Future<void> _regenSynopsis() async {
    setState(() => _generatingSynopsis = true);
    try {
      final p = await _projectsRepo.generateSynopsis(widget.projectId);
      if (mounted) setState(() => _project = p);
    } catch (_) {
    } finally {
      if (mounted) setState(() => _generatingSynopsis = false);
    }
  }

  Future<void> _editSynopsis() async {
    final controller = TextEditingController(text: _synopsisText);
    final text = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Sinopse'),
        content: TextField(
          controller: controller,
          minLines: 6,
          maxLines: 14,
          decoration: InputDecoration(suffixIcon: DictationButton(controller: controller)),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')),
          FilledButton(
              onPressed: () => Navigator.pop(context, controller.text), child: const Text('Salvar')),
        ],
      ),
    );
    if (text == null || text.trim().isEmpty) return;
    await _projectsRepo.update(widget.projectId, {'synopsis': text.trim()});
    final project = await _projectsRepo.get(widget.projectId);
    if (mounted) setState(() => _project = project);
  }

  /// Passo 1: quadros vazios; passo 2: conteúdo de cada quadro, 3 por vez.
  Future<void> _generatePanels() async {
    if (_panels.isNotEmpty && !await _confirm('Gerar de novo?', 'Os quadros atuais serão substituídos.')) {
      return;
    }
    setState(() {
      _generatingSlots = true;
      _panels = [];
    });
    try {
      final slots = await _panelsRepo.generateAll(widget.projectId, targetPanels: _targetPanels);
      ref.invalidate(furthestStepProvider(widget.projectId));
      if (!mounted) return;
      setState(() {
        _panels = slots;
        _targetPanels = slots.length;
        _generatingSlots = false;
        _contentInProgress.addAll(slots.map((p) => p.id));
      });
      await runLimited(slots, 3, (panel) async {
        try {
          _replace(await _panelsRepo.generateContent(panel.id));
        } finally {
          if (mounted) setState(() => _contentInProgress.remove(panel.id));
        }
      });
    } catch (_) {
      if (mounted) setState(() => _generatingSlots = false);
    }
  }

  Future<void> _generateContent(Panel panel) async {
    setState(() => _contentInProgress.add(panel.id));
    try {
      _replace(await _panelsRepo.generateContent(panel.id));
    } catch (_) {
    } finally {
      if (mounted) setState(() => _contentInProgress.remove(panel.id));
    }
  }

  Future<void> _generateAllImages() async {
    final panels = List<Panel>.from(_panels);
    setState(() {
      _imagesTotal = panels.length;
      _imagesDone = 0;
      _imageInProgress.addAll(panels.map((p) => p.id));
    });
    await runLimited(panels, 3, (panel) async {
      try {
        _replace(await _panelsRepo.generateImage(panel.id));
      } finally {
        if (mounted) {
          setState(() {
            _imagesDone++;
            _imageInProgress.remove(panel.id);
          });
        }
      }
    });
    ref.invalidate(furthestStepProvider(widget.projectId));
  }

  Future<void> _insertAfter(int afterIndexOrder) async {
    await _panelsRepo.insert(widget.projectId, afterIndexOrder);
    await _reloadPanels();
  }

  Future<void> _delete(Panel panel) async {
    if (_panels.length <= 1) return;
    await _panelsRepo.delete(panel.id);
    await _reloadPanels();
  }

  Future<void> _deleteAll() async {
    if (!await _confirm('Apagar todos os quadros?', 'Esta ação não pode ser desfeita.')) return;
    await _panelsRepo.deleteMany(widget.projectId, _panels.map((p) => p.id).toList());
    ref.invalidate(furthestStepProvider(widget.projectId));
    await _reloadPanels();
  }

  Future<void> _reorder(int oldIndex, int newIndex) async {
    if (newIndex > oldIndex) newIndex--;
    final list = List<Panel>.from(_panels);
    list.insert(newIndex, list.removeAt(oldIndex));
    setState(() => _panels = list);
    await _panelsRepo.reorder(widget.projectId, list.map((p) => p.id).toList());
    await _reloadPanels();
  }

  Future<void> _edit(Panel panel) async {
    final updated = await showModalBottomSheet<Map<String, dynamic>>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (_) => SafeArea(top: false, child: _PanelEditSheet(panel: panel, cast: _project?.characters.map((c) => c.name).toList() ?? [])),
    );
    if (updated == null) return;
    _replace(await _panelsRepo.update(panel.id, updated));
  }

  Future<bool> _confirm(String title, String message) async =>
      await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: Text(title),
          content: Text(message),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancelar')),
            FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Confirmar')),
          ],
        ),
      ) ??
      false;

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) return ErrorRetry(error: _error!, onRetry: _load);
    final busyImages = _imageInProgress.isNotEmpty;

    return Column(
      children: [
        Expanded(
          child: RefreshIndicator(
            onRefresh: _reloadPanels,
            child: ReorderableListView.builder(
              padding: const EdgeInsets.all(16),
              buildDefaultDragHandles: false,
              header: _header(busyImages),
              itemCount: _panels.length,
              onReorder: _reorder,
              itemBuilder: (_, i) {
                final p = _panels[i];
                return _PanelCard(
                  key: ValueKey(p.id),
                  index: i,
                  panel: p,
                  generatingContent: _contentInProgress.contains(p.id),
                  generatingImage: _imageInProgress.contains(p.id),
                  onEdit: () => _edit(p),
                  onGenerateContent: () => _generateContent(p),
                  onInsertAfter: () => _insertAfter(p.indexOrder),
                  onDelete: _panels.length > 1 ? () => _delete(p) : null,
                );
              },
            ),
          ),
        ),
        StepActionBar(
          loading: false,
          enabled: _panels.isNotEmpty && !_generatingSlots,
          label: 'Próximo: Revisão',
          onPressed: () => context.go(ProductionStep.review.location(widget.projectId)),
        ),
      ],
    );
  }

  Widget _header(bool busyImages) => Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          PageTitle(
            eyebrow: 'ETAPA 3 DE 5',
            title: _panels.isEmpty ? 'Roteiro' : 'A IA propôs um roteiro.',
            lede: _panels.isEmpty
                ? 'Trabalhe a sinopse com a IA e gere o storyboard quando estiver pronto.'
                : 'Aqui está o storyboard sugerido. Você pode gerar tudo de novo ou seguir para '
                    'revisar quadro por quadro.',
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Eyebrow('SINOPSE'),
                      const Spacer(),
                      IconButton(
                          tooltip: 'Editar',
                          onPressed: _editSynopsis,
                          icon: const Icon(Icons.edit_outlined, size: 18)),
                      IconButton(
                          tooltip: 'Gerar com IA',
                          onPressed: _generatingSynopsis ? null : _regenSynopsis,
                          icon: const Icon(Icons.auto_awesome, size: 18)),
                    ],
                  ),
                  if (_generatingSynopsis)
                    const GeneratingNotice('Gerando sinopse…')
                  else
                    Text(_synopsisText, style: const TextStyle(height: 1.4)),
                ],
              ),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'ELENCO: ${_project!.characters.isEmpty ? 'Sem personagens definidos.' : _project!.characters.map((c) => c.name).join(', ')}',
            style: const TextStyle(fontSize: 12, color: SumiColors.ink3),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              const Text('Quadros:'),
              IconButton(
                  onPressed: _targetPanels > 5 ? () => setState(() => _targetPanels--) : null,
                  icon: const Icon(Icons.remove)),
              Text('$_targetPanels'),
              IconButton(
                  onPressed: _targetPanels < 30 ? () => setState(() => _targetPanels++) : null,
                  icon: const Icon(Icons.add)),
              const Spacer(),
              FilledButton(
                onPressed: _generatingSlots || busyImages ? null : _generatePanels,
                child: Text(_panels.isEmpty ? '✦ Gerar quadros' : '✦ Gerar de novo'),
              ),
            ],
          ),
          if (_generatingSlots) const GeneratingNotice('A IA está dividindo o roteiro em quadros…'),
          if (_panels.isNotEmpty) ...[
            const SizedBox(height: 8),
            if (busyImages)
              GeneratingNotice('Gerando imagens… $_imagesDone de $_imagesTotal',
                  progress: _imagesTotal == 0 ? null : (_imagesDone * 100 ~/ _imagesTotal))
            else
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: _generatingSlots ? null : _generateAllImages,
                      icon: const Icon(Icons.image_outlined),
                      label: const Text('Gerar todas as imagens'),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton(
                    tooltip: 'Inserir no início',
                    onPressed: () => _insertAfter(0),
                    icon: const Icon(Icons.vertical_align_top),
                  ),
                  IconButton(
                    tooltip: 'Apagar todos',
                    onPressed: _deleteAll,
                    icon: const Icon(Icons.delete_sweep_outlined),
                  ),
                ],
              ),
            const SizedBox(height: 4),
            const Text('Segure e arraste ☰ para reordenar.',
                style: TextStyle(fontSize: 11, color: SumiColors.ink3)),
          ],
          const SizedBox(height: 8),
        ],
      );
}

class _PanelCard extends StatelessWidget {
  final int index;
  final Panel panel;
  final bool generatingContent;
  final bool generatingImage;
  final VoidCallback onEdit;
  final VoidCallback onGenerateContent;
  final VoidCallback onInsertAfter;
  final VoidCallback? onDelete;

  const _PanelCard({
    super.key,
    required this.index,
    required this.panel,
    required this.generatingContent,
    required this.generatingImage,
    required this.onEdit,
    required this.onGenerateContent,
    required this.onInsertAfter,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) => Card(
        margin: const EdgeInsets.only(bottom: 10),
        child: Padding(
          padding: const EdgeInsets.all(10),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SizedBox(
                width: 72,
                height: 72,
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: generatingImage
                      ? const Center(child: CircularProgressIndicator(strokeWidth: 2))
                      : panel.hasImage
                          ? Image.network(fileUrl(panel.imageUrl), fit: BoxFit.cover)
                          : Container(color: SumiColors.paper2),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('QUADRO ${panel.indexOrder.toString().padLeft(2, '0')} · ${panel.label}',
                        style: const TextStyle(fontFamily: monoFamily, fontSize: 11)),
                    Text('${panel.framing}${panel.characterName != null ? ' · ${panel.characterName}' : ''}',
                        style: const TextStyle(fontSize: 11, color: SumiColors.ink3)),
                    const SizedBox(height: 4),
                    if (generatingContent)
                      const LinearProgressIndicator()
                    else
                      Text(panel.caption.isEmpty ? '(sem direção ainda)' : panel.caption,
                          maxLines: 4, overflow: TextOverflow.ellipsis),
                    for (final b in panel.bubbles)
                      Text('[${bubbleKindLabels[b.kind] ?? b.kind}] ${b.text}',
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(fontSize: 12, color: SumiColors.ink2)),
                    Row(
                      children: [
                        IconButton(
                            tooltip: 'Editar',
                            onPressed: onEdit,
                            icon: const Icon(Icons.edit_outlined, size: 18)),
                        IconButton(
                            tooltip: 'Gerar conteúdo',
                            onPressed: generatingContent ? null : onGenerateContent,
                            icon: const Icon(Icons.auto_awesome, size: 18)),
                        IconButton(
                            tooltip: 'Inserir depois',
                            onPressed: onInsertAfter,
                            icon: const Icon(Icons.add_box_outlined, size: 18)),
                        IconButton(
                            tooltip: 'Excluir',
                            onPressed: onDelete,
                            icon: const Icon(Icons.delete_outline, size: 18)),
                        const Spacer(),
                        ReorderableDragStartListener(
                          index: index,
                          child: const Padding(
                            padding: EdgeInsets.all(8),
                            child: Icon(Icons.drag_handle),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      );
}

class _PanelEditSheet extends StatefulWidget {
  final Panel panel;
  final List<String> cast;
  const _PanelEditSheet({required this.panel, required this.cast});

  @override
  State<_PanelEditSheet> createState() => _PanelEditSheetState();
}

class _PanelEditSheetState extends State<_PanelEditSheet> {
  late final _label = TextEditingController(text: widget.panel.label);
  late final _framing = TextEditingController(text: widget.panel.framing);
  late final _caption = TextEditingController(text: widget.panel.caption);
  late String? _character = widget.panel.characterName;

  @override
  void dispose() {
    _label.dispose();
    _framing.dispose();
    _caption.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Padding(
        padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text('Quadro ${widget.panel.indexOrder}',
                  style: const TextStyle(fontFamily: serifFamily, fontSize: 20, fontWeight: FontWeight.w700)),
              const SizedBox(height: 12),
              TextField(controller: _label, decoration: const InputDecoration(labelText: 'Título')),
              const SizedBox(height: 12),
              TextField(controller: _framing, decoration: const InputDecoration(labelText: 'Enquadramento')),
              const SizedBox(height: 12),
              DropdownButtonFormField<String?>(
                key: ValueKey('dd-${widget.cast.contains(_character) ? _character : null}'),
                initialValue: widget.cast.contains(_character) ? _character : null,
                decoration: const InputDecoration(labelText: 'Personagem'),
                items: [
                  const DropdownMenuItem(value: null, child: Text('—')),
                  for (final c in widget.cast) DropdownMenuItem(value: c, child: Text(c)),
                ],
                onChanged: (v) => setState(() => _character = v),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _caption,
                minLines: 3,
                maxLines: 8,
                decoration: InputDecoration(
                  labelText: 'Direção',
                  alignLabelWithHint: true,
                  suffixIcon: DictationButton(controller: _caption),
                ),
              ),
              const SizedBox(height: 16),
              FilledButton(
                onPressed: () => Navigator.pop(context, {
                  'label': _label.text.trim(),
                  'framing': _framing.text.trim(),
                  'caption': _caption.text.trim(),
                  'character_name': _character,
                }),
                child: const Padding(padding: EdgeInsets.symmetric(vertical: 12), child: Text('Salvar')),
              ),
            ],
          ),
        ),
      );
}
