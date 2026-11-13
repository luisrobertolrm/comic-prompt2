import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../production/candidate_picker.dart';
import '../production/jobs.dart';
import '../production/poll_job.dart';
import '../voice_test/voices_repository.dart';
import 'character.dart';
import 'characters_repository.dart';
import '../../shared/dictation_button.dart';

const genders = ['Feminino', 'Masculino', 'Outro', 'Não especificado'];

/// Criar ou editar personagem com geração de retrato (mesmas regras de
/// manual-tab e do modal de edição de `characters-screen.component.ts`).
class CharacterForm extends ConsumerStatefulWidget {
  final Character? character;
  final String style;
  final String colorMode;
  final ValueChanged<Character> onSaved;

  const CharacterForm({
    super.key,
    this.character,
    required this.style,
    required this.colorMode,
    required this.onSaved,
  });

  @override
  ConsumerState<CharacterForm> createState() => _CharacterFormState();
}

class _CharacterFormState extends ConsumerState<CharacterForm> {
  late final _name = TextEditingController(text: widget.character?.name ?? '');
  late final _role = TextEditingController(text: widget.character?.role ?? 'Protagonista');
  late final _age = TextEditingController(text: widget.character?.age?.toString() ?? '16');
  late final _height = TextEditingController(text: widget.character?.height ?? '');
  late final _summary = TextEditingController(text: widget.character?.summary ?? '');
  late final _outfit = TextEditingController(text: widget.character?.outfit ?? '');
  late final _traits = TextEditingController(text: widget.character?.traits.join(', ') ?? '');
  late String? _gender = widget.character?.gender;
  late String? _voiceId = widget.character?.narratorVoiceId;

  bool _generating = false;
  bool _saving = false;
  String _error = '';
  List<ImageCandidate> _candidates = [];
  String? _pickedId;
  JobPoller? _poller;

  bool get _isEdit => widget.character != null;

  @override
  void initState() {
    super.initState();
    for (final c in [_name, _role, _age, _height, _summary, _outfit, _traits]) {
      c.addListener(() => setState(() {}));
    }
  }

  @override
  void dispose() {
    _poller?.cancel();
    for (final c in [_name, _role, _age, _height, _summary, _outfit, _traits]) {
      c.dispose();
    }
    super.dispose();
  }

  bool get _complete => [_name, _role, _age, _height, _summary, _outfit, _traits]
          .every((c) => c.text.trim().isNotEmpty) &&
      _gender != null;

  bool get _canGenerate => _isEdit ? _summary.text.trim().isNotEmpty : _complete;

  String _buildPrompt() => [
        _name.text.trim(),
        _role.text.trim(),
        if (_age.text.trim().isNotEmpty) '${_age.text.trim()} anos',
        if (_height.text.trim().isNotEmpty) 'altura ${_height.text.trim()}',
        _summary.text.trim(),
        if (_outfit.text.trim().isNotEmpty) 'figurino: ${_outfit.text.trim()}',
        if (_traits.text.trim().isNotEmpty) 'personalidade: ${_traits.text.trim()}',
      ].where((s) => s.isNotEmpty).join(', ');

  Map<String, dynamic> _fields() => {
        'name': _name.text.trim(),
        'role': _role.text.trim().isEmpty ? 'Personagem' : _role.text.trim(),
        'gender': _gender,
        'age': int.tryParse(_age.text.trim()),
        'height': _height.text.trim().isEmpty ? null : _height.text.trim(),
        'summary': _summary.text.trim().isEmpty ? null : _summary.text.trim(),
        'outfit': _outfit.text.trim().isEmpty ? null : _outfit.text.trim(),
        'traits': _traits.text.split(',').map((t) => t.trim()).where((t) => t.isNotEmpty).toList(),
        'narrator_voice_id': _voiceId,
      };

  Future<void> _generate() async {
    if (!_canGenerate || _generating) return;
    if (_name.text.trim().isEmpty) {
      setState(() => _error = 'Informe o nome antes de gerar.');
      return;
    }
    if (_isEdit && widget.character!.projectCount > 0 && !await _confirmRegen()) return;

    setState(() {
      _generating = true;
      _error = '';
      _candidates = [];
      _pickedId = null;
    });
    final repo = ref.read(charactersRepositoryProvider);
    try {
      if (_isEdit) await repo.update(widget.character!.id, _fields());
      final job = await repo.startPortrait({
        'style': widget.style,
        'color_mode': widget.colorMode,
        'gender': _gender,
        'extra': _isEdit ? _summary.text.trim() : _buildPrompt(),
        'raw': false,
      });
      _poller?.cancel();
      _poller = JobPoller(
        fetch: () => repo.portraitJob(job.jobId),
        onUpdate: (j) {
          if (!mounted || !j.isFinished) return;
          setState(() {
            _generating = false;
            if (j.isError) {
              _error = j.detail.isEmpty ? 'Erro ao gerar retratos.' : j.detail;
            } else {
              _candidates = j.candidates;
            }
          });
        },
      );
    } catch (e) {
      if (mounted) {
        setState(() {
          _generating = false;
          _error = friendlyError(e);
        });
      }
    }
  }

  Future<bool> _confirmRegen() async =>
      await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Regerar retrato?'),
          content: Text('Este personagem já aparece em ${widget.character!.projectCount} '
              'projeto(s). Um novo retrato muda a aparência dele nas próximas gerações.'),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(context, false), child: const Text('Cancelar')),
            FilledButton(
                onPressed: () => Navigator.pop(context, true),
                child: const Text('Regerar mesmo assim')),
          ],
        ),
      ) ??
      false;

  Future<void> _save() async {
    if (_name.text.trim().isEmpty || _saving) return;
    setState(() => _saving = true);
    final repo = ref.read(charactersRepositoryProvider);
    final picked = _candidates.where((c) => c.id == _pickedId).firstOrNull;
    final body = {
      ..._fields(),
      // URL como veio da API (relativa): o web resolve contra a própria base.
      if (picked != null) 'image_url': picked.url,
    };
    try {
      final saved = _isEdit
          ? await repo.update(widget.character!.id, body)
          : await repo.create({...body, 'style': widget.style});
      widget.onSaved(saved);
    } catch (_) {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final voices = ref.watch(savedVoicesProvider).valueOrNull ?? const [];
    final currentImage = widget.character?.imageUrl;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (currentImage != null && _candidates.isEmpty)
          Center(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: Image.network(fileUrl(currentImage), height: 180, fit: BoxFit.cover),
            ),
          ),
        TextField(controller: _name, decoration: const InputDecoration(labelText: 'Nome do personagem')),
        const SizedBox(height: 12),
        DropdownButtonFormField<String>(
          key: ValueKey('dd-${genders.contains(_gender) ? _gender : null}'),
          initialValue: genders.contains(_gender) ? _gender : null,
          decoration: const InputDecoration(labelText: 'Gênero'),
          hint: const Text('Selecione…'),
          items: [for (final g in genders) DropdownMenuItem(value: g, child: Text(g))],
          onChanged: (v) => setState(() => _gender = v),
        ),
        const SizedBox(height: 12),
        TextField(controller: _role, decoration: const InputDecoration(labelText: 'Papel')),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _age,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: 'Idade'),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: TextField(
                controller: _height,
                decoration: const InputDecoration(labelText: 'Altura', hintText: '1.60 m'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _summary,
          minLines: 2,
          maxLines: 5,
          decoration: InputDecoration(
              labelText: 'Descrição visual',
              alignLabelWithHint: true,
              suffixIcon: DictationButton(controller: _summary)),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _outfit,
          minLines: 1,
          maxLines: 3,
          decoration: const InputDecoration(labelText: 'Figurino padrão'),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _traits,
          decoration: const InputDecoration(
              labelText: 'Traços de personalidade', helperText: 'Separe por vírgula.'),
        ),
        const SizedBox(height: 12),
        DropdownButtonFormField<String?>(
          key: ValueKey('dd-${voices.any((v) => v.id == _voiceId) ? _voiceId : null}'),
          initialValue: voices.any((v) => v.id == _voiceId) ? _voiceId : null,
          isExpanded: true,
          decoration: const InputDecoration(labelText: 'Voz do personagem'),
          items: [
            const DropdownMenuItem(value: null, child: Text('— Sem voz —')),
            for (final v in voices)
              DropdownMenuItem(
                  value: v.id, child: Text(v.meta.isEmpty ? v.name : '${v.name} · ${v.meta}')),
          ],
          onChanged: (v) => setState(() => _voiceId = v),
        ),
        const SizedBox(height: 20),
        if (_generating)
          const GeneratingNotice('Gerando retratos…')
        else
          OutlinedButton.icon(
            onPressed: _canGenerate ? _generate : null,
            icon: const Icon(Icons.auto_awesome),
            label: Text(_isEdit ? 'Regerar retrato' : 'Gerar retrato'),
          ),
        if (!_isEdit && !_complete && !_generating)
          const Padding(
            padding: EdgeInsets.only(top: 6),
            child: Text('Preencha todos os campos para gerar o retrato.',
                style: TextStyle(fontSize: 12, color: SumiColors.ink3)),
          ),
        if (_error.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(top: 8),
            child: Text(_error, style: const TextStyle(color: SumiColors.danger)),
          ),
        if (_candidates.isNotEmpty) ...[
          const SizedBox(height: 16),
          CandidatePicker(
            title: _isEdit ? 'ESCOLHA O NOVO RETRATO' : 'ESCOLHA O RETRATO',
            candidates: _candidates,
            pickedId: _pickedId,
            onPick: (id) => setState(() => _pickedId = id),
          ),
        ],
        const SizedBox(height: 20),
        FilledButton(
          onPressed: _name.text.trim().isEmpty || _saving ? null : _save,
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 12),
            child: Text(_saving ? 'Salvando…' : (_isEdit ? 'Salvar alterações' : 'Criar personagem')),
          ),
        ),
      ],
    );
  }
}
