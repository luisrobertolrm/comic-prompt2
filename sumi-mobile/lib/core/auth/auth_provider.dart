import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../services/notification_service.dart';
import '../storage/secure_storage.dart';
import 'app_user.dart';
import 'auth_repository.dart';

class AuthState {
  final bool loading;
  final AppUser? user;
  const AuthState({this.loading = false, this.user});

  bool get isAuthenticated => user != null;
}

final authProvider = NotifierProvider<AuthNotifier, AuthState>(AuthNotifier.new);

class AuthNotifier extends Notifier<AuthState> {
  SecureStorage get _storage => ref.read(secureStorageProvider);
  AuthRepository get _repository => ref.read(authRepositoryProvider);

  @override
  AuthState build() {
    _bootstrap();
    return const AuthState(loading: true);
  }

  Future<void> _bootstrap() async {
    final token = await _storage.accessToken;
    final userJson = await _storage.userJson;
    if (token == null || userJson == null) {
      state = const AuthState();
      return;
    }
    if (_isExpired(token)) {
      await logout(expired: true);
      return;
    }
    state = AuthState(user: AppUser.fromJson(jsonDecode(userJson) as Map<String, dynamic>));
    await _renew();
  }

  Future<void> _renew() async {
    try {
      await _save(await _repository.refresh());
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) await logout(expired: true);
    }
  }

  Future<void> login(String email, String password) async {
    await _save(await _repository.login(email.trim(), password));
  }

  Future<void> logout({bool expired = false}) async {
    await _storage.clear();
    state = const AuthState();
    if (expired) {
      ref.read(notificationServiceProvider).info('Sua sessão expirou. Entre novamente.');
    }
  }

  Future<void> _save(Session session) async {
    await _storage.saveSession(
      accessToken: session.accessToken,
      userJson: jsonEncode(session.user.toJson()),
    );
    state = AuthState(user: session.user);
  }

  bool _isExpired(String jwt) {
    try {
      final payload = jsonDecode(
          utf8.decode(base64Url.decode(base64Url.normalize(jwt.split('.')[1]))));
      final exp = payload['exp'] as int;
      return DateTime.now().isAfter(DateTime.fromMillisecondsSinceEpoch(exp * 1000));
    } catch (_) {
      return true;
    }
  }
}
