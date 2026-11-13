import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/services/dictation_service.dart';
import '../core/services/notification_service.dart';

enum _State { idle, recording, transcribing }

enum _Mode { append, replace }

/// Microfone para o `suffixIcon` de um campo: toque para gravar, toque de novo
/// para transcrever. Com o campo preenchido, pergunta antes se o ditado
/// acrescenta ao fim ou substitui o conteúdo.
class DictationButton extends ConsumerStatefulWidget {
  const DictationButton({super.key, required this.controller, this.onChanged});

  final TextEditingController controller;

  /// Chamado com o novo valor do campo, já que alterar o controller por código
  /// não dispara o `onChanged` do TextField.
  final ValueChanged<String>? onChanged;

  @override
  ConsumerState<DictationButton> createState() => _DictationButtonState();
}

class _DictationButtonState extends ConsumerState<DictationButton> {
  _State _state = _State.idle;
  _Mode _mode = _Mode.append;
  late final DictationService _dictation = ref.read(dictationServiceProvider);

  @override
  void dispose() {
    if (_state == _State.recording) _dictation.cancel();
    super.dispose();
  }

  Future<_Mode?> _askMode() {
    final box = context.findRenderObject() as RenderBox;
    final overlay = Overlay.of(context).context.findRenderObject() as RenderBox;
    final origin = box.localToGlobal(Offset(0, box.size.height), ancestor: overlay);
    return showMenu<_Mode>(
      context: context,
      position: RelativeRect.fromRect(origin & Size.zero, Offset.zero & overlay.size),
      items: const [
        PopupMenuItem(
          value: _Mode.append,
          child: ListTile(leading: Icon(Icons.playlist_add), title: Text('Acrescentar')),
        ),
        PopupMenuItem(
          value: _Mode.replace,
          child: ListTile(leading: Icon(Icons.find_replace), title: Text('Substituir')),
        ),
      ],
    );
  }

  Future<void> _toggle() async {
    switch (_state) {
      case _State.idle:
        if (widget.controller.text.trim().isEmpty) {
          _mode = _Mode.replace;
        } else {
          final mode = await _askMode();
          if (mode == null || !mounted) return;
          _mode = mode;
        }
        if (await _dictation.start()) {
          setState(() => _state = _State.recording);
        } else {
          ref.read(notificationServiceProvider).error('Permissão do microfone negada.');
        }
      case _State.recording:
        setState(() => _state = _State.transcribing);
        try {
          _insert(await _dictation.stopAndTranscribe());
        } catch (_) {
          // O interceptor do Dio já exibiu a mensagem de erro.
        } finally {
          if (mounted) setState(() => _state = _State.idle);
        }
      case _State.transcribing:
        return;
    }
  }

  void _insert(String text) {
    if (text.isEmpty || !mounted) return;
    final c = widget.controller;
    final before = _mode == _Mode.replace ? '' : c.text.trimRight();
    final updated = before.isEmpty ? text : '$before $text';
    c.value = TextEditingValue(
      text: updated,
      selection: TextSelection.collapsed(offset: updated.length),
    );
    widget.onChanged?.call(updated);
  }

  @override
  Widget build(BuildContext context) {
    return switch (_state) {
      _State.idle => IconButton(
          icon: const Icon(Icons.mic_none),
          tooltip: 'Ditar',
          onPressed: _toggle,
        ),
      _State.recording => IconButton(
          icon: const Icon(Icons.stop_circle, color: Colors.red),
          tooltip: 'Parar e transcrever',
          onPressed: _toggle,
        ),
      _State.transcribing => const Padding(
          padding: EdgeInsets.all(14),
          child: SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)),
        ),
    };
  }
}
