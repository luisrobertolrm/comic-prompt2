import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import 'voice.dart';

abstract class VoicesRepository {
  Future<List<Voice>> list();
  Future<Voice> create(VoiceInput input);
  Future<Voice> update(String id, VoiceInput input);
  Future<void> delete(String id);
  Future<Uint8List> synthesize(String text, String voiceId);
}

class ApiVoicesRepository implements VoicesRepository {
  final Dio _dio;
  ApiVoicesRepository(this._dio);

  Voice _voice(Response resp) => Voice.fromJson((resp.data as Map).cast<String, dynamic>());

  @override
  Future<List<Voice>> list() async {
    final resp = await _dio.get('/voice');
    return (resp.data as List)
        .map((e) => Voice.fromJson((e as Map).cast<String, dynamic>()))
        .toList();
  }

  @override
  Future<Voice> create(VoiceInput input) async =>
      _voice(await _dio.post('/voice', data: input.toJson()));

  @override
  Future<Voice> update(String id, VoiceInput input) async =>
      _voice(await _dio.patch('/voice/$id', data: input.toJson()));

  @override
  Future<void> delete(String id) => _dio.delete('/voice/$id');

  @override
  Future<Uint8List> synthesize(String text, String voiceId) async {
    final resp = await _dio.post<List<int>>('/voice/test',
        data: {'text': text, 'voice_id': voiceId},
        options: Options(responseType: ResponseType.bytes));
    return Uint8List.fromList(resp.data!);
  }
}

final voicesRepositoryProvider =
    Provider<VoicesRepository>((ref) => ApiVoicesRepository(ref.read(apiClientProvider)));

final savedVoicesProvider =
    FutureProvider.autoDispose<List<Voice>>((ref) => ref.read(voicesRepositoryProvider).list());
