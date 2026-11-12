import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/api_client.dart';
import 'app_user.dart';

class Session {
  final String accessToken;
  final AppUser user;
  const Session(this.accessToken, this.user);

  factory Session.fromJson(Map<String, dynamic> j) => Session(
        j['access_token'] as String,
        AppUser.fromJson((j['user'] as Map).cast<String, dynamic>()),
      );
}

abstract class AuthRepository {
  Future<Session> login(String email, String password);
  Future<Session> refresh();
}

class ApiAuthRepository implements AuthRepository {
  final Dio _dio;
  ApiAuthRepository(this._dio);

  @override
  Future<Session> login(String email, String password) async {
    final resp = await _dio.post('/auth/login',
        data: {'email': email, 'password': password, 'remember': true});
    return Session.fromJson((resp.data as Map).cast<String, dynamic>());
  }

  @override
  Future<Session> refresh() async {
    final resp = await _dio.post('/auth/refresh', options: Options(extra: silent));
    return Session.fromJson((resp.data as Map).cast<String, dynamic>());
  }
}

final authRepositoryProvider =
    Provider<AuthRepository>((ref) => ApiAuthRepository(ref.read(apiClientProvider)));
