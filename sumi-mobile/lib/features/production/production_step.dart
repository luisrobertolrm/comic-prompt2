import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../projects/project.dart';
import '../projects/projects_repository.dart';
import 'panel.dart';
import 'panels_repository.dart';

enum ProductionStep {
  idea('Ideia', 'idea'),
  characters('Personagens', 'characters'),
  scenarios('Cenários', 'scenarios'),
  script('Roteiro', 'script'),
  review('Revisão', 'review'),
  editor('Editor', 'editor'),
  finalize('Finalizar', 'finalize'),
  video('Vídeo', 'video');

  final String label;
  final String slug;
  const ProductionStep(this.label, this.slug);

  String get path => '/production/:id/$slug';
  String location(String projectId) => '/production/$projectId/$slug';
}

/// Etapa de abertura: só se pula para uma etapa se todas as anteriores já foram feitas
/// (regra em specs/001-mobile-app-menus/data-model.md).
ProductionStep stepFor(Project detail, List<Panel> panels) {
  if (detail.videoUrl != null && detail.videoUrl!.isNotEmpty) return ProductionStep.video;
  if (panels.isNotEmpty && panels.every((p) => p.hasImage)) return ProductionStep.editor;
  if (panels.isNotEmpty) return ProductionStep.review;
  if (detail.scenarios.isNotEmpty) return ProductionStep.script;
  if (detail.characters.isNotEmpty) return ProductionStep.scenarios;
  return ProductionStep.characters;
}

/// Editor e Finalizar não deixam rastro nos dados: depois da Revisão, todas as etapas
/// ficam liberadas.
bool isStepReachable(ProductionStep step, ProductionStep furthest) =>
    furthest.index >= ProductionStep.editor.index || step.index <= furthest.index;

final furthestStepProvider =
    FutureProvider.autoDispose.family<ProductionStep, String>((ref, projectId) async {
  final results = await Future.wait([
    ref.read(projectsRepositoryProvider).get(projectId),
    ref.read(panelsRepositoryProvider).list(projectId),
  ]);
  return stepFor(results[0] as Project, results[1] as List<Panel>);
});
