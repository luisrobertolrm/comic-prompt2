import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/services/audio_player_service.dart';
import '../../core/services/notification_service.dart';
import '../../core/theme/app_theme.dart';
import 'minimax_voices.dart';
import 'voice.dart';
import 'voices_repository.dart';
import '../../shared/dictation_button.dart';

const _sexes = ['Feminino', 'Masculino', 'Outro'];

class VoiceTestScreen extends ConsumerStatefulWidget {
  const VoiceTestScreen({super.key});

  @override
  ConsumerState<VoiceTestScreen> createState() => _VoiceTestScreenState();
}

class _VoiceTestScreenState extends ConsumerState<VoiceTestScreen> {
  final _text = TextEditingController(text: 'Olá! Esta é uma voz de teste do MiniMax.');
  final _formName = TextEditingController(text: minimaxVoices.first.name);
  final _ageStart = TextEditingController();
  final _ageEnd = TextEditingController();
  final _details = TextEditingController();
  String _search = '';
  String _selectedId = minimaxVoices.first.id;
  String? _sex;
  String? _editingId;
  bool _generating = false;
  bool _saving = false;
  String _error = '';

  late final AudioPlayerService _audio;

  VoicesRepository get _repo => ref.read(voicesRepositoryProvider);

  @override
  void initState() {
    super.initState();
    _audio = ref.read(audioPlayerServiceProvider);
  }

  @override
  void dispose() {
    for (final c in [_text, _formName, _ageStart, _ageEnd, _details]) {
      c.dispose();
    }
    _audio.stop();
    super.dispose();
  }

  List<MinimaxVoice> get _filtered {
    final q = _search.trim().toLowerCase();
    if (q.isEmpty) return minimaxVoices;
    return minimaxVoices
        .where((v) => v.id.toLowerCase().contains(q) || v.name.toLowerCase().contains(q))
        .toList();
  }

  void _fillForm(Voice? v, String fallbackName) {
    _editingId = v?.id;
    _formName.text = v?.name ?? fallbackName;
    _ageStart.text = v?.ageStart?.toString() ?? '';
    _ageEnd.text = v?.ageEnd?.toString() ?? '';
    _sex = v?.sex;
    _details.text = v?.details ?? '';
  }

  void _selectVoice(MinimaxVoice voice, List<Voice> saved) => setState(() {
        _selectedId = voice.id;
        _fillForm(saved.where((v) => v.voiceId == voice.id).firstOrNull, voice.name);
      });

  void _editSaved(Voice v) => setState(() {
        _selectedId = v.voiceId;
        _fillForm(v, v.name);
      });

  void _resetForm() => setState(() {
        final voice = minimaxVoices.where((v) => v.id == _selectedId).firstOrNull;
        _fillForm(null, voice?.name ?? '');
      });

  Future<void> _generate() async {
    final text = _text.text.trim();
    if (text.isEmpty || _generating) return;
    setState(() {
      _generating = true;
      _error = '';
    });
    try {
      final bytes = await _repo.synthesize(text, _selectedId);
      await _audio.playBytes(bytes);
    } catch (_) {
      if (mounted) setState(() => _error = 'Falha ao gerar o áudio. Verifique a configuração do MiniMax.');
    } finally {
      if (mounted) setState(() => _generating = false);
    }
  }

  Future<void> _save() async {
    final name = _formName.text.trim();
    if (name.isEmpty || _saving) return;
    setState(() => _saving = true);
    final input = VoiceInput(
      name: name,
      voiceId: _selectedId,
      ageStart: int.tryParse(_ageStart.text.trim()),
      ageEnd: int.tryParse(_ageEnd.text.trim()),
      sex: _sex,
      details: _details.text.trim().isEmpty ? null : _details.text.trim(),
    );
    try {
      if (_editingId == null) {
        await _repo.create(input);
      } else {
        await _repo.update(_editingId!, input);
      }
      ref.invalidate(savedVoicesProvider);
      ref.read(notificationServiceProvider).success('Voz salva.');
      _resetForm();
    } catch (_) {
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _remove(Voice v) async {
    await _repo.delete(v.id);
    ref.invalidate(savedVoicesProvider);
    if (_editingId == v.id) _resetForm();
  }

  @override
  Widget build(BuildContext context) {
    final saved = ref.watch(savedVoicesProvider).valueOrNull ?? const <Voice>[];
    final selected = minimaxVoices.where((v) => v.id == _selectedId).firstOrNull;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const PageTitle(
          eyebrow: 'TESTE · MINIMAX',
          title: 'Teste de voz',
          lede: 'Escolha uma voz, escreva o texto e gere o áudio. Página isolada, fora do fluxo de produção.',
        ),
        const SizedBox(height: 16),
        TextField(
          decoration: const InputDecoration(
              prefixIcon: Icon(Icons.search), hintText: 'Pesquisar voz (nome ou id)…'),
          onChanged: (v) => setState(() => _search = v),
        ),
        const SizedBox(height: 8),
        SizedBox(
          height: 220,
          child: Card(
            child: ListView.builder(
              itemCount: _filtered.length,
              itemBuilder: (_, i) {
                final v = _filtered[i];
                return ListTile(
                  dense: true,
                  selected: v.id == _selectedId,
                  selectedTileColor: SumiColors.accentSoft,
                  title: Text(v.name),
                  subtitle: Text(v.id, style: const TextStyle(fontFamily: monoFamily, fontSize: 10)),
                  trailing: saved.any((s) => s.voiceId == v.id)
                      ? const Icon(Icons.bookmark, size: 16)
                      : null,
                  onTap: () => _selectVoice(v, saved),
                );
              },
            ),
          ),
        ),
        const SizedBox(height: 8),
        Text('Selecionada: ${selected == null ? _selectedId : '${selected.name} · ${selected.id}'}',
            style: const TextStyle(fontSize: 12, color: SumiColors.ink3)),
        const SizedBox(height: 12),
        TextField(
          controller: _text,
          minLines: 3,
          maxLines: 6,
          maxLength: 300,
          decoration: InputDecoration(
            labelText: 'Texto',
            alignLabelWithHint: true,
            suffixIcon: DictationButton(controller: _text),
          ),
        ),
        FilledButton.icon(
          onPressed: _generating ? null : _generate,
          icon: _generating
              ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
              : const Icon(Icons.play_arrow),
          label: Text(_generating ? 'Gerando…' : 'Gerar e ouvir'),
        ),
        if (_error.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(top: 8),
            child: Text(_error, style: const TextStyle(color: SumiColors.danger)),
          ),
        const SizedBox(height: 24),
        Eyebrow(_editingId == null ? 'SALVAR VOZ' : 'EDITAR VOZ SALVA'),
        const SizedBox(height: 8),
        TextField(
          controller: _formName,
          decoration: const InputDecoration(labelText: 'Nome', hintText: 'Ex.: Menina alegre'),
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _ageStart,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: 'Idade inicial', hintText: '5'),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: TextField(
                controller: _ageEnd,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: 'Idade final', hintText: '10'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        DropdownButtonFormField<String?>(
          key: ValueKey('dd-${_sexes.contains(_sex) ? _sex : null}'),
          initialValue: _sexes.contains(_sex) ? _sex : null,
          decoration: const InputDecoration(labelText: 'Sexo'),
          items: [
            const DropdownMenuItem(value: null, child: Text('—')),
            for (final s in _sexes) DropdownMenuItem(value: s, child: Text(s)),
          ],
          onChanged: (v) => setState(() => _sex = v),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _details,
          minLines: 2,
          maxLines: 4,
          decoration: InputDecoration(
            labelText: 'Descrição',
            hintText: 'Ex.: menina de 5 a 10 anos, tom doce e animado',
            suffixIcon: DictationButton(controller: _details),
          ),
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            if (_editingId != null)
              TextButton(onPressed: _resetForm, child: const Text('Cancelar edição')),
            const Spacer(),
            FilledButton(
              onPressed: _saving ? null : _save,
              child: Text(_saving ? 'Salvando…' : (_editingId == null ? 'Salvar voz' : 'Atualizar voz')),
            ),
          ],
        ),
        const SizedBox(height: 24),
        const Eyebrow('CATÁLOGO · NARRAÇÃO'),
        const SizedBox(height: 8),
        if (saved.isEmpty)
          const Text('Nenhuma voz salva ainda.', style: TextStyle(color: SumiColors.ink3)),
        for (final v in saved)
          ListTile(
            contentPadding: EdgeInsets.zero,
            title: Text(v.name),
            subtitle: Text([v.meta, v.details ?? ''].where((s) => s.isNotEmpty).join(' · ')),
            onTap: () => _editSaved(v),
            trailing: IconButton(icon: const Icon(Icons.delete_outline), onPressed: () => _remove(v)),
          ),
      ],
    );
  }
}
