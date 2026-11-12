import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../production/jobs.dart';
import 'character.dart';

abstract class CharactersRepository {
  Future<List<Character>> list();
  Future<Character> create(Map<String, dynamic> body);
  Future<Character> update(String id, Map<String, dynamic> patch);
  Future<List<AttrGroup>> options();
  Future<Job> startPortrait(Map<String, dynamic> body);
  Future<Job> portraitJob(String jobId);
  Future<void> deleteUnused(List<String> ids);
}

class ApiCharactersRepository implements CharactersRepository {
  final Dio _dio;
  ApiCharactersRepository(this._dio);

  Character _character(Response resp) =>
      Character.fromJson((resp.data as Map).cast<String, dynamic>());

  @override
  Future<List<Character>> list() async {
    final resp = await _dio.get('/characters');
    return (resp.data as List)
        .map((e) => Character.fromJson((e as Map).cast<String, dynamic>()))
        .toList();
  }

  @override
  Future<Character> create(Map<String, dynamic> body) async =>
      _character(await _dio.post('/characters', data: body));

  @override
  Future<Character> update(String id, Map<String, dynamic> patch) async =>
      _character(await _dio.patch('/characters/$id', data: patch));

  @override
  Future<List<AttrGroup>> options() async {
    final resp = await _dio.get('/character-options');
    return (resp.data as List)
        .map((e) => AttrGroup.fromJson((e as Map).cast<String, dynamic>()))
        .toList();
  }

  @override
  Future<Job> startPortrait(Map<String, dynamic> body) async {
    final resp = await _dio.post('/characters/generate-portrait', data: body);
    return Job.fromJson((resp.data as Map).cast<String, dynamic>());
  }

  @override
  Future<Job> portraitJob(String jobId) async {
    final resp =
        await _dio.get('/characters/portrait-job/$jobId', options: Options(extra: silent));
    return Job.fromJson((resp.data as Map).cast<String, dynamic>());
  }

  @override
  Future<void> deleteUnused(List<String> ids) =>
      _dio.post('/characters/delete-unused', data: {'ids': ids});
}

final charactersRepositoryProvider = Provider<CharactersRepository>(
    (ref) => ApiCharactersRepository(ref.read(apiClientProvider)));
