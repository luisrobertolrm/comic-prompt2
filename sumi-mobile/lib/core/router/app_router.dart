import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/auth/login_screen.dart';
import '../../features/home/home_screen.dart';
import '../../features/library/character_edit_screen.dart';
import '../../features/library/library_screen.dart';
import '../../features/production/characters/characters_step_screen.dart';
import '../../features/production/editor/editor_screen.dart';
import '../../features/production/finalize/finalize_screen.dart';
import '../../features/production/idea/idea_screen.dart';
import '../../features/production/production_scaffold.dart';
import '../../features/production/production_step.dart';
import '../../features/production/review/review_screen.dart';
import '../../features/production/scenarios/scenarios_step_screen.dart';
import '../../features/production/script/script_screen.dart';
import '../../features/production/video/video_screen.dart';
import '../../features/projects/projects_screen.dart';
import '../../features/series/series_screen.dart';
import '../../features/shell/shell_scaffold.dart';
import '../../features/voice_test/voice_test_screen.dart';
import '../auth/auth_provider.dart';

class _AuthListenable extends ChangeNotifier {
  _AuthListenable(Ref ref) {
    ref.listen(authProvider, (_, _) => notifyListeners());
  }
}

GoRoute _step(ProductionStep step, Widget Function(String projectId) screen) => GoRoute(
      path: step.path,
      builder: (context, state) {
        final id = state.pathParameters['id']!;
        return ProductionScaffold(projectId: id, step: step, child: screen(id));
      },
    );

final appRouterProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/splash',
    refreshListenable: _AuthListenable(ref),
    redirect: (context, state) {
      final auth = ref.read(authProvider);
      final location = state.matchedLocation;
      if (auth.loading) return location == '/splash' ? null : '/splash';
      if (!auth.isAuthenticated) return location == '/login' ? null : '/login';
      if (location == '/login' || location == '/splash') return '/';
      return null;
    },
    routes: [
      GoRoute(
        path: '/splash',
        builder: (_, _) => const Scaffold(body: Center(child: CircularProgressIndicator())),
      ),
      GoRoute(path: '/login', builder: (_, _) => const LoginScreen()),
      ShellRoute(
        builder: (context, state, child) =>
            ShellScaffold(location: state.matchedLocation, child: child),
        routes: [
          GoRoute(path: '/', builder: (_, _) => const HomeScreen()),
          GoRoute(path: '/projects', builder: (_, _) => const ProjectsScreen()),
          GoRoute(
            path: '/library',
            builder: (_, _) => const LibraryScreen(),
            routes: [
              GoRoute(path: 'new', builder: (_, _) => const CharacterEditScreen()),
              GoRoute(
                path: ':cid',
                builder: (_, state) =>
                    CharacterEditScreen(characterId: state.pathParameters['cid']),
              ),
            ],
          ),
          GoRoute(path: '/series', builder: (_, _) => const SeriesScreen()),
          GoRoute(path: '/voice-test', builder: (_, _) => const VoiceTestScreen()),
        ],
      ),
      GoRoute(
        path: '/production/new/idea',
        builder: (_, _) => const ProductionScaffold(
            projectId: null, step: ProductionStep.idea, child: IdeaScreen(projectId: null)),
      ),
      _step(ProductionStep.idea, (id) => IdeaScreen(projectId: id)),
      _step(ProductionStep.characters, (id) => CharactersStepScreen(projectId: id)),
      _step(ProductionStep.scenarios, (id) => ScenariosStepScreen(projectId: id)),
      _step(ProductionStep.script, (id) => ScriptScreen(projectId: id)),
      _step(ProductionStep.review, (id) => ReviewScreen(projectId: id)),
      _step(ProductionStep.editor, (id) => EditorScreen(projectId: id)),
      _step(ProductionStep.finalize, (id) => FinalizeScreen(projectId: id)),
      _step(ProductionStep.video, (id) => VideoScreen(projectId: id)),
    ],
  );
});
