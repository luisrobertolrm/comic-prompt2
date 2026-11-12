import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import 'panel.dart';

abstract class PanelsRepository {
  Future<List<Panel>> list(String projectId);
  Future<List<Panel>> generateAll(String projectId, {int? targetPanels});
  Future<Panel> insert(String projectId, int afterIndex);
  Future<List<Panel>> generateAllImages(String projectId);
  Future<void> reorder(String projectId, List<String> panelIds);
  Future<void> deleteMany(String projectId, List<String> panelIds);
  Future<Panel> update(String panelId, Map<String, dynamic> patch);
  Future<void> delete(String panelId);
  Future<Panel> generateContent(String panelId);
  Future<Panel> generateImage(String panelId);
  Future<Panel> generateBubbles(String panelId);
}

class ApiPanelsRepository implements PanelsRepository {
  final Dio _dio;
  ApiPanelsRepository(this._dio);

  Panel _panel(Response resp) => Panel.fromJson((resp.data as Map).cast<String, dynamic>());

  List<Panel> _panels(Response resp) => (resp.data as List)
      .map((e) => Panel.fromJson((e as Map).cast<String, dynamic>()))
      .toList();

  @override
  Future<List<Panel>> list(String projectId) async =>
      _panels(await _dio.get('/projects/$projectId/panels'));

  @override
  Future<List<Panel>> generateAll(String projectId, {int? targetPanels}) async => _panels(
      await _dio.post('/projects/$projectId/panels/generate',
          data: {'target_panels': targetPanels, 'use_local': false}));

  @override
  Future<Panel> insert(String projectId, int afterIndex) async =>
      _panel(await _dio.post('/projects/$projectId/panels', data: {'after_index': afterIndex}));

  @override
  Future<List<Panel>> generateAllImages(String projectId) async =>
      _panels(await _dio.post('/projects/$projectId/panels/generate-images', data: {}));

  @override
  Future<void> reorder(String projectId, List<String> panelIds) =>
      _dio.put('/projects/$projectId/panels/order', data: {'panel_ids': panelIds});

  @override
  Future<void> deleteMany(String projectId, List<String> panelIds) =>
      _dio.post('/projects/$projectId/panels/delete', data: {'panel_ids': panelIds});

  @override
  Future<Panel> update(String panelId, Map<String, dynamic> patch) async =>
      _panel(await _dio.patch('/panels/$panelId', data: patch));

  @override
  Future<void> delete(String panelId) => _dio.delete('/panels/$panelId');

  @override
  Future<Panel> generateContent(String panelId) async =>
      _panel(await _dio.post('/panels/$panelId/generate', data: {'use_local': false}));

  @override
  Future<Panel> generateImage(String panelId) async =>
      _panel(await _dio.post('/panels/$panelId/image', data: {}));

  @override
  Future<Panel> generateBubbles(String panelId) async =>
      _panel(await _dio.post('/panels/$panelId/bubbles/generate', data: {}));
}

final panelsRepositoryProvider =
    Provider<PanelsRepository>((ref) => ApiPanelsRepository(ref.read(apiClientProvider)));
