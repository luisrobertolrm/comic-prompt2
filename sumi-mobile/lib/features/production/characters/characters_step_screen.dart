import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/app_theme.dart';
import '../../../shared/empty_state.dart';
import '../../../shared/error_retry.dart';
import '../../library/character.dart';
import '../../library/character_card.dart';
import '../../library/character_form.dart';
import '../../library/characters_repository.dart';
import '../../projects/project.dart';
import '../../projects/projects_repository.dart';
import '../production_step.dart';
import '../step_action_bar.dart';

class CharactersStepScreen extends ConsumerStatefulWidget {
  final String projectId;
  const CharactersStepScreen({super.key, required this.projectId});

  @override
  ConsumerState<CharactersStepScreen> createState() => _CharactersStepScreenState();
}

class _CharactersStepScreenState extends ConsumerState<CharactersStepScreen> {
  Project? _project;
  List<Character> _characters = [];
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
        ref.read(charactersRepositoryProvider).list(),
      ]);
      final project = results[0] as Project;
      setState(() {
        _project = project;
        _characters = results[1] as List<Character>;
        _selected = project.characters.map((c) => c.id).toSet();
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

  Future<void> _openForm({Character? character}) async {
    final project = _project;
    if (project == null) return;
    final saved = await showModalBottomSheet<Character>(
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
              Text(character == null ? 'Novo personagem' : 'Editar personagem',
                  style: const TextStyle(
                      fontFamily: serifFamily, fontSize: 20, fontWeight: FontWeight.w700)),
              const SizedBox(height: 12),
              CharacterForm(
                character: character,
                style: project.style,
                colorMode: project.colorMode,
                onSaved: (c) => Navigator.of(sheetContext).pop(c),
              ),
            ],
          ),
        ),
      ),
    );
    if (saved == null) return;
    setState(() {
      final i = _characters.indexWhere((c) => c.id == saved.id);
      if (i >= 0) {
        _characters[i] = saved;
      } else {
        _characters.add(saved);
        _selected.add(saved.id);
      }
    });
  }

  Future<void> _advance() async {
    setState(() => _saving = true);
    try {
      await ref.read(projectsRepositoryProvider).setCharacters(widget.projectId, _selected.toList());
      ref.invalidate(furthestStepProvider(widget.projectId));
      if (mounted) context.go(ProductionStep.scenarios.location(widget.projectId));
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
                eyebrow: 'ETAPA 2 DE 5',
                title: 'Quem habita essa história?',
                lede: 'Escolha da biblioteca ou crie um novo personagem com retrato gerado pela IA.',
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
                    label: const Text('Novo personagem'),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              if (_characters.isEmpty)
                EmptyState(
                  message: 'Nenhum personagem na biblioteca ainda.',
                  actionLabel: 'Criar o primeiro personagem',
                  onAction: () => _openForm(),
                )
              else
                GridView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2,
                    mainAxisSpacing: 12,
                    crossAxisSpacing: 12,
                    childAspectRatio: 0.62,
                  ),
                  itemCount: _characters.length,
                  itemBuilder: (_, i) {
                    final c = _characters[i];
                    return CharacterCard(
                      character: c,
                      selected: _selected.contains(c.id),
                      onTap: () => _toggle(c.id),
                      onEdit: () => _openForm(character: c),
                    );
                  },
                ),
            ],
          ),
        ),
        StepActionBar(
          loading: _saving,
          enabled: true,
          label: 'Próximo: Cenários',
          onPressed: _advance,
          secondaryLabel: 'Pular',
          onSecondary: () => context.go(ProductionStep.script.location(widget.projectId)),
        ),
      ],
    );
  }
}
