import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import '../../../core/theme/app_theme.dart';
import '../candidate_picker.dart';
import '../jobs.dart';
import '../poll_job.dart';
import '../scenario.dart';
import '../scenarios_repository.dart';

final scenarioOptionsProvider =
    FutureProvider<List<AttrGroup>>((ref) => ref.read(scenariosRepositoryProvider).options());

/// Criar ou editar cenário com geração de imagem (regras de scenarios-screen.component.ts).
class ScenarioForm extends ConsumerStatefulWidget {
  final Scenario? scenario;
  final String style;
  final String colorMode;
  final ValueChanged<Scenario> onSaved;

  const ScenarioForm({
    super.key,
    this.scenario,
    required this.style,
    required this.colorMode,
    required this.onSaved,
  });

  @override
  ConsumerState<ScenarioForm> createState() => _ScenarioFormState();
}

class _ScenarioFormState extends ConsumerState<ScenarioForm> {
  late final _name = TextEditingController(text: widget.scenario?.name ?? '');
  late final _kind = TextEditingController(text: widget.scenario?.kind ?? '');
  late final _summary = TextEditingController(text: widget.scenario?.summary ?? '');
  late final _details = TextEditingController(text: widget.scenario?.details ?? '');
  late String? _location = widget.scenario?.locationType;
  late String? _time = widget.scenario?.timeOfDay;
  late String? _weather = widget.scenario?.weather;
  late String? _atmosphere = widget.scenario?.atmosphere;

  bool _generating = false;
  bool _saving = false;
  String _error = '';
  List<ImageCandidate> _candidates = [];
  String? _pickedId;
  JobPoller? _poller;

  bool get _isEdit => widget.scenario != null;

  @override
  void initState() {
    super.initState();
    _name.addListener(() => setState(() {}));
  }

  @override
  void dispose() {
    _poller?.cancel();
    for (final c in [_name, _kind, _summary, _details]) {
      c.dispose();
    }
    super.dispose();
  }

  String? _text(TextEditingController c) => c.text.trim().isEmpty ? null : c.text.trim();

  Map<String, dynamic> _fields() => {
        'name': _name.text.trim(),
        'kind': _text(_kind) ?? 'Cenário',
        'summary': _text(_summary),
        'details': _text(_details),
        'location_type': _location,
        'time_of_day': _time,
        'weather': _weather,
        'atmosphere': _atmosphere,
      };

  Future<void> _generate() async {
    if (_generating) return;
    if (_name.text.trim().isEmpty) {
      setState(() => _error = 'Informe o nome antes de gerar.');
      return;
    }
    if (_isEdit && widget.scenario!.projectCount > 0 && !await _confirmRegen()) return;

    setState(() {
      _generating = true;
      _error = '';
      _candidates = [];
      _pickedId = null;
    });
    final repo = ref.read(scenariosRepositoryProvider);
    try {
      if (_isEdit) await repo.update(widget.scenario!.id, _fields());
      final job = await repo.startScene({
        'style': widget.style,
        'color_mode': widget.colorMode,
        'location': _location,
        'time_of_day': _time,
        'weather': _weather,
        'atmosphere': _atmosphere,
        'extra': _text(_details) ?? _text(_summary),
        'raw': false,
      });
      _poller?.cancel();
      _poller = JobPoller(
        fetch: () => repo.sceneJob(job.jobId),
        onUpdate: (j) {
          if (!mounted || !j.isFinished) return;
          setState(() {
            _generating = false;
            if (j.isError) {
              _error = j.detail.isEmpty ? 'Erro ao gerar cenários.' : j.detail;
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
          title: const Text('Regerar cenário?'),
          content: Text('Este cenário já aparece em ${widget.scenario!.projectCount} projeto(s).'),
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
    final repo = ref.read(scenariosRepositoryProvider);
    final picked = _candidates.where((c) => c.id == _pickedId).firstOrNull;
    final body = {..._fields(), if (picked != null) 'image_url': picked.url};
    try {
      final saved = _isEdit
          ? await repo.update(widget.scenario!.id, body)
          : await repo.create({...body, 'style': widget.style});
      widget.onSaved(saved);
    } catch (_) {
      if (mounted) setState(() => _saving = false);
    }
  }

  Widget _dropdown(AttrGroup? group, String label, String? value, ValueChanged<String?> onChanged) {
    final options = group?.options ?? const <AttrOption>[];
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: DropdownButtonFormField<String?>(
        key: ValueKey('dd-${options.any((o) => o.id == value) ? value : null}'),
        initialValue: options.any((o) => o.id == value) ? value : null,
        isExpanded: true,
        decoration: InputDecoration(labelText: label),
        items: [
          const DropdownMenuItem(value: null, child: Text('—')),
          for (final o in options) DropdownMenuItem(value: o.id, child: Text(o.label)),
        ],
        onChanged: onChanged,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final groups = ref.watch(scenarioOptionsProvider).valueOrNull ?? const [];
    AttrGroup? group(String id) => groups.where((g) => g.id == id).firstOrNull;
    final currentImage = widget.scenario?.imageUrl;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (currentImage != null && _candidates.isEmpty)
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: Image.network(fileUrl(currentImage), height: 180, fit: BoxFit.cover),
          ),
        const SizedBox(height: 12),
        TextField(controller: _name, decoration: const InputDecoration(labelText: 'Nome do cenário')),
        const SizedBox(height: 12),
        TextField(
            controller: _kind,
            decoration: const InputDecoration(labelText: 'Tipo', hintText: 'Cenário')),
        const SizedBox(height: 12),
        _dropdown(group('location'), 'Local', _location, (v) => setState(() => _location = v)),
        _dropdown(group('time_of_day'), 'Hora do dia', _time, (v) => setState(() => _time = v)),
        _dropdown(group('weather'), 'Clima', _weather, (v) => setState(() => _weather = v)),
        _dropdown(group('atmosphere'), 'Atmosfera', _atmosphere,
            (v) => setState(() => _atmosphere = v)),
        TextField(
          controller: _summary,
          minLines: 2,
          maxLines: 4,
          decoration: const InputDecoration(labelText: 'Resumo', alignLabelWithHint: true),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _details,
          minLines: 2,
          maxLines: 4,
          decoration: const InputDecoration(labelText: 'Detalhes visuais', alignLabelWithHint: true),
        ),
        const SizedBox(height: 20),
        if (_generating)
          const GeneratingNotice('Gerando cenários…')
        else
          OutlinedButton.icon(
            onPressed: _generate,
            icon: const Icon(Icons.auto_awesome),
            label: Text(_isEdit ? 'Regerar imagem' : 'Gerar imagem'),
          ),
        if (_error.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(top: 8),
            child: Text(_error, style: const TextStyle(color: SumiColors.danger)),
          ),
        if (_candidates.isNotEmpty) ...[
          const SizedBox(height: 16),
          CandidatePicker(
            title: 'ESCOLHA A IMAGEM',
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
            child: Text(_saving ? 'Salvando…' : (_isEdit ? 'Salvar alterações' : 'Criar cenário')),
          ),
        ),
      ],
    );
  }
}
