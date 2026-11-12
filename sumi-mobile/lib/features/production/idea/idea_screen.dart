import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/app_theme.dart';
import '../../projects/projects_repository.dart';
import '../../voice_test/voices_repository.dart';
import '../production_draft.dart';
import '../step_action_bar.dart';
import '../production_step.dart';
import '../styles_repository.dart';

const _genres = [
  'Shojo', 'Shonen', 'Slice of life', 'Mistério', 'Drama',
  'Comédia', 'Fantasia', 'Romance', 'Aventura', 'Horror leve',
];
const _tones = ['Doce e melancólico', 'Tenso', 'Cômico', 'Mistério leve', 'Reflexivo', 'Heróico'];
const _examples = [
  'Uma estudante recebe uma carta anônima debaixo da carteira no último dia de aula.',
  'Um gato preto guia uma garota tímida até um portão que ela nunca tinha visto.',
  'Dois rivais de clube esquecem o jogo quando começa a chover.',
];
const _languages = {
  'pt-BR': 'Português (BR)',
  'ja': '日本語',
  'en': 'English',
  'es': 'Español',
};

class IdeaScreen extends ConsumerStatefulWidget {
  final String? projectId;
  const IdeaScreen({super.key, required this.projectId});

  @override
  ConsumerState<IdeaScreen> createState() => _IdeaScreenState();
}

class _IdeaScreenState extends ConsumerState<IdeaScreen> {
  final _title = TextEditingController();
  final _idea = TextEditingController();
  String _genre = 'Shojo';
  String _tone = 'Doce e melancólico';
  int _pages = 4;
  String _language = 'pt-BR';
  String _style = '';
  String _colorMode = '';
  String? _narratorVoiceId;
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _title.addListener(() => setState(() {}));
    _idea.addListener(() => setState(() {}));
    if (widget.projectId != null) _load(widget.projectId!);
  }

  Future<void> _load(String id) async {
    setState(() => _loading = true);
    try {
      final p = await ref.read(projectsRepositoryProvider).get(id);
      _title.text = p.title;
      _idea.text = p.premise ?? '';
      setState(() {
        _genre = p.genre;
        _tone = p.tone;
        _pages = p.pages;
        _style = p.style;
        if (p.colorMode.isNotEmpty) _colorMode = p.colorMode;
        _narratorVoiceId = p.narratorVoiceId;
      });
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  void dispose() {
    _title.dispose();
    _idea.dispose();
    super.dispose();
  }

  bool get _canAdvance => _title.text.trim().isNotEmpty && _idea.text.trim().isNotEmpty && !_loading;

  Future<void> _advance() async {
    if (!_canAdvance) return;
    setState(() => _loading = true);
    final repo = ref.read(projectsRepositoryProvider);
    final body = {
      'title': _title.text,
      'premise': _idea.text,
      'genre': _genre,
      'tone': _tone,
      'pages': _pages,
      'style': _style,
      'color_mode': _colorMode,
      'narrator_voice_id': _narratorVoiceId,
    };
    try {
      final project = widget.projectId == null
          ? await repo.create({...body, 'language': _language})
          : await repo.update(widget.projectId!, body);
      await ref.read(productionDraftProvider.notifier).open(project.id, project.title);
      ref.invalidate(furthestStepProvider(project.id));
      if (mounted) context.go(ProductionStep.characters.location(project.id));
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final catalog = ref.watch(styleCatalogProvider).valueOrNull;
    if (catalog != null) {
      if (_style.isEmpty) _style = catalog.defaultStyle;
      if (_colorMode.isEmpty) _colorMode = catalog.defaultColorMode;
    }
    final voices = ref.watch(savedVoicesProvider).valueOrNull ?? const [];

    return Column(
      children: [
        Expanded(
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              const PageTitle(
                eyebrow: 'ETAPA 1 DE 5',
                title: 'Conte a primeira faísca.',
                lede: 'Não precisa ser detalhada. Uma ideia em uma frase é suficiente — '
                    'a IA vai te ajudar a expandir e propor cenas.',
              ),
              const SizedBox(height: 20),
              TextField(
                controller: _title,
                decoration: const InputDecoration(
                    labelText: 'Título', hintText: 'Ex: A carta no livro emprestado'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _idea,
                minLines: 3,
                maxLines: 8,
                decoration: const InputDecoration(
                  labelText: 'Sua ideia',
                  hintText: 'Ex: Uma carta dobrada cai do livro emprestado. Quem a colocou ali?',
                  alignLabelWithHint: true,
                ),
              ),
              const SizedBox(height: 8),
              const Text('Sugestões para começar:',
                  style: TextStyle(color: SumiColors.ink3, fontSize: 12)),
              for (final ex in _examples)
                TextButton(
                  style: TextButton.styleFrom(alignment: Alignment.centerLeft),
                  onPressed: () => _idea.text = ex,
                  child: Text(ex, style: const TextStyle(color: SumiColors.ink2)),
                ),
              _Section('Gênero', _choices(_genres, _genre, (g) => setState(() => _genre = g))),
              _Section('Tom emocional', _choices(_tones, _tone, (t) => setState(() => _tone = t))),
              _Section(
                'Páginas',
                Row(
                  children: [
                    IconButton.outlined(
                        onPressed: _pages > 1 ? () => setState(() => _pages--) : null,
                        icon: const Icon(Icons.remove)),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      child: Text('$_pages', style: const TextStyle(fontSize: 20)),
                    ),
                    IconButton.outlined(
                        onPressed: _pages < 20 ? () => setState(() => _pages++) : null,
                        icon: const Icon(Icons.add)),
                    const SizedBox(width: 12),
                    Text('≈ ${_pages * 3}–${_pages * 4} quadros',
                        style: const TextStyle(color: SumiColors.ink3)),
                  ],
                ),
                hint: 'A IA distribuirá os quadros entre as páginas.',
              ),
              if (widget.projectId == null)
                _Section(
                  'Idioma dos balões',
                  DropdownButtonFormField<String>(
                    key: ValueKey('dd-$_language'),
                    initialValue: _language,
                    items: [
                      for (final e in _languages.entries)
                        DropdownMenuItem(value: e.key, child: Text(e.value)),
                    ],
                    onChanged: (v) => setState(() => _language = v ?? 'pt-BR'),
                  ),
                ),
              _Section(
                'Voz do narrador',
                DropdownButtonFormField<String?>(
                  key: ValueKey('dd-${voices.any((v) => v.id == _narratorVoiceId) ? _narratorVoiceId : null}'),
                  initialValue: voices.any((v) => v.id == _narratorVoiceId) ? _narratorVoiceId : null,
                  isExpanded: true,
                  items: [
                    const DropdownMenuItem(value: null, child: Text('— Sem voz de narração —')),
                    for (final v in voices)
                      DropdownMenuItem(
                          value: v.id,
                          child: Text(v.meta.isEmpty ? v.name : '${v.name} · ${v.meta}')),
                  ],
                  onChanged: (v) => setState(() => _narratorVoiceId = v),
                ),
                hint: 'Voz usada na narração em off. Cadastre vozes em Teste de Voz.',
              ),
              if (catalog != null) ...[
                _Section(
                  'ESTILO VISUAL',
                  _optionList(catalog.styles, _style, (id) => setState(() => _style = id)),
                ),
                _Section(
                  'MODO DE COR',
                  _optionList(catalog.colorModes, _colorMode, (id) => setState(() => _colorMode = id)),
                ),
              ],
            ],
          ),
        ),
        StepActionBar(
          loading: _loading,
          enabled: _canAdvance,
          label: 'Próximo: Personagens',
          onPressed: _advance,
        ),
      ],
    );
  }

  Widget _choices(List<String> options, String selected, ValueChanged<String> onSelected) => Wrap(
        spacing: 8,
        runSpacing: 8,
        children: [
          for (final o in options)
            ChoiceChip(
              label: Text(o),
              selected: o == selected,
              showCheckmark: false,
              labelStyle: TextStyle(color: o == selected ? SumiColors.paper : SumiColors.ink2),
              onSelected: (_) => onSelected(o),
            ),
        ],
      );

  Widget _optionList(List<StyleOption> options, String selected, ValueChanged<String> onSelected) =>
      RadioGroup<String>(
        groupValue: selected,
        onChanged: (v) => onSelected(v!),
        child: Column(
          children: [
            for (final o in options)
              RadioListTile<String>(
                contentPadding: EdgeInsets.zero,
                value: o.id,
                title: Text(o.label),
                subtitle: o.note.isEmpty ? null : Text(o.note),
              ),
          ],
        ),
      );
}

class _Section extends StatelessWidget {
  final String label;
  final Widget child;
  final String? hint;
  const _Section(this.label, this.child, {this.hint});

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(top: 20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label, style: const TextStyle(fontWeight: FontWeight.w600)),
            if (hint != null)
              Padding(
                padding: const EdgeInsets.only(top: 2, bottom: 8),
                child: Text(hint!, style: const TextStyle(color: SumiColors.ink3, fontSize: 12)),
              )
            else
              const SizedBox(height: 8),
            child,
          ],
        ),
      );
}
