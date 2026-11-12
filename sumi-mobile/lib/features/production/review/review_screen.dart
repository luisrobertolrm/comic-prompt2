import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/api/api_client.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/empty_state.dart';
import '../../../shared/error_retry.dart';
import '../candidate_picker.dart';
import '../manga_panel_view.dart';
import '../panel.dart';
import '../panels_repository.dart';
import '../poll_job.dart';
import '../production_step.dart';
import '../step_action_bar.dart';

const _framings = [
  'Plano geral', 'Plano americano', 'Plano médio', 'Close-up',
  'Extreme close', 'Inserto', 'Detalhe', 'Plongée', 'Contra-plongée',
];
const _aspects = {'16-9': '16:9', '4-3': '4:3', '1-1': '1:1', '3-4': '3:4'};

class ReviewScreen extends ConsumerStatefulWidget {
  final String projectId;
  const ReviewScreen({super.key, required this.projectId});

  @override
  ConsumerState<ReviewScreen> createState() => _ReviewScreenState();
}

class _ReviewScreenState extends ConsumerState<ReviewScreen> {
  List<Panel> _panels = [];
  int _idx = 0;
  Object? _error;
  bool _loading = true;
  bool _generatingImage = false;
  bool _generatingAll = false;
  bool _generatingBubbles = false;
  bool _regenContent = false;
  Timer? _debounce;
  late final _caption = TextEditingController();
  late final _prompt = TextEditingController();
  late final ResumeListener _resume;

  PanelsRepository get _repo => ref.read(panelsRepositoryProvider);
  Panel? get _cur => _panels.isEmpty ? null : _panels[_idx];

  @override
  void initState() {
    super.initState();
    _resume = ResumeListener(_reload);
    _load();
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _resume.dispose();
    _caption.dispose();
    _prompt.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final panels = await _repo.list(widget.projectId);
      setState(() {
        _panels = panels;
        _idx = 0;
      });
      _syncFields();
    } catch (e) {
      setState(() => _error = e);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _reload() async {
    try {
      final panels = await _repo.list(widget.projectId);
      if (!mounted) return;
      setState(() {
        _panels = panels;
        _idx = _idx.clamp(0, panels.isEmpty ? 0 : panels.length - 1);
      });
      _syncFields();
    } catch (_) {}
  }

  void _syncFields() {
    final cur = _cur;
    _caption.text = cur?.caption ?? '';
    _prompt.text = cur?.prompt ?? '';
  }

  void _goTo(int i) {
    setState(() => _idx = i);
    _syncFields();
  }

  void _setLocal(Panel updated) {
    setState(() => _panels = [for (final p in _panels) p.id == updated.id ? updated : p]);
  }

  /// Digitação: salva após 600 ms parado (como o debounce do web).
  void _patchDebounced(Map<String, dynamic> patch) {
    final cur = _cur;
    if (cur == null) return;
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 600), () => _repo.update(cur.id, patch));
  }

  Future<void> _patchNow(Map<String, dynamic> patch) async {
    final cur = _cur;
    if (cur == null) return;
    final updated = await _repo.update(cur.id, patch);
    if (mounted) _setLocal(updated);
  }

  Future<void> _setBubbles(List<Bubble> bubbles) =>
      _patchNow({'bubbles': bubbles.map((b) => b.toJson()).toList()});

  Future<void> _run(void Function(bool) setBusy, Future<void> Function() action) async {
    setState(() => setBusy(true));
    try {
      await action();
    } catch (_) {
    } finally {
      if (mounted) setState(() => setBusy(false));
    }
  }

  Future<void> _approve() async {
    await _patchNow({'status': 'approved'});
    if (!mounted) return;
    if (_idx < _panels.length - 1) {
      _goTo(_idx + 1);
    } else {
      context.go(ProductionStep.editor.location(widget.projectId));
    }
  }

  Future<void> _move(int dir) async {
    final j = _idx + dir;
    if (j < 0 || j >= _panels.length) return;
    final list = List<Panel>.from(_panels);
    final tmp = list[_idx];
    list[_idx] = list[j];
    list[j] = tmp;
    setState(() {
      _panels = list;
      _idx = j;
    });
    await _repo.reorder(widget.projectId, list.map((p) => p.id).toList());
    await _reload();
  }

  Future<void> _insert() async {
    await _repo.insert(widget.projectId, _idx + 1);
    await _reload();
    if (mounted) _goTo(_idx + 1);
  }

  Future<void> _delete() async {
    final cur = _cur;
    if (cur == null || _panels.length <= 1) return;
    await _repo.delete(cur.id);
    await _reload();
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) return ErrorRetry(error: _error!, onRetry: _load);
    final cur = _cur;
    if (cur == null) {
      return EmptyState(
        message: 'Nenhum quadro ainda. Gere o roteiro primeiro.',
        actionLabel: 'Ir para o Roteiro',
        onAction: () => context.go(ProductionStep.script.location(widget.projectId)),
      );
    }
    final allImages = _panels.every((p) => p.hasImage);

    return Column(
      children: [
        Expanded(
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Eyebrow('ETAPA 4 DE 5 — REVISÃO QUADRO A QUADRO'),
              const SizedBox(height: 4),
              Text('Quadro ${cur.indexOrder.toString().padLeft(2, '0')} · ${cur.label}',
                  style: const TextStyle(
                      fontFamily: serifFamily, fontSize: 22, fontWeight: FontWeight.w700)),
              const SizedBox(height: 4),
              const Text('Arraste os balões diretamente no quadro para reposicioná-los.',
                  style: TextStyle(color: SumiColors.ink3)),
              const SizedBox(height: 12),
              _Strip(panels: _panels, current: _idx, onTap: _goTo),
              const SizedBox(height: 12),
              MangaPanelView(
                panel: cur,
                loading: _generatingImage || _generatingAll,
                onBubbleMoved: (i, x, y) => _setLocal(cur.copyWith(bubbles: [
                  for (var j = 0; j < cur.bubbles.length; j++)
                    j == i ? cur.bubbles[j].copyWith(x: x, y: y) : cur.bubbles[j],
                ])),
                onBubbleDropped: (_) => _setBubbles(_cur!.bubbles),
              ),
              if (_generatingAll) ...[
                const SizedBox(height: 8),
                const GeneratingNotice('Gerando as imagens de todos os quadros…'),
              ],
              const SizedBox(height: 8),
              Row(
                children: [
                  IconButton(
                      onPressed: _idx > 0 ? () => _goTo(_idx - 1) : null,
                      icon: const Icon(Icons.chevron_left)),
                  Text('${_idx + 1} / ${_panels.length}'),
                  IconButton(
                      onPressed: _idx < _panels.length - 1 ? () => _goTo(_idx + 1) : null,
                      icon: const Icon(Icons.chevron_right)),
                  const Spacer(),
                  PopupMenuButton<String>(
                    icon: const Icon(Icons.more_vert),
                    onSelected: (v) => switch (v) {
                      'left' => _move(-1),
                      'right' => _move(1),
                      'insert' => _insert(),
                      'delete' => _delete(),
                      _ => null,
                    },
                    itemBuilder: (_) => [
                      const PopupMenuItem(value: 'left', child: Text('Mover para trás')),
                      const PopupMenuItem(value: 'right', child: Text('Mover para frente')),
                      const PopupMenuItem(value: 'insert', child: Text('Inserir quadro depois')),
                      if (_panels.length > 1)
                        const PopupMenuItem(value: 'delete', child: Text('Excluir quadro')),
                    ],
                  ),
                ],
              ),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  FilledButton.icon(
                    onPressed: _generatingImage || _generatingAll
                        ? null
                        : () => _run((v) => _generatingImage = v,
                            () async => _setLocal(await _repo.generateImage(cur.id))),
                    icon: const Icon(Icons.image_outlined),
                    label: Text(cur.hasImage ? 'Regerar imagem' : 'Gerar imagem'),
                  ),
                  OutlinedButton(
                    onPressed: _generatingAll
                        ? null
                        : () => _run((v) => _generatingAll = v, () async {
                              final updated = await _repo.generateAllImages(widget.projectId);
                              if (mounted) setState(() => _panels = updated);
                              ref.invalidate(furthestStepProvider(widget.projectId));
                            }),
                    child: const Text('Gerar todas'),
                  ),
                  OutlinedButton(
                    onPressed: _regenContent
                        ? null
                        : () => _run((v) => _regenContent = v, () async {
                              _setLocal(await _repo.generateContent(cur.id));
                              _syncFields();
                            }),
                    child: Text(_regenContent ? 'Gerando…' : 'Regerar texto'),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              const Eyebrow('ENQUADRAMENTO E PROPORÇÃO'),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      key: ValueKey('dd-${_framings.contains(cur.framing) ? cur.framing : null}'),
                      initialValue: _framings.contains(cur.framing) ? cur.framing : null,
                      isExpanded: true,
                      hint: Text(cur.framing),
                      items: [for (final f in _framings) DropdownMenuItem(value: f, child: Text(f))],
                      onChanged: (v) => _patchNow({'framing': v}),
                    ),
                  ),
                  const SizedBox(width: 8),
                  DropdownButton<String>(
                    value: _aspects.containsKey(cur.aspect) ? cur.aspect : '4-3',
                    items: [
                      for (final e in _aspects.entries)
                        DropdownMenuItem(value: e.key, child: Text(e.value)),
                    ],
                    onChanged: (v) => _patchNow({'aspect': v}),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _caption,
                minLines: 2,
                maxLines: 6,
                decoration: const InputDecoration(labelText: 'Direção', alignLabelWithHint: true),
                onChanged: (v) {
                  _setLocal(cur.copyWith(caption: v));
                  _patchDebounced({'caption': v});
                },
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _prompt,
                minLines: 2,
                maxLines: 6,
                decoration:
                    const InputDecoration(labelText: 'Prompt da imagem', alignLabelWithHint: true),
                onChanged: (v) => _patchDebounced({'prompt': v}),
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  const Eyebrow('BALÕES'),
                  const Spacer(),
                  TextButton.icon(
                    onPressed: _generatingBubbles
                        ? null
                        : () => _run((v) => _generatingBubbles = v,
                            () async => _setLocal(await _repo.generateBubbles(cur.id))),
                    icon: const Icon(Icons.auto_awesome, size: 16),
                    label: Text(_generatingBubbles ? 'Gerando…' : 'Gerar balões'),
                  ),
                  TextButton.icon(
                    onPressed: () =>
                        _setBubbles([...cur.bubbles, const Bubble(text: 'Novo balão')]),
                    icon: const Icon(Icons.add, size: 16),
                    label: const Text('Adicionar'),
                  ),
                ],
              ),
              for (var i = 0; i < cur.bubbles.length; i++)
                BubbleEditor(
                  key: ValueKey('${cur.id}-$i-${cur.bubbles.length}'),
                  bubble: cur.bubbles[i],
                  onChanged: (b, {bool typing = false}) {
                    final list = [...cur.bubbles]..[i] = b;
                    if (typing) {
                      _setLocal(cur.copyWith(bubbles: list));
                      _patchDebounced({'bubbles': list.map((e) => e.toJson()).toList()});
                    } else {
                      _setBubbles(list);
                    }
                  },
                  onRemove: () => _setBubbles([...cur.bubbles]..removeAt(i)),
                ),
            ],
          ),
        ),
        StepActionBar(
          loading: false,
          enabled: true,
          label: cur.status == 'approved' && allImages ? 'Próximo: Editor' : 'Aprovar quadro',
          onPressed: cur.status == 'approved' && allImages
              ? () => context.go(ProductionStep.editor.location(widget.projectId))
              : _approve,
          secondaryLabel: 'Roteiro',
          onSecondary: () => context.go(ProductionStep.script.location(widget.projectId)),
        ),
      ],
    );
  }
}

class _Strip extends StatelessWidget {
  final List<Panel> panels;
  final int current;
  final ValueChanged<int> onTap;
  const _Strip({required this.panels, required this.current, required this.onTap});

  @override
  Widget build(BuildContext context) => SizedBox(
        height: 52,
        child: ListView.separated(
          scrollDirection: Axis.horizontal,
          itemCount: panels.length,
          separatorBuilder: (_, _) => const SizedBox(width: 6),
          itemBuilder: (_, i) {
            final p = panels[i];
            return GestureDetector(
              onTap: () => onTap(i),
              child: Container(
                width: 52,
                decoration: BoxDecoration(
                  color: p.status == 'approved' ? const Color(0xFFDFF4EB) : SumiColors.paper2,
                  border: Border.all(
                      color: i == current ? SumiColors.ink : SumiColors.rule,
                      width: i == current ? 2 : 1),
                  borderRadius: BorderRadius.circular(4),
                ),
                clipBehavior: Clip.antiAlias,
                child: p.hasImage
                    ? Image.network(fileUrl(p.imageUrl), fit: BoxFit.cover)
                    : Center(child: Text('${i + 1}')),
              ),
            );
          },
        ),
      );
}

/// Edição de um balão: texto (salva com debounce), tipo, lado e seta (salvam na hora).
class BubbleEditor extends StatefulWidget {
  final Bubble bubble;
  final void Function(Bubble bubble, {bool typing}) onChanged;
  final VoidCallback onRemove;

  const BubbleEditor({super.key, required this.bubble, required this.onChanged, required this.onRemove});

  @override
  State<BubbleEditor> createState() => _BubbleEditorState();
}

class _BubbleEditorState extends State<BubbleEditor> {
  late final _text = TextEditingController(text: widget.bubble.text);

  @override
  void dispose() {
    _text.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final b = widget.bubble;
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(8),
        child: Column(
          children: [
            TextField(
              controller: _text,
              minLines: 1,
              maxLines: 4,
              decoration: InputDecoration(
                isDense: true,
                suffixIcon: IconButton(icon: const Icon(Icons.close), onPressed: widget.onRemove),
              ),
              onChanged: (v) => widget.onChanged(b.copyWith(text: v), typing: true),
            ),
            const SizedBox(height: 6),
            Row(
              children: [
                Expanded(
                  child: DropdownButton<String>(
                    isExpanded: true,
                    value: b.kind,
                    items: [
                      for (final k in bubbleKinds)
                        DropdownMenuItem(value: k, child: Text(bubbleKindLabels[k]!)),
                    ],
                    onChanged: (v) => widget.onChanged(b.copyWith(kind: v)),
                  ),
                ),
                const SizedBox(width: 8),
                DropdownButton<String>(
                  value: b.side,
                  items: const [
                    DropdownMenuItem(value: 'left', child: Text('Esquerda')),
                    DropdownMenuItem(value: 'right', child: Text('Direita')),
                  ],
                  onChanged: (v) => widget.onChanged(b.copyWith(side: v)),
                ),
                const SizedBox(width: 8),
                DropdownButton<String>(
                  value: b.tail,
                  items: const [
                    DropdownMenuItem(value: 'none', child: Text('Sem seta')),
                    DropdownMenuItem(value: 'left', child: Text('Seta ←')),
                    DropdownMenuItem(value: 'right', child: Text('Seta →')),
                  ],
                  onChanged: (v) => widget.onChanged(b.copyWith(tail: v)),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
