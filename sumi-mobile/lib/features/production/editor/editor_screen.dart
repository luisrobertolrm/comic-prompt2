import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/app_theme.dart';
import '../../../shared/empty_state.dart';
import '../../../shared/error_retry.dart';
import '../manga_panel_view.dart';
import '../panel.dart';
import '../panels_repository.dart';
import '../production_step.dart';
import '../step_action_bar.dart';
import 'page_layouts.dart';

class EditorScreen extends ConsumerStatefulWidget {
  final String projectId;
  const EditorScreen({super.key, required this.projectId});

  @override
  ConsumerState<EditorScreen> createState() => _EditorScreenState();
}

class _EditorScreenState extends ConsumerState<EditorScreen> {
  List<Panel> _panels = [];
  Object? _error;
  bool _loading = true;
  String _layoutKey = 'manga-vertical';
  int _page = 0;
  final Map<String, Timer> _pendingSaves = {};

  PageLayout get _layout => pageLayouts[_layoutKey]!;
  int get _slotsPerPage => _layout.slots.length;
  int get _totalPages => (_panels.length / _slotsPerPage).ceil().clamp(1, 999);

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    for (final t in _pendingSaves.values) {
      t.cancel();
    }
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final panels = await ref.read(panelsRepositoryProvider).list(widget.projectId);
      setState(() => _panels = panels);
    } catch (e) {
      setState(() => _error = e);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _moveBubble(Panel panel, int i, int x, int y) {
    final updated = panel.copyWith(bubbles: [
      for (var j = 0; j < panel.bubbles.length; j++)
        j == i ? panel.bubbles[j].copyWith(x: x, y: y) : panel.bubbles[j],
    ]);
    setState(() => _panels = [for (final p in _panels) p.id == panel.id ? updated : p]);
  }

  /// Salva ao soltar, com 500 ms de debounce por quadro (como o patchSubject do web).
  void _saveBubbles(String panelId) {
    _pendingSaves[panelId]?.cancel();
    _pendingSaves[panelId] = Timer(const Duration(milliseconds: 500), () {
      final panel = _panels.firstWhere((p) => p.id == panelId);
      ref
          .read(panelsRepositoryProvider)
          .update(panelId, {'bubbles': panel.bubbles.map((b) => b.toJson()).toList()});
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) return ErrorRetry(error: _error!, onRetry: _load);
    if (_panels.isEmpty) {
      return EmptyState(
        message: 'Nenhum quadro para compor.',
        actionLabel: 'Ir para o Roteiro',
        onAction: () => context.go(ProductionStep.script.location(widget.projectId)),
      );
    }
    final start = _page * _slotsPerPage;
    final visible = _panels.skip(start).take(_slotsPerPage).toList();

    return Column(
      children: [
        Expanded(
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              const PageTitle(
                eyebrow: 'EDITOR',
                title: 'Componha a página.',
                lede: 'Arraste os balões para reposicionar. Troque o layout. Use dois dedos '
                    'para ampliar a página.',
              ),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                children: [
                  for (final e in pageLayouts.entries)
                    ChoiceChip(
                      label: Text(e.value.label),
                      selected: e.key == _layoutKey,
                      showCheckmark: false,
                      labelStyle: TextStyle(
                          color: e.key == _layoutKey ? SumiColors.paper : SumiColors.ink2),
                      onSelected: (_) => setState(() {
                        _layoutKey = e.key;
                        _page = 0;
                      }),
                    ),
                ],
              ),
              const SizedBox(height: 12),
              InteractiveViewer(
                maxScale: 4,
                child: AspectRatio(
                  aspectRatio: _layout.aspect,
                  child: Container(
                    color: Colors.white,
                    padding: const EdgeInsets.all(pageGap),
                    child: LayoutBuilder(
                      builder: (_, box) => Stack(
                        children: [
                          for (var i = 0; i < visible.length; i++)
                            _slot(_layout.slots[i], box.biggest, visible[i]),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  IconButton(
                      onPressed: _page > 0 ? () => setState(() => _page--) : null,
                      icon: const Icon(Icons.chevron_left)),
                  Text('Página ${_page + 1} de $_totalPages'),
                  IconButton(
                      onPressed: _page < _totalPages - 1 ? () => setState(() => _page++) : null,
                      icon: const Icon(Icons.chevron_right)),
                ],
              ),
            ],
          ),
        ),
        StepActionBar(
          loading: false,
          enabled: true,
          label: 'Próximo: Finalizar',
          onPressed: () => context.go(ProductionStep.finalize.location(widget.projectId)),
        ),
      ],
    );
  }

  /// Posiciona o quadro como o CSS grid do web (frações + gap).
  Widget _slot(LayoutSlot slot, Size size, Panel panel) {
    ({double offset, double length}) track(List<double> fr, int start, int span, double total) {
      final free = total - pageGap * (fr.length - 1);
      final sum = fr.reduce((a, b) => a + b);
      double offset = 0;
      for (var i = 0; i < start - 1; i++) {
        offset += free * fr[i] / sum + pageGap;
      }
      double length = pageGap * (span - 1);
      for (var i = start - 1; i < start - 1 + span; i++) {
        length += free * fr[i] / sum;
      }
      return (offset: offset, length: length);
    }

    final x = track(_layout.cols, slot.col, slot.colSpan, size.width);
    final y = track(_layout.rows, slot.row, slot.rowSpan, size.height);
    return Positioned(
      left: x.offset,
      top: y.offset,
      width: x.length,
      height: y.length,
      child: MangaPanelView(
        panel: panel,
        fill: true,
        onBubbleMoved: (i, bx, by) => _moveBubble(panel, i, bx, by),
        onBubbleDropped: (_) => _saveBubbles(panel.id),
      ),
    );
  }
}
