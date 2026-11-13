import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/services/text_organizer_service.dart';

/// Botão para o `suffixIcon` de um campo: a IA organiza o texto (pontuação,
/// parágrafos) sem acrescentar conteúdo. Oferece "Desfazer" no snackbar.
class OrganizeButton extends ConsumerStatefulWidget {
  const OrganizeButton({super.key, required this.controller});

  final TextEditingController controller;

  @override
  ConsumerState<OrganizeButton> createState() => _OrganizeButtonState();
}

class _OrganizeButtonState extends ConsumerState<OrganizeButton> {
  bool _busy = false;

  Future<void> _organize() async {
    final original = widget.controller.text;
    if (original.trim().length < 3) return;
    setState(() => _busy = true);
    try {
      final organized = await ref.read(textOrganizerServiceProvider).organize(original);
      if (!mounted || organized.isEmpty || organized == original) return;
      widget.controller.value = TextEditingValue(
        text: organized,
        selection: TextSelection.collapsed(offset: organized.length),
      );
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: const Text('Texto organizado.'),
        action: SnackBarAction(
          label: 'Desfazer',
          onPressed: () => widget.controller.text = original,
        ),
      ));
    } catch (_) {
      // O interceptor do Dio já exibiu a mensagem de erro.
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_busy) {
      return const Padding(
        padding: EdgeInsets.all(14),
        child: SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)),
      );
    }
    return IconButton(
      icon: const Icon(Icons.auto_fix_high),
      tooltip: 'Organizar texto',
      onPressed: _organize,
    );
  }
}
