import 'dart:math';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/services/notification_service.dart';
import '../../core/theme/app_theme.dart';
import '../projects/projects_repository.dart';
import 'production_draft.dart';

const _codeAlphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';

Future<void> showDeleteProjectDialog(
    BuildContext context, WidgetRef ref, String projectId, String title) async {
  final random = Random();
  final code = List.generate(6, (_) => _codeAlphabet[random.nextInt(_codeAlphabet.length)]).join();
  final deleted = await showDialog<bool>(
    context: context,
    builder: (_) => _DeleteProjectDialog(projectId: projectId, title: title, code: code),
  );
  if (deleted == true && context.mounted) {
    await ref.read(productionDraftProvider.notifier).clear();
    ref.read(notificationServiceProvider).success('Projeto excluído.');
    if (context.mounted) context.go('/');
  }
}

class _DeleteProjectDialog extends ConsumerStatefulWidget {
  final String projectId;
  final String title;
  final String code;

  const _DeleteProjectDialog({required this.projectId, required this.title, required this.code});

  @override
  ConsumerState<_DeleteProjectDialog> createState() => _DeleteProjectDialogState();
}

class _DeleteProjectDialogState extends ConsumerState<_DeleteProjectDialog> {
  String _input = '';
  bool _deleting = false;

  bool get _canConfirm => _input.trim().toUpperCase() == widget.code && !_deleting;

  Future<void> _confirm() async {
    setState(() => _deleting = true);
    try {
      await ref.read(projectsRepositoryProvider).delete(widget.projectId);
      if (mounted) Navigator.of(context).pop(true);
    } catch (_) {
      if (mounted) setState(() => _deleting = false);
    }
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
        icon: const Icon(Icons.warning_amber_rounded, color: SumiColors.danger),
        title: const Text('Excluir projeto'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text.rich(TextSpan(children: [
              const TextSpan(text: 'Esta ação é '),
              const TextSpan(text: 'permanente', style: TextStyle(fontWeight: FontWeight.bold)),
              TextSpan(
                  text: '. O projeto “${widget.title.isEmpty ? 'sem título' : widget.title}” e '),
              const TextSpan(
                  text: 'todas as imagens', style: TextStyle(fontWeight: FontWeight.bold)),
              const TextSpan(text: ' geradas serão apagados e não poderão ser recuperados.'),
            ])),
            const SizedBox(height: 16),
            const Text('Para confirmar, digite o código abaixo:'),
            const SizedBox(height: 8),
            Center(
              child: SelectableText(widget.code,
                  style: const TextStyle(
                      fontFamily: monoFamily, fontSize: 22, letterSpacing: 4, fontWeight: FontWeight.bold)),
            ),
            const SizedBox(height: 8),
            TextField(
              autocorrect: false,
              textCapitalization: TextCapitalization.characters,
              decoration: const InputDecoration(hintText: 'Digite o código'),
              onChanged: (v) => setState(() => _input = v),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: _deleting ? null : () => Navigator.of(context).pop(false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
                backgroundColor: SumiColors.danger, foregroundColor: Colors.white),
            onPressed: _canConfirm ? _confirm : null,
            child: Text(_deleting ? 'Excluindo…' : 'Excluir definitivamente'),
          ),
        ],
      );
}
