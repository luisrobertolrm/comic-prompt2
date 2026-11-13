import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_theme.dart';
import 'delete_project_dialog.dart';
import 'production_draft.dart';
import 'production_step.dart';

/// Moldura das etapas: título da HQ, barra de etapas e exclusão do projeto.
class ProductionScaffold extends ConsumerWidget {
  final String? projectId;
  final ProductionStep step;
  final Widget child;

  const ProductionScaffold({
    super.key,
    required this.projectId,
    required this.step,
    required this.child,
  });

  void _leave(BuildContext context) {
    if (context.canPop()) {
      context.pop();
    } else {
      context.go('/');
    }
  }

  void _back(BuildContext context) {
    if (step == ProductionStep.idea || projectId == null) {
      _leave(context);
      return;
    }
    context.go(ProductionStep.values[step.index - 1].location(projectId!));
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final title = ref.watch(productionDraftProvider).title;
    final furthest = projectId == null
        ? ProductionStep.idea
        : ref.watch(furthestStepProvider(projectId!)).valueOrNull ?? step;

    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) _back(context);
      },
      child: Scaffold(
        appBar: AppBar(
          leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => _back(context)),
          title: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Eyebrow('HQ ATUAL'),
              Text(title.isEmpty ? 'Novo projeto' : title,
                  maxLines: 1, overflow: TextOverflow.ellipsis),
            ],
          ),
          actions: [
            IconButton(
              tooltip: 'Fechar',
              icon: const Icon(Icons.close),
              onPressed: () => context.go('/'),
            ),
            if (projectId != null)
              PopupMenuButton<String>(
                onSelected: (_) => showDeleteProjectDialog(context, ref, projectId!, title),
                itemBuilder: (_) => const [
                  PopupMenuItem(
                    value: 'delete',
                    child: Text('Excluir projeto', style: TextStyle(color: SumiColors.danger)),
                  ),
                ],
              ),
          ],
          bottom: PreferredSize(
            preferredSize: const Size.fromHeight(48),
            child: _StepBar(
              current: step,
              furthest: furthest.index > step.index ? furthest : step,
              onTap: projectId == null ? null : (s) => context.go(s.location(projectId!)),
            ),
          ),
        ),
        body: child,
      ),
    );
  }
}

class _StepBar extends StatelessWidget {
  final ProductionStep current;
  final ProductionStep furthest;
  final ValueChanged<ProductionStep>? onTap;

  const _StepBar({required this.current, required this.furthest, required this.onTap});

  @override
  Widget build(BuildContext context) => SizedBox(
        height: 48,
        child: ListView(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          children: [
            for (final s in ProductionStep.values) _chip(s),
          ],
        ),
      );

  Widget _chip(ProductionStep s) {
    final isCurrent = s == current;
    final done = s.index < furthest.index;
    final reachable = onTap != null && !isCurrent && isStepReachable(s, furthest);
    return Padding(
      padding: const EdgeInsets.only(right: 6),
      child: ActionChip(
        onPressed: reachable ? () => onTap!(s) : null,
        backgroundColor: isCurrent ? SumiColors.ink : Colors.white,
        disabledColor: isCurrent ? SumiColors.ink : SumiColors.paper2,
        side: const BorderSide(color: SumiColors.rule),
        label: Text(
          '${done && !isCurrent ? '✓' : '${s.index + 1}'}  ${s.label}',
          style: TextStyle(
            fontSize: 12,
            color: isCurrent
                ? SumiColors.paper
                : reachable
                    ? SumiColors.ink
                    : SumiColors.ink4,
          ),
        ),
      ),
    );
  }
}
