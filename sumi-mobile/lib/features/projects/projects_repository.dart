import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../production/jobs.dart';
import 'project.dart';

class YoutubeMetadata {
  final String title;
  final String description;
  final List<String> tags;
  final String categoryId;
  final String privacyStatus;
  final String? publishAt;
  final String? thumbnailPanelId;

  const YoutubeMetadata({
    this.title = '',
    this.description = '',
    this.tags = const [],
    this.categoryId = '24',
    this.privacyStatus = 'private',
    this.publishAt,
    this.thumbnailPanelId,
  });

  factory YoutubeMetadata.fromJson(Map<String, dynamic> j) => YoutubeMetadata(
        title: j['yt_title'] as String? ?? '',
        description: j['yt_description'] as String? ?? '',
        tags: (j['yt_tags'] as List? ?? const []).map((e) => e.toString()).toList(),
        categoryId: j['yt_category_id']?.toString() ?? '24',
        privacyStatus: j['privacy_status'] as String? ?? 'private',
        publishAt: j['publish_at'] as String?,
        thumbnailPanelId: j['thumbnail_panel_id'] as String?,
      );

  Map<String, dynamic> toJson() => {
        'yt_title': title,
        'yt_description': description,
        'yt_tags': tags,
        'yt_category_id': categoryId,
        'privacy_status': privacyStatus,
        'publish_at': publishAt,
        'thumbnail_panel_id': thumbnailPanelId,
      };
}

abstract class ProjectsRepository {
  Future<List<Project>> list();
  Future<Project> get(String id);
  Future<Project> create(Map<String, dynamic> body);
  Future<Project> update(String id, Map<String, dynamic> patch);
  Future<void> delete(String id);
  Future<Project> generateSynopsis(String id);
  Future<void> setCharacters(String id, List<String> characterIds);
  Future<void> setScenarios(String id, List<String> scenarioIds);
  Future<Uint8List> exportPanelsZip(String id);
  Future<Job> startVideo(String id);
  Future<Job> videoJob(String id, String jobId);
  Future<Uint8List> downloadVideo(String videoUrl);
  Future<YoutubeMetadata> getYoutubeMetadata(String id);
  Future<YoutubeMetadata> saveYoutubeMetadata(String id, YoutubeMetadata meta);
  Future<YoutubeMetadata> generateYoutubeMetadata(String id);
}

class ApiProjectsRepository implements ProjectsRepository {
  final Dio _dio;
  ApiProjectsRepository(this._dio);

  Project _project(Response resp) => Project.fromJson((resp.data as Map).cast<String, dynamic>());

  @override
  Future<List<Project>> list() async {
    final resp = await _dio.get('/projects');
    return (resp.data as List)
        .map((e) => Project.fromJson((e as Map).cast<String, dynamic>()))
        .toList();
  }

  @override
  Future<Project> get(String id) async => _project(await _dio.get('/projects/$id'));

  @override
  Future<Project> create(Map<String, dynamic> body) async =>
      _project(await _dio.post('/projects', data: body));

  @override
  Future<Project> update(String id, Map<String, dynamic> patch) async =>
      _project(await _dio.patch('/projects/$id', data: patch));

  @override
  Future<void> delete(String id) => _dio.delete('/projects/$id');

  @override
  Future<Project> generateSynopsis(String id) async =>
      _project(await _dio.post('/projects/$id/synopsis/generate', data: {}));

  @override
  Future<void> setCharacters(String id, List<String> characterIds) =>
      _dio.put('/projects/$id/characters', data: {'character_ids': characterIds});

  @override
  Future<void> setScenarios(String id, List<String> scenarioIds) =>
      _dio.put('/projects/$id/scenarios', data: {'scenario_ids': scenarioIds});

  @override
  Future<Uint8List> exportPanelsZip(String id) async {
    final resp = await _dio.get<List<int>>('/projects/$id/export/panels',
        options: Options(responseType: ResponseType.bytes));
    return Uint8List.fromList(resp.data!);
  }

  @override
  Future<Job> startVideo(String id) async {
    final resp = await _dio.post('/projects/$id/export/video', data: {});
    return Job.fromJson((resp.data as Map).cast<String, dynamic>());
  }

  @override
  Future<Job> videoJob(String id, String jobId) async {
    final resp =
        await _dio.get('/projects/$id/export/video/$jobId', options: Options(extra: silent));
    return Job.fromJson((resp.data as Map).cast<String, dynamic>());
  }

  @override
  Future<Uint8List> downloadVideo(String videoUrl) async {
    final resp = await _dio.get<List<int>>(fileUrl(videoUrl),
        options: Options(responseType: ResponseType.bytes));
    return Uint8List.fromList(resp.data!);
  }

  YoutubeMetadata _meta(Response resp) =>
      YoutubeMetadata.fromJson((resp.data as Map).cast<String, dynamic>());

  @override
  Future<YoutubeMetadata> getYoutubeMetadata(String id) async =>
      _meta(await _dio.get('/projects/$id/youtube-metadata'));

  @override
  Future<YoutubeMetadata> saveYoutubeMetadata(String id, YoutubeMetadata meta) async =>
      _meta(await _dio.put('/projects/$id/youtube-metadata', data: meta.toJson()));

  @override
  Future<YoutubeMetadata> generateYoutubeMetadata(String id) async =>
      _meta(await _dio.post('/projects/$id/youtube-metadata/generate', data: {}));
}

final projectsRepositoryProvider = Provider<ProjectsRepository>(
    (ref) => ApiProjectsRepository(ref.read(apiClientProvider)));
