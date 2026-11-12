import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import 'series.dart';

abstract class SeriesRepository {
  Future<List<Series>> list();
  Future<Series> create(String name, String? description);
  Future<Series> update(String id, String name, String? description);
  Future<void> delete(String id);
  Future<void> setProjects(String id, List<String> projectIds);
}

class ApiSeriesRepository implements SeriesRepository {
  final Dio _dio;
  ApiSeriesRepository(this._dio);

  Series _series(Response resp) => Series.fromJson((resp.data as Map).cast<String, dynamic>());

  @override
  Future<List<Series>> list() async {
    final resp = await _dio.get('/series');
    return (resp.data as List)
        .map((e) => Series.fromJson((e as Map).cast<String, dynamic>()))
        .toList();
  }

  @override
  Future<Series> create(String name, String? description) async =>
      _series(await _dio.post('/series', data: {'name': name, 'description': description}));

  @override
  Future<Series> update(String id, String name, String? description) async =>
      _series(await _dio.patch('/series/$id', data: {'name': name, 'description': description}));

  @override
  Future<void> delete(String id) => _dio.delete('/series/$id');

  @override
  Future<void> setProjects(String id, List<String> projectIds) =>
      _dio.put('/series/$id/projects', data: {'project_ids': projectIds});
}

final seriesRepositoryProvider =
    Provider<SeriesRepository>((ref) => ApiSeriesRepository(ref.read(apiClientProvider)));
