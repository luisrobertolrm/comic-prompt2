import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/api_client.dart';

/// Pontua, corrige e divide o texto em parágrafos, sem acrescentar conteúdo.
abstract class TextOrganizerService {
  Future<String> organize(String text);
}

class ApiTextOrganizerService implements TextOrganizerService {
  ApiTextOrganizerService(this._dio);

  final Dio _dio;

  @override
  Future<String> organize(String text) async {
    final resp = await _dio.post<Map<String, dynamic>>('/text/organize', data: {'text': text});
    return (resp.data?['text'] as String? ?? '').trim();
  }
}

final textOrganizerServiceProvider = Provider<TextOrganizerService>(
    (ref) => ApiTextOrganizerService(ref.read(apiClientProvider)));
