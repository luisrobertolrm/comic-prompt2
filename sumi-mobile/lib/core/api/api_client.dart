import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../auth/auth_provider.dart';
import '../services/notification_service.dart';
import '../storage/secure_storage.dart';

const String kApiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://10.0.2.2:8000',
);

const silent = {'silent': true};

String fileUrl(String? pathOrUrl) {
  if (pathOrUrl == null || pathOrUrl.isEmpty) return '';
  if (pathOrUrl.startsWith('http')) return pathOrUrl;
  return '$kApiBaseUrl${pathOrUrl.startsWith('/') ? '' : '/'}$pathOrUrl';
}

/// A API FastAPI responde JSON direto (sem envelope) e erros como `{detail}`.
final apiClientProvider = Provider<Dio>((ref) {
  final notifier = ref.read(notificationServiceProvider);
  final storage = ref.read(secureStorageProvider);

  final dio = Dio(BaseOptions(
    baseUrl: kApiBaseUrl,
    connectTimeout: const Duration(seconds: 10),
    receiveTimeout: const Duration(minutes: 10),
  ));

  dio.interceptors.add(InterceptorsWrapper(
    onRequest: (options, handler) async {
      final token = await storage.accessToken;
      if (token != null) options.headers['Authorization'] = 'Bearer $token';
      handler.next(options);
    },
    onError: (err, handler) {
      final status = err.response?.statusCode;
      final isAuthRoute = err.requestOptions.path.startsWith('/auth/');
      if (status == 401 && !isAuthRoute) {
        // Lido só aqui (nunca no build) para não criar ciclo entre providers.
        ref.read(authProvider.notifier).logout(expired: true);
        handler.next(err);
        return;
      }
      if (err.requestOptions.extra['silent'] == true) {
        handler.next(err);
        return;
      }
      final messages = errorMessages(err);
      for (final m in messages) {
        notifier.error(m);
      }
      handler.next(err);
    },
  ));

  return dio;
});

List<String> errorMessages(DioException err) {
  if (err.type == DioExceptionType.connectionError ||
      err.type == DioExceptionType.connectionTimeout ||
      err.type == DioExceptionType.receiveTimeout ||
      err.type == DioExceptionType.sendTimeout) {
    return ['Sem conexão com o servidor.'];
  }
  var data = err.response?.data;
  if (data is List<int>) {
    try {
      data = jsonDecode(utf8.decode(data));
    } catch (_) {
      data = null;
    }
  }
  if (data is Map) {
    final detail = data['detail'];
    if (detail is String && detail.isNotEmpty) return [detail];
    if (detail is List) {
      return detail
          .whereType<Map>()
          .map((e) => e['msg']?.toString() ?? '')
          .where((m) => m.isNotEmpty)
          .toList();
    }
  }
  if (err.response != null) return ['Erro inesperado (${err.response!.statusCode}).'];
  return ['Erro inesperado.'];
}

/// Mensagem amigável para exibir inline nas telas.
String friendlyError(Object error) {
  if (error is DioException) {
    final m = errorMessages(error);
    if (m.isNotEmpty) return m.first;
  }
  return 'Algo deu errado. Tente novamente.';
}
