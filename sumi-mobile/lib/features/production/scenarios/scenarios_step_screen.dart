import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/api/api_client.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/empty_state.dart';
import '../../../shared/error_retry.dart';
import '../../projects/project.dart';
import '../../projects/projects_repository.dart';
import '../production_step.dart';
import '../scenario.dart';
import '../scenarios_repository.dart';
import '../step_action_bar.dart';
import 'scenario_form.dart';

class ScenariosStepScreen extends ConsumerStatefulWidget {
  final String projectId;
  const ScenariosStepScreen({super.key, required this.projectId});

  @override
  ConsumerState<ScenariosStepScreen> createState() => _ScenariosStepScreenState();
}

class _ScenariosStepScreenState extends ConsumerState<ScenariosStepScreen> {
  Project? _project;
  List<Scenario> _scenarios = [];
  Set<String> _selected = {};
  Object? _error;
  bool _loading = true;
  bool _saving = false;

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
      final results = await Future.wait([
        ref.read(projectsRepositoryProvider).get(widget.projectId),
        ref.read(scenariosRepositoryProvider).list(),
      ]);
      final project = results[0] as Project;
      setState(() {
        _project = project;
        _scenarios = results[1] as List<Scenario>;
        _selected = project.scenarios.map((s) => s.id).toSet();
      });
    } catch (e) {
      setState(() => _error = e);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _toggle(String id) => setState(() {
        if (!_selected.remove(id)) _selected.add(id);
      });

  Future<void> _openForm({Scenario? scenario}) async {
    final project = _project;
    if (project == null) return;
    final saved = await showModalBottomSheet<Scenario>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (sheetContext) => Padding(
        padding: EdgeInsets.only(bottom: MediaQuery.of(sheetContext).viewInsets.bottom),
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(scenario == null ? 'Novo cenário' : 'Editar cenário',
                  style: const TextStyle(
                      fontFamily: serifFamily, fontSize: 20, fontWeight: FontWeight.w700)),
              ScenarioForm(
                scenario: scenario,
                style: project.style,
                colorMode: project.colorMode,
                onSaved: (s) => Navigator.of(sheetContext).pop(s),
              ),
            ],
          ),
        ),
      ),
    );
    if (saved == null) return;
    setState(() {
      final i = _scenarios.indexWhere((s) => s.id == saved.id);
      if (i >= 0) {
        _scenarios[i] = saved;
      } else {
        _scenarios.add(saved);
        _selected.add(saved.id);
      }
    });
  }

  Future<void> _advance() async {
    setState(() => _saving = true);
    try {
      await ref.read(projectsRepositoryProvider).setScenarios(widget.projectId, _selected.toList());
      ref.invalidate(furthestStepProvider(widget.projectId));
      if (mounted) context.go(ProductionStep.script.location(widget.projectId));
    } catch (_) {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) return ErrorRetry(error: _error!, onRetry: _load);

    return Column(
      children: [
        Expanded(
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              const PageTitle(
                eyebrow: 'ETAPA 3 DE 5',
                title: 'Onde a história acontece?',
                lede: 'Escolha cenários da biblioteca ou gere novos. Eles mantêm o ambiente '
                    'coerente entre os quadros.',
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Text('${_selected.length} selecionado(s)',
                      style: const TextStyle(color: SumiColors.ink3)),
                  const Spacer(),
                  FilledButton.icon(
                    onPressed: () => _openForm(),
                    icon: const Icon(Icons.add),
                    label: const Text('Novo cenário'),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              if (_scenarios.isEmpty)
                EmptyState(
                  message: 'Nenhum cenário na biblioteca ainda.',
                  actionLabel: 'Criar o primeiro cenário',
                  onAction: () => _openForm(),
                )
              else
                for (final s in _scenarios)
                  Card(
                    margin: const EdgeInsets.only(bottom: 8),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                      side: BorderSide(
                        color: _selected.contains(s.id) ? SumiColors.ink : SumiColors.rule,
                        width: _selected.contains(s.id) ? 2 : 1,
                      ),
                    ),
                    child: ListTile(
                      onTap: () => _toggle(s.id),
                      leading: ClipRRect(
                        borderRadius: BorderRadius.circular(4),
                        child: SizedBox(
                          width: 56,
                          height: 56,
                          child: s.imageUrl != null && s.imageUrl!.isNotEmpty
                              ? Image.network(fileUrl(s.imageUrl), fit: BoxFit.cover)
                              : Container(
                                  color: SumiColors.paper2,
                                  alignment: Alignment.center,
                                  child: Text(s.initial),
                                ),
                        ),
                      ),
                      title: Text(s.name),
                      subtitle: Text(
                        [s.kind, if (s.summary != null) s.summary!].join(' · '),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                      trailing: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          IconButton(
                            icon: const Icon(Icons.edit_outlined),
                            onPressed: () => _openForm(scenario: s),
                          ),
                          Icon(_selected.contains(s.id)
                              ? Icons.check_circle
                              : Icons.radio_button_unchecked),
                        ],
                      ),
                    ),
                  ),
            ],
          ),
        ),
        StepActionBar(
          loading: _saving,
          enabled: true,
          label: 'Próximo: Roteiro',
          onPressed: _advance,
          secondaryLabel: 'Pular',
          onSecondary: () => context.go(ProductionStep.script.location(widget.projectId)),
        ),
      ],
    );
  }
}
