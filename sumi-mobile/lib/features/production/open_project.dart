import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../projects/project.dart';
import 'production_draft.dart';
import 'production_step.dart';

Future<void> openProject(BuildContext context, WidgetRef ref, Project project) async {
  await ref.read(productionDraftProvider.notifier).open(project.id, project.title);
  try {
    final step = await ref.refresh(furthestStepProvider(project.id).future);
    if (context.mounted) context.push(step.location(project.id));
  } catch (_) {
    // O interceptor já mostrou o erro.
  }
}

Future<void> startNewProject(BuildContext context, WidgetRef ref) async {
  await ref.read(productionDraftProvider.notifier).clear();
  if (context.mounted) context.push('/production/new/idea');
}
