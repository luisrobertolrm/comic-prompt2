import 'package:flutter/material.dart';

import '../core/api/api_client.dart';
import '../core/theme/app_theme.dart';
import 'dictation_button.dart';

/// Descrição livre (digitada ou ditada) que a IA quebra nos campos de um
/// formulário. [interpret] devolve o rascunho, ou null e a mensagem explicando
/// o que faltou.
class AiDraftDialog<T> extends StatefulWidget {
  const AiDraftDialog({
    super.key,
    required this.hint,
    required this.fallbackMessage,
    required this.interpret,
  });

  final String hint;
  final String fallbackMessage;
  final Future<(T?, String)> Function(String text) interpret;

  @override
  State<AiDraftDialog<T>> createState() => _AiDraftDialogState<T>();
}

class _AiDraftDialogState<T> extends State<AiDraftDialog<T>> {
  final _text = TextEditingController();
  bool _busy = false;
  String _message = '';

  @override
  void initState() {
    super.initState();
    _text.addListener(() => setState(() {}));
  }

  @override
  void dispose() {
    _text.dispose();
    super.dispose();
  }

  Future<void> _generate() async {
    setState(() {
      _busy = true;
      _message = '';
    });
    try {
      final (draft, message) = await widget.interpret(_text.text.trim());
      if (!mounted) return;
      if (draft != null) {
        Navigator.pop(context, draft);
        return;
      }
      setState(() => _message = message.isEmpty ? widget.fallbackMessage : message);
    } catch (e) {
      if (mounted) setState(() => _message = friendlyError(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Gerar por IA'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              controller: _text,
              minLines: 4,
              maxLines: 10,
              maxLength: 4000,
              decoration: InputDecoration(
                hintText: widget.hint,
                suffixIcon: DictationButton(controller: _text),
              ),
            ),
            if (_message.isNotEmpty)
              Text(_message, style: const TextStyle(color: SumiColors.danger)),
          ],
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')),
        FilledButton.icon(
          onPressed: _busy || _text.text.trim().length < 3 ? null : _generate,
          icon: _busy
              ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
              : const Icon(Icons.auto_awesome),
          label: Text(_busy ? 'Interpretando…' : 'Preencher'),
        ),
      ],
    );
  }
}
