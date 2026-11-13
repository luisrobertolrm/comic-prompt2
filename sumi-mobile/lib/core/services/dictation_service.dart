import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';

import '../api/api_client.dart';

/// Grava a fala do usuário e devolve o texto transcrito.
abstract class DictationService {
  /// Retorna false quando o usuário nega a permissão do microfone.
  Future<bool> start();

  /// Para a gravação e devolve a transcrição ('' se nada foi gravado).
  Future<String> stopAndTranscribe();

  Future<void> cancel();
}

/// Envia o áudio ao servidor (`POST /speech/transcribe`), que usa a
/// configuração de transcrição ativa; a chave do fornecedor nunca sai do servidor.
class ApiDictationService implements DictationService {
  ApiDictationService(this._dio);

  final Dio _dio;
  final _recorder = AudioRecorder();

  @override
  Future<bool> start() async {
    if (!await _recorder.hasPermission()) return false;
    final dir = await getTemporaryDirectory();
    await _recorder.start(
      const RecordConfig(encoder: AudioEncoder.aacLc, numChannels: 1),
      path: '${dir.path}/sumi_dictation.m4a',
    );
    return true;
  }

  @override
  Future<String> stopAndTranscribe() async {
    final path = await _recorder.stop();
    if (path == null) return '';
    final file = File(path);
    try {
      final form = FormData.fromMap({
        'file': await MultipartFile.fromFile(path, filename: 'ditado.m4a'),
      });
      final resp = await _dio.post<Map<String, dynamic>>('/speech/transcribe', data: form);
      return (resp.data?['text'] as String? ?? '').trim();
    } finally {
      if (await file.exists()) await file.delete();
    }
  }

  @override
  Future<void> cancel() => _recorder.cancel();

  void dispose() => _recorder.dispose();
}

final dictationServiceProvider = Provider<DictationService>((ref) {
  final service = ApiDictationService(ref.read(apiClientProvider));
  ref.onDispose(service.dispose);
  return service;
});
