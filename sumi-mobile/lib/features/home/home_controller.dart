import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../library/character.dart';
import '../library/characters_repository.dart';
import '../projects/project.dart';
import '../projects/projects_repository.dart';

const projectStatuses = ['Todos', 'Rascunho', 'Roteiro', 'Em revisão', 'Concluído'];

class HomeData {
  final List<Project> projects;
  final List<Character> recentCharacters;
  const HomeData(this.projects, this.recentCharacters);
}

final homeDataProvider = FutureProvider.autoDispose<HomeData>((ref) async {
  final results = await Future.wait([
    ref.read(projectsRepositoryProvider).list(),
    ref.read(charactersRepositoryProvider).list(),
  ]);
  final characters = results[1] as List<Character>;
  return HomeData(results[0] as List<Project>, characters.take(8).toList());
});

List<Project> filterByStatus(List<Project> projects, String status) =>
    status == 'Todos' ? projects : projects.where((p) => p.status == status).toList();
