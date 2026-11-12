import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

final secureStorageProvider = Provider<SecureStorage>((ref) => SecureStorage());

/// Guarda apenas dados de sessão (token, usuário, projeto em produção).
/// Classe concreta por decisão registrada no plan.md (Complexity Tracking).
class SecureStorage {
  static const _kAccess = 'access_token';
  static const _kUser = 'user';
  static const _kDraft = 'draft_project_id';

  final _storage = const FlutterSecureStorage();
  final Map<String, String?> _cache = {};
  bool _loaded = false;

  Future<void> _bootstrap() async {
    if (_loaded) return;
    for (final key in [_kAccess, _kUser, _kDraft]) {
      _cache[key] = await _storage.read(key: key);
    }
    _loaded = true;
  }

  Future<String?> get accessToken async {
    await _bootstrap();
    return _cache[_kAccess];
  }

  Future<String?> get userJson async {
    await _bootstrap();
    return _cache[_kUser];
  }

  Future<String?> get draftProjectId async {
    await _bootstrap();
    return _cache[_kDraft];
  }

  Future<void> saveSession({required String accessToken, required String userJson}) async {
    _cache[_kAccess] = accessToken;
    _cache[_kUser] = userJson;
    await _storage.write(key: _kAccess, value: accessToken);
    await _storage.write(key: _kUser, value: userJson);
  }

  Future<void> saveDraftProjectId(String? projectId) async {
    _cache[_kDraft] = projectId;
    if (projectId == null) {
      await _storage.delete(key: _kDraft);
    } else {
      await _storage.write(key: _kDraft, value: projectId);
    }
  }

  Future<void> clear() async {
    _cache.clear();
    _loaded = true;
    await _storage.deleteAll();
  }
}
