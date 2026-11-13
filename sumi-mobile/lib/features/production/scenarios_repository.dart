import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import 'jobs.dart';
import 'scenario.dart';

abstract class ScenariosRepository {
  Future<List<Scenario>> list();
  Future<Scenario> create(Map<String, dynamic> body);
  Future<Scenario> update(String id, Map<String, dynamic> patch);
  Future<List<AttrGroup>> options();
  Future<Job> startScene(Map<String, dynamic> body);
  Future<Job> sceneJob(String jobId);
  Future<void> deleteUnused(List<String> ids);
  Future<ScenarioAiResult> aiDraft(String text);
}

class ApiScenariosRepository implements ScenariosRepository {
  final Dio _dio;
  ApiScenariosRepository(this._dio);

  Scenario _scenario(Response resp) =>
      Scenario.fromJson((resp.data as Map).cast<String, dynamic>());

  @override
  Future<List<Scenario>> list() async {
    final resp = await _dio.get('/scenarios');
    return (resp.data as List)
        .map((e) => Scenario.fromJson((e as Map).cast<String, dynamic>()))
        .toList();
  }

  @override
  Future<Scenario> create(Map<String, dynamic> body) async =>
      _scenario(await _dio.post('/scenarios', data: body));

  @override
  Future<Scenario> update(String id, Map<String, dynamic> patch) async =>
      _scenario(await _dio.patch('/scenarios/$id', data: patch));

  @override
  Future<List<AttrGroup>> options() async {
    final resp = await _dio.get('/scenario-options');
    return (resp.data as List)
        .map((e) => AttrGroup.fromJson((e as Map).cast<String, dynamic>()))
        .toList();
  }

  @override
  Future<Job> startScene(Map<String, dynamic> body) async {
    final resp = await _dio.post('/scenarios/generate-scene', data: body);
    return Job.fromJson((resp.data as Map).cast<String, dynamic>());
  }

  @override
  Future<Job> sceneJob(String jobId) async {
    final resp = await _dio.get('/scenarios/scene-job/$jobId', options: Options(extra: silent));
    return Job.fromJson((resp.data as Map).cast<String, dynamic>());
  }

  @override
  Future<void> deleteUnused(List<String> ids) =>
      _dio.post('/scenarios/delete-unused', data: {'ids': ids});

  @override
  Future<ScenarioAiResult> aiDraft(String text) async {
    final resp = await _dio.post('/scenarios/ai-draft', data: {'text': text});
    return ScenarioAiResult.fromJson((resp.data as Map).cast<String, dynamic>());
  }
}

final scenariosRepositoryProvider =
    Provider<ScenariosRepository>((ref) => ApiScenariosRepository(ref.read(apiClientProvider)));
