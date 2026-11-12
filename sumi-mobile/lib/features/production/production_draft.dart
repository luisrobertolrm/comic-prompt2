import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/storage/secure_storage.dart';

class ProductionDraft {
  final String? projectId;
  final String title;
  const ProductionDraft({this.projectId, this.title = ''});
}

/// Projeto em produção (equivalente ao project-draft.service.ts do web).
final productionDraftProvider =
    NotifierProvider<ProductionDraftNotifier, ProductionDraft>(ProductionDraftNotifier.new);

class ProductionDraftNotifier extends Notifier<ProductionDraft> {
  @override
  ProductionDraft build() => const ProductionDraft();

  Future<void> open(String projectId, String title) async {
    state = ProductionDraft(projectId: projectId, title: title);
    await ref.read(secureStorageProvider).saveDraftProjectId(projectId);
  }

  void setTitle(String title) => state = ProductionDraft(projectId: state.projectId, title: title);

  Future<void> clear() async {
    state = const ProductionDraft();
    await ref.read(secureStorageProvider).saveDraftProjectId(null);
  }
}
